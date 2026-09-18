"""
Transfer-learning model factory.

Each architecture is loaded with ImageNet weights and has its classifier head
replaced with a fresh linear layer sized to the seven HAM10000 classes. The
backbones differ in where that head lives, which is the only reason this file
needs to exist at all.
"""

import torch.nn as nn
from torchvision import models

# Architectures compared in this project, with the input size each expects.
ARCHITECTURES = {
    "resnet50": 224,
    "densenet121": 224,
    "efficientnet_b0": 224,
    "mobilenet_v3_large": 224,
    "vgg16": 224,
    "inception_v3": 299,
}


def build_model(name, num_classes=7, freeze_backbone=False, dropout=0.0):
    """Return a torchvision model with a new classification head.

    freeze_backbone=True trains only the head. That is much faster and a
    reasonable first pass, but on HAM10000 full fine-tuning consistently does
    better -- dermoscopic texture is far enough from ImageNet's distribution
    that the frozen features leave accuracy on the table.
    """
    if name not in ARCHITECTURES:
        raise ValueError(
            f"Unknown architecture '{name}'. Available: {sorted(ARCHITECTURES)}"
        )

    if name == "resnet50":
        model = models.resnet50(weights=models.ResNet50_Weights.IMAGENET1K_V2)
        in_features = model.fc.in_features
        model.fc = _head(in_features, num_classes, dropout)

    elif name == "densenet121":
        model = models.densenet121(weights=models.DenseNet121_Weights.IMAGENET1K_V1)
        in_features = model.classifier.in_features
        model.classifier = _head(in_features, num_classes, dropout)

    elif name == "efficientnet_b0":
        model = models.efficientnet_b0(
            weights=models.EfficientNet_B0_Weights.IMAGENET1K_V1
        )
        in_features = model.classifier[1].in_features
        model.classifier = _head(in_features, num_classes, dropout or 0.2)

    elif name == "mobilenet_v3_large":
        model = models.mobilenet_v3_large(
            weights=models.MobileNet_V3_Large_Weights.IMAGENET1K_V2
        )
        in_features = model.classifier[3].in_features
        model.classifier[3] = _head(in_features, num_classes, dropout)

    elif name == "vgg16":
        model = models.vgg16(weights=models.VGG16_Weights.IMAGENET1K_V1)
        in_features = model.classifier[6].in_features
        model.classifier[6] = _head(in_features, num_classes, dropout)

    elif name == "inception_v3":
        model = models.inception_v3(
            weights=models.Inception_V3_Weights.IMAGENET1K_V1
        )
        # Inception has a second loss branch used during training. Retarget it
        # too, otherwise it still predicts 1000 ImageNet classes.
        model.AuxLogits.fc = nn.Linear(model.AuxLogits.fc.in_features, num_classes)
        in_features = model.fc.in_features
        model.fc = _head(in_features, num_classes, dropout)

    if freeze_backbone:
        head_names = ("fc", "classifier", "AuxLogits")
        for param_name, param in model.named_parameters():
            param.requires_grad = param_name.startswith(head_names)

    return model


def _head(in_features, num_classes, dropout):
    if dropout:
        return nn.Sequential(nn.Dropout(dropout), nn.Linear(in_features, num_classes))
    return nn.Linear(in_features, num_classes)


def trainable_parameters(model):
    return sum(p.numel() for p in model.parameters() if p.requires_grad)
