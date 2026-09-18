"""
Training entry point.

Usage:
    python -m src.train --data-dir data/ --arch resnet50 --epochs 20

Model selection is on macro-F1, not accuracy. With nv at ~67% of the dataset,
accuracy rewards a model for ignoring the six minority classes, and the
checkpoint you keep would be the one that learned least.
"""

import argparse
import csv
import json
import time
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from sklearn.metrics import f1_score
from torch.utils.data import DataLoader

from .data import (
    CLASSES,
    HAM10000Dataset,
    build_transforms,
    class_weights,
    describe,
    load_metadata,
    split_by_lesion,
)
from .models import ARCHITECTURES, build_model, trainable_parameters


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--data-dir", default="data")
    p.add_argument("--out-dir", default="runs")
    p.add_argument("--arch", default="resnet50", choices=sorted(ARCHITECTURES))
    p.add_argument("--epochs", type=int, default=20)
    p.add_argument("--batch-size", type=int, default=32)
    p.add_argument("--lr", type=float, default=3e-4)
    p.add_argument("--weight-decay", type=float, default=1e-4)
    p.add_argument("--freeze-backbone", action="store_true")
    p.add_argument("--patience", type=int, default=5,
                   help="Stop after this many epochs without macro-F1 improvement")
    p.add_argument("--num-workers", type=int, default=2)
    p.add_argument("--seed", type=int, default=42)
    return p.parse_args()


def run_epoch(model, loader, criterion, device, optimizer=None, is_inception=False):
    """One pass over a loader. Trains if an optimizer is supplied."""
    training = optimizer is not None
    model.train() if training else model.eval()

    total_loss = 0.0
    all_preds, all_targets = [], []

    with torch.set_grad_enabled(training):
        for images, targets in loader:
            images = images.to(device, non_blocking=True)
            targets = targets.to(device, non_blocking=True)

            if training:
                optimizer.zero_grad(set_to_none=True)

            if training and is_inception:
                # Inception returns (main, aux) in train mode. The 0.4 weight on
                # the auxiliary loss is the value from the original paper.
                outputs, aux = model(images)
                loss = criterion(outputs, targets) + 0.4 * criterion(aux, targets)
            else:
                outputs = model(images)
                loss = criterion(outputs, targets)

            if training:
                loss.backward()
                optimizer.step()

            total_loss += loss.item() * images.size(0)
            all_preds.append(outputs.argmax(1).detach().cpu())
            all_targets.append(targets.detach().cpu())

    preds = torch.cat(all_preds).numpy()
    targets = torch.cat(all_targets).numpy()

    return {
        "loss": total_loss / len(targets),
        "accuracy": float((preds == targets).mean()),
        "macro_f1": float(f1_score(targets, preds, average="macro", zero_division=0)),
    }


def main():
    args = parse_args()
    torch.manual_seed(args.seed)
    np.random.seed(args.seed)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Device: {device}")
    if device.type == "cpu":
        print("Warning: training on CPU will take many hours. Use a GPU runtime.")

    out_dir = Path(args.out_dir) / args.arch
    out_dir.mkdir(parents=True, exist_ok=True)

    df = load_metadata(args.data_dir)
    train_df, val_df, test_df = split_by_lesion(df, seed=args.seed)
    for split_df, name in [(train_df, "train"), (val_df, "val"), (test_df, "test")]:
        describe(split_df, name)

    split_path = out_dir / "split.json"
    split_path.write_text(json.dumps({
        "seed": args.seed,
        "train": train_df["image_id"].tolist(),
        "val": val_df["image_id"].tolist(),
        "test": test_df["image_id"].tolist(),
    }))

    image_size = ARCHITECTURES[args.arch]
    train_ds = HAM10000Dataset(train_df, build_transforms(image_size, train=True))
    val_ds = HAM10000Dataset(val_df, build_transforms(image_size, train=False))

    train_loader = DataLoader(
        train_ds, batch_size=args.batch_size, shuffle=True,
        num_workers=args.num_workers, pin_memory=(device.type == "cuda"),
        drop_last=True,
    )
    val_loader = DataLoader(
        val_ds, batch_size=args.batch_size, shuffle=False,
        num_workers=args.num_workers, pin_memory=(device.type == "cuda"),
    )

    model = build_model(
        args.arch, len(CLASSES), freeze_backbone=args.freeze_backbone
    ).to(device)
    print(f"\n{args.arch}: {trainable_parameters(model):,} trainable parameters")

    criterion = nn.CrossEntropyLoss(weight=class_weights(train_df, device))
    optimizer = torch.optim.AdamW(
        [p for p in model.parameters() if p.requires_grad],
        lr=args.lr, weight_decay=args.weight_decay,
    )
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=args.epochs)

    log_path = out_dir / "history.csv"
    with open(log_path, "w", newline="") as f:
        csv.writer(f).writerow([
            "epoch", "train_loss", "train_acc", "train_macro_f1",
            "val_loss", "val_acc", "val_macro_f1", "lr", "seconds",
        ])

    best_f1 = -1.0
    best_epoch = -1
    is_inception = args.arch == "inception_v3"

    for epoch in range(1, args.epochs + 1):
        start = time.time()
        tr = run_epoch(model, train_loader, criterion, device, optimizer, is_inception)
        va = run_epoch(model, val_loader, criterion, device)
        scheduler.step()
        elapsed = time.time() - start

        print(
            f"epoch {epoch:>3}/{args.epochs}  "
            f"train loss {tr['loss']:.4f} F1 {tr['macro_f1']:.4f}  |  "
            f"val loss {va['loss']:.4f} acc {va['accuracy']:.4f} "
            f"F1 {va['macro_f1']:.4f}  ({elapsed:.0f}s)"
        )

        with open(log_path, "a", newline="") as f:
            csv.writer(f).writerow([
                epoch, tr["loss"], tr["accuracy"], tr["macro_f1"],
                va["loss"], va["accuracy"], va["macro_f1"],
                optimizer.param_groups[0]["lr"], round(elapsed, 1),
            ])

        if va["macro_f1"] > best_f1:
            best_f1 = va["macro_f1"]
            best_epoch = epoch
            torch.save({
                "arch": args.arch,
                "epoch": epoch,
                "state_dict": model.state_dict(),
                "val_macro_f1": best_f1,
                "classes": CLASSES,
            }, out_dir / "best.pt")
            print("  saved (best val macro-F1 so far)")

        elif epoch - best_epoch >= args.patience:
            print(f"\nNo improvement in {args.patience} epochs. Stopping.")
            break

    print(f"\nBest val macro-F1 {best_f1:.4f} at epoch {best_epoch}")
    print(f"Checkpoint: {out_dir / 'best.pt'}")
    print(f"Next: python -m src.evaluate --data-dir {args.data_dir} "
          f"--checkpoint {out_dir / 'best.pt'}")


if __name__ == "__main__":
    main()
