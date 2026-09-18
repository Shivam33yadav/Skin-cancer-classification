# Skin Lesion Classification — HAM10000

Multi-class classification of dermatoscopic images into seven diagnostic
categories, comparing six ImageNet-pretrained CNN architectures under a shared
training and evaluation protocol.

## The dataset

HAM10000 contains 10,015 dermatoscopic images across seven classes:

| Code | Diagnosis | Share of dataset |
|---|---|---|
| nv | Melanocytic nevi | ~67% |
| mel | Melanoma | ~11% |
| bkl | Benign keratosis-like lesions | ~11% |
| bcc | Basal cell carcinoma | ~5% |
| akiec | Actinic keratoses / intraepithelial carcinoma | ~3% |
| vasc | Vascular lesions | ~1.4% |
| df | Dermatofibroma | ~1.1% |

Two properties of this dataset drive most of the design decisions here.

**Severe class imbalance.** A model that predicts nv for every image scores
roughly 67% accuracy while detecting no cancer at all. Accuracy is therefore
close to meaningless as a headline metric, and gradient descent will find that
degenerate solution quickly if the loss is left unweighted. Training uses
inverse-frequency class weights, model selection is on macro-F1, and the
majority-class baseline is reported alongside every result.

**Repeated images of the same lesion.** Many of the 10,015 images are additional
photographs of a lesion that already appears elsewhere in the dataset, linked by
lesion_id. Splitting randomly by image places near-duplicates of the same lesion
in both training and test sets, which inflates reported accuracy by several
points. Every split groups on lesion_id, and the split function asserts that no
lesion identifier crosses a boundary.

## Setup

Download the dataset from Kaggle (search: skin-cancer-mnist-ham10000) and
extract it so the layout looks like this:

    data/
        HAM10000_metadata.csv
        HAM10000_images_part_1/
        HAM10000_images_part_2/

Install dependencies:

    pip install -r requirements.txt

A GPU is effectively required. On a T4, one epoch of ResNet-50 over this dataset
takes a few minutes; on CPU it takes hours.

## Running it

Train one architecture:

    python -m src.train --data-dir data --arch resnet50 --epochs 20

Evaluate the checkpoint it saved:

    python -m src.evaluate --data-dir data --checkpoint runs/resnet50/best.pt

Sweep all six architectures, then build the comparison table:

    for arch in resnet50 densenet121 efficientnet_b0 mobilenet_v3_large vgg16 inception_v3; do
        python -m src.train --data-dir data --arch $arch --epochs 20
        python -m src.evaluate --data-dir data --checkpoint runs/$arch/best.pt
    done

    python -m src.compare --runs-dir runs

src/compare.py reads the saved results.json files and emits a markdown table, so
the reported numbers come from the evaluation output rather than being
transcribed by hand.

## Method

- **Transfer learning** from ImageNet weights, with the classifier head replaced
  and the full network fine-tuned. Freezing the backbone is supported via
  --freeze-backbone and trains far faster, but underperforms full fine-tuning
  here: dermoscopic texture sits far enough from ImageNet's distribution that
  frozen features leave accuracy unclaimed.
- **Split** 70 / 15 / 15 train / validation / test, grouped on lesion_id.
- **Augmentation** random resized crop, horizontal and vertical flips, rotation
  up to 30 degrees, mild colour jitter. Lesion photographs have no canonical
  orientation, so flips and rotation are safe; colour jitter is kept mild
  because dermoscopic hue carries diagnostic signal.
- **Loss** cross-entropy with inverse-frequency class weights normalised to
  mean 1.
- **Optimiser** AdamW, cosine-annealed learning rate.
- **Model selection** best validation macro-F1, with early stopping after five
  epochs without improvement.

## Results

ResNet-50, 20 epochs, best checkpoint selected on validation macro-F1 (epoch 18).
Evaluated on 1,527 held-out images from 1,121 lesions that appear nowhere in
training or validation.

| Architecture | Accuracy | Macro F1 | Macro AUC | Melanoma recall | BCC recall |
|---|---|---|---|---|---|
| resnet50 | 0.8062 | 0.6929 | 0.9643 | 0.6237 | 0.7879 |

Majority-class baseline accuracy: 0.6654 (always predict nv).

Per-class results:

| Class | Precision | Recall | F1 | Support |
|---|---|---|---|---|
| akiec | 0.5102 | 0.5208 | 0.5155 | 48 |
| bcc | 0.6753 | 0.7879 | 0.7273 | 66 |
| bkl | 0.6615 | 0.7384 | 0.6978 | 172 |
| df | 0.6364 | 0.7000 | 0.6667 | 10 |
| mel | 0.5273 | 0.6237 | 0.5714 | 186 |
| nv | 0.9312 | 0.8661 | 0.8975 | 1016 |
| vasc | 0.7273 | 0.8276 | 0.7742 | 29 |

Reading these honestly: accuracy of 0.8062 sits only 14 points above the trivial
baseline, so it is the least informative number here. Macro AUC of 0.9643 is the
stronger signal, indicating the model separates classes well across thresholds
rather than simply favouring the majority class.

Recall on melanoma is 0.6237, meaning roughly four in ten melanomas in the test
set were missed. Actinic keratoses are worse at 0.5208. These are the numbers
that matter for the task and they are well short of clinical usability. The df
row rests on 10 test images and should be read as noise rather than signal.

## Limitations

- HAM10000 is drawn from two centres in Austria and Australia and skews heavily
  toward lighter skin tones. Performance on darker skin is not measured by this
  test set and should not be assumed from these numbers.
- Test-set performance on a curated research dataset is not a clinical result.
  Images here are already cropped, centred, and captured under dermoscopy.
- No calibration analysis. The softmax outputs are not evaluated as
  probabilities, so the confidence scores should not be read as such.
- Single seed per architecture. Differences between the top few architectures
  are likely within run-to-run variance; distinguishing them properly would need
  repeated seeds and confidence intervals.


## Repository layout

    src/
        data.py       metadata loading, lesion-grouped splitting, augmentation
        models.py     model factory for the six architectures
        train.py      training loop, class weighting, early stopping
        evaluate.py   test-set metrics, per-class recall, confusion matrix
        compare.py    aggregates results.json across runs into a table
    site/
        earlier static reference page for this project

## Dataset citation

Tschandl, P., Rosendahl, C. & Kittler, H. The HAM10000 dataset, a large
collection of multi-source dermatoscopic images of common pigmented skin
lesions. Sci. Data 5, 180161 (2018).
