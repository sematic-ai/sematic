# Standard Library
import logging
import os
import pathlib
import time
from dataclasses import asdict, dataclass
from typing import Dict, List, Optional

# Third-party
import matplotlib.figure
import matplotlib.pyplot as plt
import numpy as np
import PIL.Image
import torch
from torch.optim import lr_scheduler
from tqdm import tqdm

# Sematic
import sematic

# Yolov5
from sematic.examples.yolov5.configs.dataset import DatasetConfig
from sematic.examples.yolov5.configs.evaluation import EvaluationConfig
from sematic.examples.yolov5.configs.hyperparameters import HyperParameters
from sematic.examples.yolov5.configs.model import ModelConfig
from sematic.examples.yolov5.models.yolo import DetectionModel
from sematic.examples.yolov5.utils.autoanchor import check_anchors
from sematic.examples.yolov5.utils.dataloaders import create_dataloader
from sematic.examples.yolov5.utils.general import (
    TQDM_BAR_FORMAT,
    Profile,
    check_amp,
    check_img_size,
    coco80_to_coco91_class,
    download,
    init_seeds,
    labels_to_class_weights,
    non_max_suppression,
    scale_boxes,
    xywh2xyxy,
)
from sematic.examples.yolov5.utils.loss import ComputeLoss
from sematic.examples.yolov5.utils.metrics import ConfusionMatrix, ap_per_class
from sematic.examples.yolov5.utils.plots import output_to_target, plot_images
from sematic.examples.yolov5.utils.torch_utils import (
    EarlyStopping,
    ModelEMA,
    de_parallel,
    select_device,
    smart_optimizer,
)
from sematic.examples.yolov5.val import process_batch

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
    seed: int = 0


@dataclass
class PipelineConfig:
    # weights: str
    model_config: ModelConfig
    dataset_config: DatasetConfig
    hyperparameters: HyperParameters
    training_config: TrainingConfig
    evaluation_config: EvaluationConfig
    device: str


@dataclass
class CocoDataset:
    train_path: str
    val_path: str
    classes: Dict[int, str]
    image_size: int


@sematic.func(cache=True)
def get_dataset(dataset_config: DatasetConfig) -> CocoDataset:
    """
    Download COCO dataset to local filesystem.
    """
    download(dataset_config.location, dataset_config.path)

    return CocoDataset(
        train_path=os.path.join(dataset_config.path, dataset_config.train),
        val_path=os.path.join(dataset_config.path, dataset_config.val),
        classes=dataset_config.names,
        image_size=dataset_config.image_size,
    )


@sematic.func(cache=True)
def train_model(
    device: str,
    train_config: TrainingConfig,
    input_dataset: CocoDataset,
    model_config: ModelConfig,
    hyperparameters: HyperParameters,
) -> DetectionModel:
    """
    Train YOLO model.
    """
    device = select_device(device, train_config.batch_size)
    init_seeds(train_config.seed + 1, deterministic=True)

    model = DetectionModel(
        asdict(model_config),
        ch=3,
        nc=len(input_dataset.classes),
        anchors=hyperparameters.anchors,
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
        input_dataset.image_size, gs, floor=gs * 2
    )  # verify imgsz is gs-multiple

    # Optimizer
    nbs = 64  # nominal batch size
    accumulate = max(
        round(nbs / train_config.batch_size), 1
    )  # accumulate loss before optimizing
    hyperparameters.weight_decay *= (
        train_config.batch_size * accumulate / nbs
    )  # scale weight_decay
    optimizer = smart_optimizer(
        model,
        train_config.optimizer,
        hyperparameters.lr0,
        hyperparameters.momentum,
        hyperparameters.weight_decay,
    )

    # Scheduler
    lf = (
        lambda x: (1 - x / train_config.epochs) * (1.0 - hyperparameters.lrf)
        + hyperparameters.lrf
    )  # linear
    scheduler = lr_scheduler.LambdaLR(optimizer, lr_lambda=lf)

    # EMA
    ema = ModelEMA(model)

    # Trainloader
    best_fitness, start_epoch = 0.0, 0
    single_cls = False
    train_loader, dataset = create_dataloader(
        input_dataset.train_path,
        imgsz,
        train_config.batch_size,
        gs,
        single_cls,
        hyp=asdict(hyperparameters),
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

    check_anchors(
        dataset, model=model, thr=hyperparameters.anchor_t, imgsz=imgsz
    )  # run AutoAnchor
    model.half().float()  # pre-reduce anchor precision

    # Model attributes
    nl = de_parallel(model).model[-1].nl  # number of detection layers (to scale hyps)
    hyperparameters.box *= 3 / nl  # scale to layers
    hyperparameters.cls *= model_config.nc / 80 * 3 / nl  # scale to classes and layers
    hyperparameters.obj *= (imgsz / 640) ** 2 * 3 / nl  # scale to image size and layers
    model.nc = model_config.nc  # attach number of classes to model
    model.hyp = asdict(hyperparameters)  # attach hyperparameters to model
    model.class_weights = (
        labels_to_class_weights(dataset.labels, model_config.nc).to(device)
        * model_config.nc
    )  # attach class weights
    model.names = input_dataset.classes

    # Start training
    t0 = time.time()
    nb = len(train_loader)  # number of batches
    nw = max(
        round(hyperparameters.warmup_epochs * nb), 100
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
                            hyperparameters.warmup_bias_lr if j == 0 else 0.0,
                            x["initial_lr"] * lf(epoch),
                        ],
                    )
                    if "momentum" in x:
                        x["momentum"] = np.interp(
                            ni,
                            xi,
                            [
                                hyperparameters.warmup_momentum,
                                hyperparameters.momentum,
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
        scheduler.step()

    torch.cuda.empty_cache()
    for p in model.parameters():
        p.requires_grad = False

    return model.half()


@dataclass
class EvaluationMetrics:
    mean_precision: float
    mean_recall: float
    mean_ap50: float
    mean_ap: float
    average_loss: List[float]


@dataclass
class EvaluationResults:
    images: PIL.Image.Image
    confusion_matrix: Optional[matplotlib.figure.Figure]
    precision_recall: Optional[matplotlib.figure.Figure]
    f1_score: Optional[matplotlib.figure.Figure]
    precision: Optional[matplotlib.figure.Figure]
    recall: Optional[matplotlib.figure.Figure]
    metrics: EvaluationMetrics


@sematic.func
def evaluate_model(
    model: DetectionModel,
    dataset: CocoDataset,
    config: EvaluationConfig,
    train_config: TrainingConfig,
    hyperparameters: HyperParameters,
) -> EvaluationResults:
    # strip_optimizer_model(model)  # strip optimizers
    device, pt, jit, engine = (
        next(model.parameters()).device,
        True,
        False,
        False,
    )  # get model device, PyTorch model
    cuda = device.type != "cpu"
    half = config.half and cuda  # half precision only supported on CUDA
    for p in model.parameters():
        p.requires_grad = False
    model.half() if half else model.float()

    model.eval()
    nc = len(dataset.classes)  # number of classes
    iouv = torch.linspace(0.5, 0.95, 10, device=device)  # iou vector for mAP@0.5:0.95
    niou = iouv.numel()

    gs = max(int(model.stride.max()), 32)  # grid size (max stride)
    imgsz = check_img_size(
        dataset.image_size, gs, floor=gs * 2
    )  # verify imgsz is gs-multiple

    dataloader = create_dataloader(
        dataset.val_path,
        imgsz,
        train_config.batch_size * 2,
        gs,
        False,
        hyp=asdict(hyperparameters),
        rect=train_config.rectangular_training,
        rank=-1,
        pad=0.5,
        # workers=8,
    )[0]

    seen = 0
    confusion_matrix = ConfusionMatrix(nc=nc)
    names = (
        model.names if hasattr(model, "names") else model.module.names
    )  # get class names
    if isinstance(names, (list, tuple)):  # old format
        names = dict(enumerate(names))
    # class_map = coco80_to_coco91_class()
    s = ("%22s" + "%11s" * 6) % (
        "Class",
        "Images",
        "Instances",
        "P",
        "R",
        "mAP50",
        "mAP50-95",
    )
    tp, fp, p, r, f1, mp, mr, map50, ap50, map = (
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
        0.0,
    )
    # dt = Profile(), Profile(), Profile()  # profiling times
    loss = torch.zeros(3, device=device)
    jdict, stats, ap, ap_class = [], [], [], []
    pbar = tqdm(dataloader, desc=s, bar_format=TQDM_BAR_FORMAT)  # progress bar

    compute_loss = ComputeLoss(model)  # init loss class

    images = []

    for batch_i, (im, targets, paths, shapes) in enumerate(pbar):
        # with dt[0]:
        if cuda:
            im = im.to(device, non_blocking=True)
            targets = targets.to(device)
        im = im.half() if half else im.float()  # uint8 to fp16/32
        im /= 255  # 0 - 255 to 0.0 - 1.0
        nb, _, height, width = im.shape  # batch size, channels, height, width

        # Inference
        # with dt[1]:
        preds, train_out = (
            model(im) if compute_loss else (model(im, augment=config.augment), None)
        )

        # Loss
        loss += compute_loss(train_out, targets)[1]  # box, obj, cls

        # NMS
        targets[:, 2:] *= torch.tensor(
            (width, height, width, height), device=device
        )  # to pixels
        lb = (
            [targets[targets[:, 0] == i, 1:] for i in range(nb)] if False else []
        )  # for autolabelling
        # with dt[2]:

        preds = non_max_suppression(
            preds,
            0,  # config.conf_thres,
            config.iou_thres,
            labels=lb,
            multi_label=True,
            agnostic=False,
            max_det=config.max_det,
        )

        # Metrics
        for si, pred in enumerate(preds):
            labels = targets[targets[:, 0] == si, 1:]
            nl, npr = labels.shape[0], pred.shape[0]  # number of labels, predictions
            path, shape = pathlib.Path(paths[si]), shapes[si][0]
            correct = torch.zeros(npr, niou, dtype=torch.bool, device=device)  # init
            seen += 1

            if npr == 0:
                if nl:
                    stats.append(
                        (correct, *torch.zeros((2, 0), device=device), labels[:, 0])
                    )
                    confusion_matrix.process_batch(detections=None, labels=labels[:, 0])
                continue

            # Predictions
            if config.single_cls:
                pred[:, 5] = 0
            predn = pred.clone()
            scale_boxes(
                im[si].shape[1:], predn[:, :4], shape, shapes[si][1]
            )  # native-space pred

            # Evaluate
            if nl:
                tbox = xywh2xyxy(labels[:, 1:5])  # target boxes
                scale_boxes(
                    im[si].shape[1:], tbox, shape, shapes[si][1]
                )  # native-space labels
                labelsn = torch.cat((labels[:, 0:1], tbox), 1)  # native-space labels
                correct = process_batch(predn, labelsn, iouv)
                confusion_matrix.process_batch(predn, labelsn)
            stats.append(
                (correct, pred[:, 4], pred[:, 5], labels[:, 0])
            )  # (correct, conf, pcls, tcls)

        # Plot images
        if batch_i < 3:
            images += [
                plot_images(im, targets, paths, f"val_batch{batch_i}_labels.jpg", names)
            ]  # labels
            images += [
                plot_images(
                    im,
                    output_to_target(preds),
                    paths,
                    f"val_batch{batch_i}_pred.jpg",
                    names,
                )
            ]  # pred

    # Compute metrics
    stats = [torch.cat(x, 0).cpu().numpy() for x in zip(*stats)]  # to numpy

    plots = {}
    if len(stats) and stats[0].any():
        tp, fp, p, r, f1, ap, ap_class, plots = ap_per_class(
            *stats, plot=True, save_dir="", names=names
        )
        ap50, ap = ap[:, 0], ap.mean(1)  # AP@0.5, AP@0.5:0.95
        mp, mr, map50, map = p.mean(), r.mean(), ap50.mean(), ap.mean()
    nt = np.bincount(stats[3].astype(int), minlength=nc)  # number of targets per class

    # Print results
    pf = "%22s" + "%11i" * 2 + "%11.3g" * 4  # print format
    logger.info(pf % ("all", seen, nt.sum(), mp, mr, map50, map))

    if nt.sum() == 0:
        logger.warning(
            "WARNING ⚠️ no labels found in set, can not compute metrics without labels"
        )

    # Print speeds
    # t = tuple(x.t / seen * 1e3 for x in dt)  # speeds per image

    # Plots
    confusion_matrix_plot = confusion_matrix.plot(
        save_dir="", names=list(names.values())
    )

    # Return results
    model.float()  # for training

    maps = np.zeros(nc) + map
    for i, c in enumerate(ap_class):
        maps[c] = ap[i]
    # return (mp, mr, map50, map, *(loss.cpu() / len(dataloader)).tolist()), maps, t

    metrics = EvaluationMetrics(
        mean_precision=mp,
        mean_recall=mr,
        mean_ap50=map50,
        mean_ap=map,
        average_loss=(loss.cpu() / len(dataloader)).tolist(),
    )

    return EvaluationResults(
        images=images[0],
        confusion_matrix=confusion_matrix_plot,
        precision_recall=plots.get("PR"),
        f1_score=plots.get("F1"),
        precision=plots.get("P"),
        recall=plots.get("R"),
        metrics=metrics,
    )


@sematic.func
def pipeline(
    config: PipelineConfig, model: Optional[DetectionModel] = None
) -> EvaluationResults:
    dataset = get_dataset(config.dataset_config)
    if model is None:
        model = train_model(
            device=config.device,
            train_config=config.training_config,
            input_dataset=dataset,
            model_config=config.model_config,
            hyperparameters=config.hyperparameters,
        )

    return evaluate_model(
        model=model,
        dataset=dataset,
        config=config.evaluation_config,
        train_config=config.training_config,
        hyperparameters=config.hyperparameters,
    )


@sematic.func
def make_matplotlib_plot() -> matplotlib.figure.Figure:
    # make data
    x = np.linspace(0, 10, 100)
    y = 4 + 2 * np.sin(2 * x)

    # plot
    fig, ax = plt.subplots()

    ax.plot(x, y, linewidth=2.0)

    ax.set(xlim=(0, 8), xticks=np.arange(1, 8), ylim=(0, 8), yticks=np.arange(1, 8))

    return fig
