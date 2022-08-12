# Standard Library
from typing import List

import pandas
import plotly.express as px
import torch
import torch.nn as nn
import torch.nn.functional as F
from plotly.graph_objs import Figure, Heatmap
from sklearn.metrics import confusion_matrix
from torch.optim.optimizer import Optimizer
from torch.utils.data import DataLoader
from torchmetrics import PrecisionRecallCurve  # type: ignore


class Net(nn.Module):
    def __init__(self):
        super(Net, self).__init__()
        self.conv1 = nn.Conv2d(1, 32, 3, 1)
        self.conv2 = nn.Conv2d(32, 64, 3, 1)
        self.dropout1 = nn.Dropout(0.25)
        self.dropout2 = nn.Dropout(0.5)
        self.fc1 = nn.Linear(9216, 128)
        self.fc2 = nn.Linear(128, 10)

    def forward(self, x):
        x = self.conv1(x)
        x = F.relu(x)
        x = self.conv2(x)
        x = F.relu(x)
        x = F.max_pool2d(x, 2)
        x = self.dropout1(x)
        x = torch.flatten(x, 1)
        x = self.fc1(x)
        x = F.relu(x)
        x = self.dropout2(x)
        x = self.fc2(x)
        output = F.log_softmax(x, dim=1)
        return output


def train(
    model: nn.Module,
    device: torch.device,
    train_loader: DataLoader,
    optimizer: Optimizer,
    epoch: int,
    log_interval: int,
    dry_run: bool,
):
    model.train()
    for batch_idx, (data, target) in enumerate(train_loader):
        data, target = data.to(device), target.to(device)
        optimizer.zero_grad()
        output = model(data)
        loss = F.nll_loss(output, target)
        loss.backward()
        optimizer.step()
        if batch_idx % log_interval == 0:
            print(
                "Train Epoch: {} [{}/{} ({:.0f}%)]\tLoss: {:.6f}".format(
                    epoch,
                    batch_idx * len(data),
                    len(train_loader.dataset),  # type: ignore
                    100.0 * batch_idx / len(train_loader),
                    loss.item(),
                )
            )
            if dry_run:
                break


def _confusion_matrix(targets: List[int], preds: List[int]):
    matrix = confusion_matrix(y_true=targets, y_pred=preds)
    data = Heatmap(
        z=matrix,
        text=matrix,
        texttemplate="%{text}",
        x=list(range(10)),
        y=list(range(10)),
    )
    layout = {
        "title": "Confusion Matrix",
        "xaxis": {"title": "Predicted value"},
        "yaxis": {"title": "Real value"},
    }
    return Figure(data=data, layout=layout)


def test(model: nn.Module, device: torch.device, test_loader: DataLoader):
    model.eval()
    test_loss: float = 0
    correct = 0
    probas = []
    preds = []
    targets = []
    with torch.no_grad():
        for data, target in test_loader:
            data, target = data.to(device), target.to(device)
            output = model(data)
            probas.append(output)
            targets.append(target)
            test_loss += F.nll_loss(
                output, target, reduction="sum"
            ).item()  # sum up batch loss
            pred = output.argmax(dim=1)  # get the index of the max log-probability
            preds.append(pred)
            correct += pred.eq(target).sum().item()

    test_loss /= len(test_loader.dataset)  # type: ignore
    pr_curve = PrecisionRecallCurve(num_classes=10)
    precision, recall, thresholds = pr_curve(torch.cat(probas), torch.cat(targets))
    classes = []
    for i in range(10):
        classes += [i] * len(precision[i])

    df = pandas.DataFrame(
        {
            "precision": list(torch.cat(precision).cpu()),
            "recall": list(torch.cat(recall).cpu()),
            "class": classes,
        }
    )

    fig = px.scatter(
        df,
        x="recall",
        y="precision",
        color="class",
        labels={"x": "Recall", "y": "Precision"},
    )

    return dict(
        average_loss=test_loss,
        accuracy=correct / len(test_loader.dataset),  # type: ignore
        pr_curve=fig,
        confusion_matrix=_confusion_matrix(
            torch.cat(targets).cpu(), torch.cat(preds).cpu()
        ),
    )
