# Standard Library
import logging
import time
from dataclasses import asdict, dataclass
from types import ModuleType
from typing import Any, List, Literal, Tuple, Union

# Third-party
import numpy as np
import torch
from torch.optim import lr_scheduler
from tqdm import tqdm

# Sematic
import sematic

# Yolov5
from sematic.examples.yolov5.configs.dataset import DatasetConfig
from sematic.examples.yolov5.configs.hyperparameters import HyperParametersConfig
from sematic.examples.yolov5.configs.model import ModelConfig
from sematic.examples.yolov5.models.yolo import DetectionModel
from sematic.examples.yolov5.utils.autoanchor import check_anchors
from sematic.examples.yolov5.utils.dataloaders import create_dataloader
from sematic.examples.yolov5.utils.general import (
    TQDM_BAR_FORMAT,
    check_amp,
    check_img_size,
    download,
    init_seeds,
    labels_to_class_weights,
)
from sematic.examples.yolov5.utils.loss import ComputeLoss
from sematic.examples.yolov5.utils.torch_utils import (
    EarlyStopping,
    ModelEMA,
    de_parallel,
    select_device,
    smart_optimizer,
)

logger = logging.getLogger(__name__)
RANK = -1
WORLD_SIZE = 1


@dataclass
class TrainingConfig:
    rectangular_training: bool = False
    auto_anchor: bool = True
    optimizer: str = "SGD"
    epochs: int = 1
    batch_size: int = 16
    image_size: int = 640
    seed: int = 0


@dataclass
class PipelineConfig:
    # weights: str
    model_config: ModelConfig
    dataset_config: DatasetConfig
    hyperparameters: HyperParametersConfig
    training_config: TrainingConfig
    device: str


@sematic.func
def train_model(
    device: str,
    train_config: TrainingConfig,
    dataset_config: DatasetConfig,
    model_config: ModelConfig,
    hyperparameters_config: HyperParametersConfig,
) -> DetectionModel:
    device = select_device(device, train_config.batch_size)
    cuda = device.type != "cpu"
    init_seeds(train_config.seed + 1, deterministic=True)
    download(dataset_config.location)
    train_path, val_path = dataset_config.train, dataset_config.val
    model = DetectionModel(
        asdict(model_config),
        ch=3,
        nc=len(dataset_config.names),
        anchors=hyperparameters_config.anchors,
    ).to(device)
    amp = check_amp(model)

    # Freeze
    freeze = model_config.freeze
    freeze = [
        f"model.{x}." for x in (freeze if len(freeze) > 1 else range(freeze[0]))
    ]  # layers to freeze
    for k, v in model.named_parameters():
        v.requires_grad = True  # train all layers
        # v.register_hook(lambda x: torch.nan_to_num(x))  # NaN to 0 (commented for erratic training results)
        if any(x in k for x in freeze):
            v.requires_grad = False

    # Image size
    gs = max(int(model.stride.max()), 32)  # grid size (max stride)
    imgsz = check_img_size(
        train_config.image_size, gs, floor=gs * 2
    )  # verify imgsz is gs-multiple

    # Optimizer
    nbs = 64  # nominal batch size
    accumulate = max(
        round(nbs / train_config.batch_size), 1
    )  # accumulate loss before optimizing
    hyperparameters_config.weight_decay *= (
        train_config.batch_size * accumulate / nbs
    )  # scale weight_decay
    optimizer = smart_optimizer(
        model,
        train_config.optimizer,
        hyperparameters_config.lr0,
        hyperparameters_config.momentum,
        hyperparameters_config.weight_decay,
    )

    # Scheduler
    lf = (
        lambda x: (1 - x / train_config.epochs) * (1.0 - hyperparameters_config.lrf)
        + hyperparameters_config.lrf
    )  # linear
    scheduler = lr_scheduler.LambdaLR(optimizer, lr_lambda=lf)

    # EMA
    ema = ModelEMA(model)

    # Trainloader
    best_fitness, start_epoch = 0.0, 0
    single_cls = False
    train_loader, dataset = create_dataloader(
        train_path,
        imgsz,
        train_config.batch_size,
        gs,
        single_cls,
        hyp=asdict(hyperparameters_config),
        augment=True,
        cache=None,
        rect=train_config.rectangular_training,
        rank=-1,
        workers=8,
        image_weights=None,
        quad=None,
        shuffle=True,
        seed=train_config.seed,
    )
    labels = np.concatenate(dataset.labels, 0)
    mlc = int(labels[:, 0].max())  # max label class
    assert (
        mlc < model_config.nc
    ), f"Label class {mlc} exceeds nc={model_config.nc}. Possible class labels are 0-{model_config.nc - 1}"

    val_loader = create_dataloader(
        val_path,
        imgsz,
        train_config.batch_size * 2,
        gs,
        single_cls,
        hyp=asdict(hyperparameters_config),
        rect=True,
        rank=-1,
        pad=0.5,
    )[0]

    check_anchors(
        dataset, model=model, thr=hyperparameters_config.anchor_t, imgsz=imgsz
    )  # run AutoAnchor
    model.half().float()  # pre-reduce anchor precision

    # Model attributes
    nl = de_parallel(model).model[-1].nl  # number of detection layers (to scale hyps)
    hyperparameters_config.box *= 3 / nl  # scale to layers
    hyperparameters_config.cls *= (
        model_config.nc / 80 * 3 / nl
    )  # scale to classes and layers
    hyperparameters_config.obj *= (
        (imgsz / 640) ** 2 * 3 / nl
    )  # scale to image size and layers
    model.nc = model_config.nc  # attach number of classes to model
    model.hyp = asdict(hyperparameters_config)  # attach hyperparameters to model
    model.class_weights = (
        labels_to_class_weights(dataset.labels, model_config.nc).to(device)
        * model_config.nc
    )  # attach class weights
    model.names = dataset_config.names

    # Start training
    t0 = time.time()
    nb = len(train_loader)  # number of batches
    nw = max(
        round(hyperparameters_config.warmup_epochs * nb), 100
    )  # number of warmup iterations, max(3 epochs, 100 iterations)
    # nw = min(nw, (epochs - start_epoch) / 2 * nb)  # limit warmup to < 1/2 of training
    last_opt_step = -1
    maps = np.zeros(model_config.nc)  # mAP per class
    results = (0, 0, 0, 0, 0, 0, 0)  # P, R, mAP@.5, mAP@.5-.95, val_loss(box, obj, cls)
    scheduler.last_epoch = start_epoch - 1  # do not move
    scaler = torch.cuda.amp.GradScaler(enabled=amp)
    stopper, stop = EarlyStopping(patience=100), False
    compute_loss = ComputeLoss(model)  # init loss class

    logger.info(
        f"Image sizes {imgsz} train, {imgsz} val\n"
        f"Using {train_loader.num_workers} dataloader workers\n"
        f"Starting training for {train_config.epochs} epochs..."
    )

    for epoch in range(start_epoch, train_config.epochs):
        model.train()

        mloss = torch.zeros(3, device=device)  # mean losses
        if RANK != -1:
            train_loader.sampler.set_epoch(epoch)
        pbar = enumerate(train_loader)
        logger.info(
            ("\n" + "%11s" * 7)
            % (
                "Epoch",
                "GPU_mem",
                "box_loss",
                "obj_loss",
                "cls_loss",
                "Instances",
                "Size",
            )
        )
        if RANK in {-1, 0}:
            pbar = tqdm(pbar, total=nb, bar_format=TQDM_BAR_FORMAT)  # progress bar
        optimizer.zero_grad()
        for i, (
            imgs,
            targets,
            paths,
            _,
        ) in (
            pbar
        ):  # batch -------------------------------------------------------------
            ni = i + nb * epoch  # number integrated batches (since train start)
            imgs = (
                imgs.to(device, non_blocking=True).float() / 255
            )  # uint8 to float32, 0-255 to 0.0-1.0

            # Warmup
            if ni <= nw:
                xi = [0, nw]  # x interp
                # compute_loss.gr = np.interp(ni, xi, [0.0, 1.0])  # iou loss ratio (obj_loss = 1.0 or iou)
                accumulate = max(
                    1, np.interp(ni, xi, [1, nbs / train_config.batch_size]).round()
                )
                for j, x in enumerate(optimizer.param_groups):
                    # bias lr falls from 0.1 to lr0, all other lrs rise from 0.0 to lr0
                    x["lr"] = np.interp(
                        ni,
                        xi,
                        [
                            hyperparameters_config.warmup_bias_lr if j == 0 else 0.0,
                            x["initial_lr"] * lf(epoch),
                        ],
                    )
                    if "momentum" in x:
                        x["momentum"] = np.interp(
                            ni,
                            xi,
                            [
                                hyperparameters_config.warmup_momentum,
                                hyperparameters_config.momentum,
                            ],
                        )

            # Forward
            with torch.cuda.amp.autocast(amp):
                pred = model(imgs)  # forward
                loss, loss_items = compute_loss(
                    pred, targets.to(device)
                )  # loss scaled by batch_size
                if RANK != -1:
                    loss *= WORLD_SIZE  # gradient averaged between devices in DDP mode

            # Backward
            scaler.scale(loss).backward()

            # Optimize - https://pytorch.org/docs/master/notes/amp_examples.html
            if ni - last_opt_step >= accumulate:
                scaler.unscale_(optimizer)  # unscale gradients
                torch.nn.utils.clip_grad_norm_(
                    model.parameters(), max_norm=10.0
                )  # clip gradients
                scaler.step(optimizer)  # optimizer.step
                scaler.update()
                optimizer.zero_grad()
                if ema:
                    ema.update(model)
                last_opt_step = ni

            # Log
            if RANK in {-1, 0}:
                mloss = (mloss * i + loss_items) / (i + 1)  # update mean losses
                mem = f"{torch.cuda.memory_reserved() / 1E9 if torch.cuda.is_available() else 0:.3g}G"  # (GB)
                pbar.set_description(
                    ("%11s" * 2 + "%11.4g" * 5)
                    % (
                        f"{epoch}/{train_config.epochs - 1}",
                        mem,
                        *mloss,
                        targets.shape[0],
                        imgs.shape[-1],
                    )
                )
            # end batch ------------------------------------------------------------------------------------------------

        # Scheduler
        lr = [x["lr"] for x in optimizer.param_groups]  # for loggers
        scheduler.step()

    torch.cuda.empty_cache()
    return model


@sematic.func
def pipeline(config: PipelineConfig) -> DetectionModel:
    return train_model(
        device=config.device,
        train_config=config.training_config,
        dataset_config=config.dataset_config,
        model_config=config.model_config,
        hyperparameters_config=config.hyperparameters,
    )
