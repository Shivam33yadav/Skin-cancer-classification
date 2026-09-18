"""
Evaluate a trained checkpoint on the held-out test split.

Usage:
    python -m src.evaluate --data-dir data/ --checkpoint runs/resnet50/best.pt

Writes results.json and confusion_matrix.png next to the checkpoint, and prints
a per-class breakdown. The headline number to report is macro-F1; overall
accuracy is included but should not be quoted on its own, because predicting nv
for every image already scores about 0.67.
"""

import argparse
import json
from pathlib import Path

import numpy as np
import torch
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    f1_score,
    roc_auc_score,
)
from torch.utils.data import DataLoader

from .data import (
    CLASSES,
    CLASS_NAMES,
    MALIGNANT,
    HAM10000Dataset,
    build_transforms,
    load_metadata,
    split_by_lesion,
)
from .models import ARCHITECTURES, build_model


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--data-dir", default="data")
    p.add_argument("--checkpoint", required=True)
    p.add_argument("--batch-size", type=int, default=32)
    p.add_argument("--num-workers", type=int, default=2)
    p.add_argument("--seed", type=int, default=42)
    return p.parse_args()


@torch.no_grad()
def predict(model, loader, device):
    model.eval()
    probs, targets = [], []
    for images, y in loader:
        logits = model(images.to(device))
        probs.append(torch.softmax(logits, dim=1).cpu())
        targets.append(y)
    return torch.cat(probs).numpy(), torch.cat(targets).numpy()


def plot_confusion(cm, path):
    """Row-normalised confusion matrix. Rows are true classes, so the diagonal
    reads as per-class recall."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib not installed; skipping confusion matrix plot")
        return

    normalised = cm.astype(float) / np.maximum(cm.sum(axis=1, keepdims=True), 1)

    fig, ax = plt.subplots(figsize=(7, 6))
    im = ax.imshow(normalised, cmap="Blues", vmin=0, vmax=1)
    ax.set_xticks(range(len(CLASSES)), CLASSES, rotation=45, ha="right")
    ax.set_yticks(range(len(CLASSES)), CLASSES)
    ax.set_xlabel("Predicted")
    ax.set_ylabel("True")
    ax.set_title("Confusion matrix (row-normalised)")

    for i in range(len(CLASSES)):
        for j in range(len(CLASSES)):
            ax.text(
                j, i, f"{normalised[i, j]:.2f}",
                ha="center", va="center",
                color="white" if normalised[i, j] > 0.5 else "black",
                fontsize=8,
            )

    fig.colorbar(im, ax=ax, fraction=0.046)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    print(f"Confusion matrix: {path}")


def main():
    args = parse_args()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    ckpt_path = Path(args.checkpoint)
    ckpt = torch.load(ckpt_path, map_location=device, weights_only=False)
    arch = ckpt["arch"]
    print(f"Loaded {arch} from epoch {ckpt['epoch']} "
          f"(val macro-F1 {ckpt['val_macro_f1']:.4f})")

    model = build_model(arch, len(CLASSES)).to(device)
    model.load_state_dict(ckpt["state_dict"])

    df = load_metadata(args.data_dir)
    _, _, test_df = split_by_lesion(df, seed=args.seed)

    split_path = ckpt_path.parent / "split.json"
    if split_path.exists():
        saved = set(json.loads(split_path.read_text())["test"])
        test_df = df[df["image_id"].isin(saved)].reset_index(drop=True)
        print(f"Using saved split: {len(test_df)} test images")

    image_size = ARCHITECTURES[arch]
    loader = DataLoader(
        HAM10000Dataset(test_df, build_transforms(image_size, train=False)),
        batch_size=args.batch_size, shuffle=False, num_workers=args.num_workers,
    )

    probs, targets = predict(model, loader, device)
    preds = probs.argmax(1)

    accuracy = float((preds == targets).mean())
    macro_f1 = float(f1_score(targets, preds, average="macro", zero_division=0))
    weighted_f1 = float(f1_score(targets, preds, average="weighted", zero_division=0))

    present = sorted(set(targets))
    try:
        auc = float(roc_auc_score(
            targets, probs, multi_class="ovr", average="macro", labels=present
        ))
    except ValueError:
        auc = float("nan")

    cm = confusion_matrix(targets, preds, labels=range(len(CLASSES)))
    recalls = cm.diagonal() / np.maximum(cm.sum(axis=1), 1)

    majority = int(np.bincount(targets, minlength=len(CLASSES)).argmax())
    majority_acc = float((targets == majority).mean())

    print(f"\nTest set: {len(targets)} images, "
          f"{test_df['lesion_id'].nunique()} distinct lesions\n")
    print(classification_report(
        targets, preds, labels=range(len(CLASSES)),
        target_names=CLASSES, digits=4, zero_division=0,
    ))

    print(f"Accuracy      {accuracy:.4f}")
    print(f"Macro F1      {macro_f1:.4f}")
    print(f"Weighted F1   {weighted_f1:.4f}")
    print(f"Macro AUC     {auc:.4f}")
    print(f"\nMajority-class baseline accuracy: {majority_acc:.4f} "
          f"(always predict '{CLASSES[majority]}')")

    print("\nRecall on malignant / pre-malignant classes:")
    for i, c in enumerate(CLASSES):
        if c in MALIGNANT:
            print(f"  {c:<6} {recalls[i]:.4f}   {CLASS_NAMES[c]}")

    results = {
        "architecture": arch,
        "checkpoint_epoch": ckpt["epoch"],
        "test_images": int(len(targets)),
        "test_lesions": int(test_df["lesion_id"].nunique()),
        "accuracy": accuracy,
        "macro_f1": macro_f1,
        "weighted_f1": weighted_f1,
        "macro_auc": auc,
        "majority_baseline_accuracy": majority_acc,
        "per_class_recall": {c: float(recalls[i]) for i, c in enumerate(CLASSES)},
        "confusion_matrix": cm.tolist(),
        "class_order": CLASSES,
    }

    results_path = ckpt_path.parent / "results.json"
    results_path.write_text(json.dumps(results, indent=2))
    print(f"\nResults: {results_path}")

    plot_confusion(cm, ckpt_path.parent / "confusion_matrix.png")


if __name__ == "__main__":
    main()
