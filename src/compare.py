"""
Collect results.json from every completed run and print a comparison table.

Usage:
    python -m src.compare --runs-dir runs

Produces a markdown table you can paste straight into the README, so the
reported numbers come from the files the evaluation wrote rather than from
anything retyped by hand.
"""

import argparse
import json
from pathlib import Path


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--runs-dir", default="runs")
    p.add_argument("--out", default=None, help="Optional path to write the table")
    return p.parse_args()


def main():
    args = parse_args()
    runs_dir = Path(args.runs_dir)

    rows = []
    for results_path in sorted(runs_dir.glob("*/results.json")):
        rows.append(json.loads(results_path.read_text()))

    if not rows:
        print(f"No results.json found under {runs_dir}. Run src.evaluate first.")
        return

    rows.sort(key=lambda r: r["macro_f1"], reverse=True)

    lines = [
        "| Architecture | Accuracy | Macro F1 | Macro AUC | "
        "Melanoma recall | BCC recall |",
        "|---|---|---|---|---|---|",
    ]

    for r in rows:
        lines.append(
            f"| {r['architecture']} "
            f"| {r['accuracy']:.4f} "
            f"| {r['macro_f1']:.4f} "
            f"| {r['macro_auc']:.4f} "
            f"| {r['per_class_recall']['mel']:.4f} "
            f"| {r['per_class_recall']['bcc']:.4f} |"
        )

    baseline = rows[0]["majority_baseline_accuracy"]
    lines.append("")
    lines.append(
        f"Majority-class baseline accuracy: {baseline:.4f}. "
        f"Evaluated on {rows[0]['test_images']} images from "
        f"{rows[0]['test_lesions']} held-out lesions."
    )

    table = "\n".join(lines)
    print(table)

    if args.out:
        Path(args.out).write_text(table + "\n")
        print(f"\nWritten to {args.out}")


if __name__ == "__main__":
    main()
