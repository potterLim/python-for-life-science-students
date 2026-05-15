"""
프로젝트 5. YOLO로 현미경 이미지 속 세포핵 탐지하기 참고용 완성 코드.

프로젝트 문서의 단계별 코드를 하나로 모은 파일입니다.
먼저 문서를 따라 직접 입력해 보고, 실행이 막히거나 전체 구조를 확인하고 싶을 때 참고하세요.

이 파일은 예측 결과가 눈에 보일 정도로 학습되도록 조금 더 긴 학습 설정을 사용합니다.
안정적으로 실행되도록 기본 장치는 CPU로 두었습니다. GPU나 Apple Silicon MPS를 사용하고 싶다면
문서의 파라미터 설명을 참고해 DEVICE 값을 바꿔 보세요.
"""

# 1단계. 필요한 기능 불러오기
from pathlib import Path
from urllib.request import urlretrieve
from zipfile import ZipFile

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from PIL import Image
from skimage import exposure, io, measure

# 2단계. 폴더와 기본 파라미터 준비하기
PROJECT_DIR = Path(__file__).resolve().parents[1] / "05_yolo_nuclei_detection"
DATA_DIR = PROJECT_DIR / "data" / "raw"
YOLO_DATASET_DIR = PROJECT_DIR / "data" / "yolo_dataset"
OUTPUT_DIR = PROJECT_DIR / "outputs"

IMAGE_DIR = DATA_DIR / "images"
MASK_DIR = DATA_DIR / "masks"
METADATA_DIR = DATA_DIR / "metadata"

YOLO_IMAGES_TRAIN_DIR = YOLO_DATASET_DIR / "images" / "train"
YOLO_IMAGES_VAL_DIR = YOLO_DATASET_DIR / "images" / "val"
YOLO_LABELS_TRAIN_DIR = YOLO_DATASET_DIR / "labels" / "train"
YOLO_LABELS_VAL_DIR = YOLO_DATASET_DIR / "labels" / "val"

for directory in [
    DATA_DIR,
    YOLO_IMAGES_TRAIN_DIR,
    YOLO_IMAGES_VAL_DIR,
    YOLO_LABELS_TRAIN_DIR,
    YOLO_LABELS_VAL_DIR,
    OUTPUT_DIR,
]:
    directory.mkdir(parents=True, exist_ok=True)

TRAIN_IMAGE_COUNT = 40
VAL_IMAGE_COUNT = 10

MODEL_NAME = "yolo26n.pt"
EPOCHS = 50
IMAGE_SIZE = 640
BATCH_SIZE = 4
DEVICE = "cpu"
WORKERS = 0
CONFIDENCE = 0.25

print("YOLO 데이터셋 폴더:", YOLO_DATASET_DIR)
print("출력 폴더:", OUTPUT_DIR)

# 3단계. 데이터 다운로드하기
DOWNLOADS = {
    "images.zip": "https://data.broadinstitute.org/bbbc/BBBC039/images.zip",
    "masks.zip": "https://data.broadinstitute.org/bbbc/BBBC039/masks.zip",
    "metadata.zip": "https://data.broadinstitute.org/bbbc/BBBC039/metadata.zip",
}

for filename, url in DOWNLOADS.items():
    output_path = DATA_DIR / filename

    if output_path.exists():
        print("이미 파일이 있습니다:", output_path.name)
    else:
        print("다운로드합니다:", output_path.name)
        urlretrieve(url, output_path)
        print("다운로드 완료:", output_path.name)

# 4단계. 압축 풀기
def extract_zip(zip_path, output_dir):
    with ZipFile(zip_path) as zip_file:
        for file_info in zip_file.infolist():
            if file_info.is_dir():
                continue

            if file_info.filename.startswith("__MACOSX/"):
                continue

            output_path = output_dir / file_info.filename

            if output_path.exists():
                continue

            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_bytes(zip_file.read(file_info.filename))


extract_zip(DATA_DIR / "images.zip", DATA_DIR)
extract_zip(DATA_DIR / "masks.zip", DATA_DIR)
extract_zip(DATA_DIR / "metadata.zip", DATA_DIR)

print("이미지 폴더:", IMAGE_DIR)
print("mask 폴더:", MASK_DIR)
print("metadata 폴더:", METADATA_DIR)

image_files = sorted(IMAGE_DIR.glob("*.tif"))
mask_files = sorted(MASK_DIR.glob("*.png"))
metadata_files = sorted(METADATA_DIR.iterdir())

print("이미지 파일 수:", len(image_files))
print("mask 파일 수:", len(mask_files))
print("metadata 파일:", [path.name for path in metadata_files])
print("첫 번째 이미지 파일:", image_files[0].name)
print("첫 번째 mask 파일:", mask_files[0].name)

# 5단계. train/validation 이미지 목록 만들기
def read_name_list(path):
    return [
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


training_mask_names = read_name_list(METADATA_DIR / "training.txt")
validation_mask_names = read_name_list(METADATA_DIR / "validation.txt")

train_mask_names = training_mask_names[:TRAIN_IMAGE_COUNT]
val_mask_names = validation_mask_names[:VAL_IMAGE_COUNT]

print("train mask 수:", len(train_mask_names))
print("val mask 수:", len(val_mask_names))
print("첫 번째 train mask:", train_mask_names[0])
print("첫 번째 val mask:", val_mask_names[0])

# 6단계. mask를 label image로 바꾸는 함수 만들기
def decode_instance_mask(mask_image):
    rgb_mask = mask_image[..., :3]

    color_code = (
        rgb_mask[..., 0].astype(np.int32)
        + rgb_mask[..., 1].astype(np.int32) * 256
        + rgb_mask[..., 2].astype(np.int32) * 256 * 256
    )

    labels = np.zeros(color_code.shape, dtype=np.int32)
    next_label = 1

    for color_value in np.unique(color_code):
        if color_value == 0:
            continue

        same_color = color_code == color_value
        connected_parts = measure.label(same_color)

        for part_label in range(1, connected_parts.max() + 1):
            labels[connected_parts == part_label] = next_label
            next_label += 1

    return labels

# 7단계. TIFF 이미지를 PNG로 변환하는 함수 만들기
def save_png_for_yolo(tif_path, png_path):
    image = io.imread(tif_path)

    image_8bit = exposure.rescale_intensity(
        image.astype(float),
        in_range="image",
        out_range=(0, 255),
    ).astype(np.uint8)

    image_rgb = np.dstack([image_8bit, image_8bit, image_8bit])
    Image.fromarray(image_rgb).save(png_path)

    return image.shape

# 8단계. bounding box를 YOLO label 형식으로 바꾸기
def labels_to_yolo_rows(labels, image_height, image_width, min_area_pixels=20):
    yolo_rows = []

    for region in measure.regionprops(labels):
        if region.area < min_area_pixels:
            continue

        min_row, min_col, max_row, max_col = region.bbox

        box_width = max_col - min_col
        box_height = max_row - min_row
        x_center = min_col + box_width / 2
        y_center = min_row + box_height / 2

        class_id = 0
        yolo_rows.append(
            [
                class_id,
                x_center / image_width,
                y_center / image_height,
                box_width / image_width,
                box_height / image_height,
            ]
        )

    return yolo_rows

# 9단계. YOLO label 파일 저장 함수 만들기
def write_yolo_label_file(yolo_rows, label_path):
    lines = []

    for row in yolo_rows:
        class_id, x_center, y_center, width, height = row
        lines.append(
            f"{class_id} "
            f"{x_center:.6f} "
            f"{y_center:.6f} "
            f"{width:.6f} "
            f"{height:.6f}"
        )

    label_path.write_text("\n".join(lines), encoding="utf-8")

# 10단계. 이미지와 mask를 YOLO 데이터셋으로 변환하기
def convert_one_image(mask_name, image_output_dir, label_output_dir):
    image_name = mask_name.replace(".png", ".tif")
    yolo_image_name = mask_name
    yolo_label_name = mask_name.replace(".png", ".txt")

    tif_path = IMAGE_DIR / image_name
    mask_path = MASK_DIR / mask_name
    yolo_image_path = image_output_dir / yolo_image_name
    yolo_label_path = label_output_dir / yolo_label_name

    image_height, image_width = save_png_for_yolo(tif_path, yolo_image_path)

    mask_image = io.imread(mask_path)
    labels = decode_instance_mask(mask_image)
    yolo_rows = labels_to_yolo_rows(labels, image_height, image_width)
    write_yolo_label_file(yolo_rows, yolo_label_path)

    return {
        "image_file": yolo_image_name,
        "label_file": yolo_label_name,
        "nucleus_count": len(yolo_rows),
        "image_width": image_width,
        "image_height": image_height,
    }


dataset_rows = []

for mask_name in train_mask_names:
    row = convert_one_image(mask_name, YOLO_IMAGES_TRAIN_DIR, YOLO_LABELS_TRAIN_DIR)
    row["split"] = "train"
    dataset_rows.append(row)

for mask_name in val_mask_names:
    row = convert_one_image(mask_name, YOLO_IMAGES_VAL_DIR, YOLO_LABELS_VAL_DIR)
    row["split"] = "val"
    dataset_rows.append(row)

dataset_summary = pd.DataFrame(dataset_rows)

print(dataset_summary.head())
print(dataset_summary.groupby("split")["nucleus_count"].sum())

# 11단계. label preview 저장하기
def read_yolo_label_file(label_path):
    rows = []

    for line in label_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue

        class_id, x_center, y_center, width, height = line.split()
        rows.append(
            {
                "class_id": int(class_id),
                "x_center": float(x_center),
                "y_center": float(y_center),
                "width": float(width),
                "height": float(height),
            }
        )

    return rows


preview_image_path = YOLO_IMAGES_TRAIN_DIR / dataset_summary.iloc[0]["image_file"]
preview_label_path = YOLO_LABELS_TRAIN_DIR / dataset_summary.iloc[0]["label_file"]

preview_image = np.array(Image.open(preview_image_path))
preview_height, preview_width = preview_image.shape[:2]

fig, ax = plt.subplots(figsize=(6, 5))
ax.imshow(preview_image)

for row in read_yolo_label_file(preview_label_path):
    box_width = row["width"] * preview_width
    box_height = row["height"] * preview_height
    x_center = row["x_center"] * preview_width
    y_center = row["y_center"] * preview_height

    min_col = x_center - box_width / 2
    min_row = y_center - box_height / 2

    rectangle = Rectangle(
        (min_col, min_row),
        box_width,
        box_height,
        fill=False,
        edgecolor="#00FF66",
        linewidth=0.7,
    )
    ax.add_patch(rectangle)

ax.set_title("YOLO label preview")
ax.axis("off")
plt.tight_layout()

preview_path = OUTPUT_DIR / "dataset_preview.png"
plt.savefig(preview_path, dpi=150)
plt.close()

print("저장된 파일:", preview_path)

# 12단계. dataset YAML 파일 만들기
DATASET_YAML_FILE = YOLO_DATASET_DIR / "nuclei.yaml"

dataset_yaml_text = f"""path: {YOLO_DATASET_DIR.as_posix()}
train: images/train
val: images/val
names:
  0: nucleus
"""

DATASET_YAML_FILE.write_text(dataset_yaml_text, encoding="utf-8")

print(DATASET_YAML_FILE.read_text(encoding="utf-8"))

# 13단계. 학습 파라미터 다시 확인하기
training_config = {
    "model": MODEL_NAME,
    "epochs": EPOCHS,
    "imgsz": IMAGE_SIZE,
    "batch": BATCH_SIZE,
    "device": DEVICE,
    "workers": WORKERS,
    "confidence": CONFIDENCE,
    "train_images": TRAIN_IMAGE_COUNT,
    "val_images": VAL_IMAGE_COUNT,
}

print(pd.Series(training_config))

# 14단계. YOLO 모델 학습하기
def train_yolo_model():
    from ultralytics import YOLO

    best_model_path = OUTPUT_DIR / "runs" / "nuclei_yolo" / "weights" / "best.pt"

    if best_model_path.exists():
        print("이미 학습된 모델이 있습니다:", best_model_path)
        return best_model_path

    model = YOLO(MODEL_NAME)

    model.train(
        data=str(DATASET_YAML_FILE),
        epochs=EPOCHS,
        imgsz=IMAGE_SIZE,
        batch=BATCH_SIZE,
        device=DEVICE,
        workers=WORKERS,
        project=str(OUTPUT_DIR / "runs"),
        name="nuclei_yolo",
        exist_ok=True,
        patience=3,
        seed=0,
    )

    return best_model_path


best_model_path = train_yolo_model()

print("학습된 모델:", best_model_path)

# 15단계. validation 이미지에서 예측하기
from ultralytics import YOLO

trained_model = YOLO(best_model_path)

prediction_results = trained_model.predict(
    source=str(YOLO_IMAGES_VAL_DIR),
    imgsz=IMAGE_SIZE,
    conf=CONFIDENCE,
    device=DEVICE,
    save=True,
    project=str(OUTPUT_DIR / "predictions"),
    name="val_examples",
    exist_ok=True,
)

print("예측한 이미지 수:", len(prediction_results))
print("예측 이미지 저장 폴더:", OUTPUT_DIR / "predictions" / "val_examples")

# 16단계. 실제 nucleus 수와 예측 nucleus 수 비교하기
ground_truth_counts = {}

for label_path in YOLO_LABELS_VAL_DIR.glob("*.txt"):
    image_name = label_path.name.replace(".txt", ".png")
    label_rows = read_yolo_label_file(label_path)
    ground_truth_counts[image_name] = len(label_rows)

comparison_rows = []

for result in prediction_results:
    image_name = Path(result.path).name

    if result.boxes is None:
        predicted_count = 0
    else:
        predicted_count = len(result.boxes)

    comparison_rows.append(
        {
            "image_file": image_name,
            "ground_truth_count": ground_truth_counts.get(image_name, 0),
            "predicted_count": predicted_count,
        }
    )

count_comparison = pd.DataFrame(comparison_rows)
count_comparison["difference"] = (
    count_comparison["predicted_count"]
    - count_comparison["ground_truth_count"]
)

comparison_path = OUTPUT_DIR / "count_comparison.csv"
count_comparison.to_csv(comparison_path, index=False)

print(count_comparison)
print("저장된 파일:", comparison_path)

# 17단계. 개수 비교 그래프 저장하기
plot_data = count_comparison.sort_values("ground_truth_count").copy()
plot_data["image_index"] = range(1, len(plot_data) + 1)

plt.figure(figsize=(8, 4))
plt.bar(
    plot_data["image_index"] - 0.2,
    plot_data["ground_truth_count"],
    width=0.4,
    label="Ground truth",
)
plt.bar(
    plot_data["image_index"] + 0.2,
    plot_data["predicted_count"],
    width=0.4,
    label="YOLO prediction",
)
plt.xlabel("Validation image")
plt.ylabel("Nucleus count")
plt.title("Ground truth vs YOLO predicted nuclei count")
plt.legend()
plt.tight_layout()

comparison_plot_path = OUTPUT_DIR / "count_comparison.png"
plt.savefig(comparison_plot_path, dpi=150)
plt.close()

print("저장된 파일:", comparison_plot_path)
