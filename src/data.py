"""
HAM10000 data loading.

The important detail in this dataset: many images are repeat photographs of the
same physical lesion. HAM10000_metadata.csv gives every image a `lesion_id`, and
roughly 5,500 of the 10,015 images share a lesion_id with at least one other
image.

If you split randomly by image, near-duplicate photographs of the same lesion end
up in both train and test, and reported accuracy is inflated by several points.
Every split here is done on lesion_id so that all images of a lesion land on the
same side of the split.
"""

from pathlib import Path

import numpy as np
import pandas as pd
import torch
from PIL import Image
from sklearn.model_selection import GroupShuffleSplit
from torch.utils.data import Dataset, WeightedRandomSampler
from torchvision import transforms

CLASSES = ["akiec", "bcc", "bkl", "df", "mel", "nv", "vasc"]

CLASS_NAMES = {
    "akiec": "Actinic keratoses / intraepithelial carcinoma",
    "bcc": "Basal cell carcinoma",
    "bkl": "Benign keratosis-like lesions",
    "df": "Dermatofibroma",
    "mel": "Melanoma",
    "nv": "Melanocytic nevi",
    "vasc": "Vascular lesions",
}

# Malignant or pre-malignant classes. Recall on these is what actually matters
# clinically -- a missed melanoma is not the same kind of error as a missed nevus.
MALIGNANT = {"mel", "bcc", "akiec"}

IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]


def load_metadata(data_dir):
    """Read HAM10000_metadata.csv and attach a resolved path for each image."""
    data_dir = Path(data_dir)
    meta_path = data_dir / "HAM10000_metadata.csv"
    if not meta_path.exists():
        raise FileNotFoundError(
            f"Could not find {meta_path}. See the README for download steps."
        )

    df = pd.read_csv(meta_path)

    index = {}
    for jpg in data_dir.rglob("*.jpg"):
        index[jpg.stem] = jpg

    df["path"] = df["image_id"].map(index)

    missing = df["path"].isna().sum()
    if missing:
        raise FileNotFoundError(
            f"{missing} of {len(df)} images listed in the metadata were not found "
            f"under {data_dir}. Check that both image folders were extracted."
        )

    df["label"] = df["dx"].map({c: i for i, c in enumerate(CLASSES)})
    if df["label"].isna().any():
        unexpected = sorted(set(df.loc[df["label"].isna(), "dx"]))
        raise ValueError(f"Unexpected diagnosis codes in metadata: {unexpected}")
    df["label"] = df["label"].astype(int)

    return df


def split_by_lesion(df, val_size=0.15, test_size=0.15, seed=42):
    """Split into train/val/test, grouping on lesion_id."""
    gss = GroupShuffleSplit(n_splits=1, test_size=test_size, random_state=seed)
    trainval_idx, test_idx = next(gss.split(df, groups=df["lesion_id"]))
    trainval = df.iloc[trainval_idx].reset_index(drop=True)
    test = df.iloc[test_idx].reset_index(drop=True)

    adjusted = val_size / (1.0 - test_size)
    gss = GroupShuffleSplit(n_splits=1, test_size=adjusted, random_state=seed)
    train_idx, val_idx = next(gss.split(trainval, groups=trainval["lesion_id"]))
    train = trainval.iloc[train_idx].reset_index(drop=True)
    val = trainval.iloc[val_idx].reset_index(drop=True)

    for a, b, name in [
        (train, val, "train/val"),
        (train, test, "train/test"),
        (val, test, "val/test"),
    ]:
        overlap = set(a["lesion_id"]) & set(b["lesion_id"])
        assert not overlap, f"lesion_id leak across {name}: {len(overlap)} shared"

    return train, val, test


def build_transforms(image_size=224, train=False):
    """Augmentation for training, plain resize for evaluation."""
    if train:
        return transforms.Compose([
            transforms.Resize((image_size + 32, image_size + 32)),
            transforms.RandomResizedCrop(image_size, scale=(0.7, 1.0)),
            transforms.RandomHorizontalFlip(),
            transforms.RandomVerticalFlip(),
            transforms.RandomRotation(30),
            transforms.ColorJitter(brightness=0.15, contrast=0.15, saturation=0.10),
            transforms.ToTensor(),
            transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
        ])

    return transforms.Compose([
        transforms.Resize((image_size, image_size)),
        transforms.ToTensor(),
        transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
    ])


class HAM10000Dataset(Dataset):
    def __init__(self, df, transform=None):
        self.paths = df["path"].tolist()
        self.labels = df["label"].tolist()
        self.transform = transform

    def __len__(self):
        return len(self.paths)

    def __getitem__(self, i):
        image = Image.open(self.paths[i]).convert("RGB")
        if self.transform:
            image = self.transform(image)
        return image, self.labels[i]


def class_weights(df, device=None):
    """Inverse-frequency weights, normalised to mean 1."""
    counts = np.bincount(df["label"], minlength=len(CLASSES)).astype(np.float64)
    counts[counts == 0] = 1.0
    weights = counts.sum() / (len(CLASSES) * counts)
    weights = weights / weights.mean()
    t = torch.tensor(weights, dtype=torch.float32)
    return t.to(device) if device else t


def balanced_sampler(df):
    """Alternative to weighted loss: oversample rare classes during training."""
    counts = np.bincount(df["label"], minlength=len(CLASSES)).astype(np.float64)
    counts[counts == 0] = 1.0
    per_sample = (1.0 / counts)[df["label"].to_numpy()]
    return WeightedRandomSampler(
        weights=torch.tensor(per_sample, dtype=torch.double),
        num_samples=len(df),
        replacement=True,
    )


def describe(df, name):
    """Print class distribution for a split."""
    counts = df["dx"].value_counts()
    total = len(df)
    print(f"\n{name}: {total} images, {df['lesion_id'].nunique()} lesions")
    for c in CLASSES:
        n = int(counts.get(c, 0))
        print(f"  {c:<6} {n:>5}  ({100 * n / total:5.2f}%)  {CLASS_NAMES[c]}")
