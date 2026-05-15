"""
프로젝트 4. 현미경 이미지에서 세포핵 측정하기 참고용 완성 코드.

프로젝트 문서의 단계별 코드를 하나로 모은 파일입니다.
먼저 문서를 따라 직접 입력해 보고, 실행이 막히거나 전체 구조를 확인하고 싶을 때 참고하세요.
"""

# 1단계. 필요한 기능 불러오기
from pathlib import Path
from urllib.request import urlretrieve
from zipfile import ZipFile

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from skimage import exposure, io, measure, segmentation

# 2단계. 폴더와 파일 경로 준비하기
PROJECT_DIR = Path(__file__).resolve().parents[1] / "04_microscopy_nuclei_measurement"
DATA_DIR = PROJECT_DIR / "data" / "raw"
OUTPUT_DIR = PROJECT_DIR / "outputs"

IMAGE_DIR = DATA_DIR / "images"
MASK_DIR = DATA_DIR / "masks"
METADATA_DIR = DATA_DIR / "metadata"

DATA_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

print("데이터 폴더:", DATA_DIR)
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

# 5단계. 분석할 이미지 목록 고르기
training_list_path = METADATA_DIR / "training.txt"

training_mask_names = [
    line.strip()
    for line in training_list_path.read_text(encoding="utf-8").splitlines()
    if line.strip()
]

selected_image_count = 20
selected_mask_names = training_mask_names[:selected_image_count]
selected_image_names = [
    mask_name.replace(".png", ".tif")
    for mask_name in selected_mask_names
]

print("training 목록 이미지 수:", len(training_mask_names))
print("선택한 이미지 수:", len(selected_image_names))
print("첫 번째 이미지:", selected_image_names[0])
print("첫 번째 mask:", selected_mask_names[0])

# 6단계. 현미경 이미지 읽기
example_image_name = selected_image_names[0]
example_mask_name = selected_mask_names[0]

example_image_path = IMAGE_DIR / example_image_name
example_mask_path = MASK_DIR / example_mask_name

image = io.imread(example_image_path)

print("이미지 크기:", image.shape)
print("자료형:", image.dtype)
print("최솟값:", image.min())
print("최댓값:", image.max())

# 7단계. 이미지 정규화해서 보기
def normalize_image(image):
    return exposure.rescale_intensity(
        image.astype(float),
        in_range="image",
        out_range=(0, 1),
    )


image_normalized = normalize_image(image)

plt.figure(figsize=(6, 5))
plt.imshow(image_normalized, cmap="gray")
plt.title("Example microscopy image")
plt.axis("off")
plt.tight_layout()

raw_image_path = OUTPUT_DIR / "example_raw_image.png"
plt.savefig(raw_image_path, dpi=150)
plt.close()

print("저장된 파일:", raw_image_path)

# 8단계. mask 읽기
mask_image = io.imread(example_mask_path)

print("mask 크기:", mask_image.shape)
print("mask 자료형:", mask_image.dtype)
print("mask 최솟값:", mask_image.min())
print("mask 최댓값:", mask_image.max())
print("원본 이미지의 세로, 가로:", image.shape[:2])
print("mask의 세로, 가로:", mask_image.shape[:2])

# 9단계. mask를 nucleus label로 바꾸기
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


labels = decode_instance_mask(mask_image)

print("nucleus 개수:", labels.max())
print("label image 크기:", labels.shape)

# 10단계. 원본 이미지 위에 nucleus boundary 표시하기
boundaries = segmentation.find_boundaries(labels, mode="outer")

overlay = np.dstack(
    [
        image_normalized,
        image_normalized,
        image_normalized,
    ]
)
overlay[boundaries] = [1, 0, 0]

plt.figure(figsize=(6, 5))
plt.imshow(overlay)
plt.title("Nucleus boundaries")
plt.axis("off")
plt.tight_layout()

overlay_path = OUTPUT_DIR / "example_nuclei_overlay.png"
plt.savefig(overlay_path, dpi=150)
plt.close()

print("저장된 파일:", overlay_path)

# 11단계. nucleus별 측정값 계산하기
properties = measure.regionprops_table(
    labels,
    intensity_image=image,
    properties=(
        "label",
        "area",
        "centroid",
        "bbox",
        "mean_intensity",
        "max_intensity",
    ),
)

example_measurements = pd.DataFrame(properties)

example_measurements = example_measurements.rename(
    columns={
        "area": "area_pixels",
        "centroid-0": "centroid_y",
        "centroid-1": "centroid_x",
        "bbox-0": "bbox_min_row",
        "bbox-1": "bbox_min_col",
        "bbox-2": "bbox_max_row",
        "bbox-3": "bbox_max_col",
    }
)

print(example_measurements.head())

# 12단계. bounding box 그리기
regions = measure.regionprops(labels, intensity_image=image)

fig, ax = plt.subplots(figsize=(6, 5))
ax.imshow(image_normalized, cmap="gray")

for region in regions:
    min_row, min_col, max_row, max_col = region.bbox

    rectangle = Rectangle(
        (min_col, min_row),
        max_col - min_col,
        max_row - min_row,
        fill=False,
        edgecolor="#00FF66",
        linewidth=0.7,
    )

    ax.add_patch(rectangle)

ax.set_title("Nucleus bounding boxes")
ax.axis("off")
plt.tight_layout()

box_path = OUTPUT_DIR / "example_bounding_boxes.png"
plt.savefig(box_path, dpi=150)
plt.close()

print("저장된 파일:", box_path)

# 13단계. 여러 이미지 반복 처리하기
def measure_nuclei_in_image(image_name, mask_name):
    image_path = IMAGE_DIR / image_name
    mask_path = MASK_DIR / mask_name

    image = io.imread(image_path)
    mask_image = io.imread(mask_path)
    labels = decode_instance_mask(mask_image)

    properties = measure.regionprops_table(
        labels,
        intensity_image=image,
        properties=(
            "label",
            "area",
            "centroid",
            "bbox",
            "mean_intensity",
            "max_intensity",
        ),
    )

    measurements = pd.DataFrame(properties)

    measurements = measurements.rename(
        columns={
            "area": "area_pixels",
            "centroid-0": "centroid_y",
            "centroid-1": "centroid_x",
            "bbox-0": "bbox_min_row",
            "bbox-1": "bbox_min_col",
            "bbox-2": "bbox_max_row",
            "bbox-3": "bbox_max_col",
        }
    )

    measurements["image_file"] = image_name
    measurements["mask_file"] = mask_name
    measurements["image_height"] = image.shape[0]
    measurements["image_width"] = image.shape[1]

    return measurements


measurement_tables = []

for image_name, mask_name in zip(selected_image_names, selected_mask_names):
    image_measurements = measure_nuclei_in_image(image_name, mask_name)
    measurement_tables.append(image_measurements)
    print(mask_name, "nucleus 수:", len(image_measurements))

nuclei_measurements = pd.concat(measurement_tables, ignore_index=True)

print("전체 nucleus 수:", len(nuclei_measurements))
print(nuclei_measurements.head())

# 14단계. metadata 연결하기
metadata_path = METADATA_DIR / "filenames_and_plates.csv"

metadata = pd.read_csv(
    metadata_path,
    header=None,
    names=["mask_file", "plate"],
)

nuclei_measurements = nuclei_measurements.merge(
    metadata,
    on="mask_file",
    how="left",
)

print(nuclei_measurements[["image_file", "mask_file", "plate"]].head())

# 15단계. nucleus별 측정 CSV 저장하기
nuclei_measurements_path = OUTPUT_DIR / "nuclei_measurements.csv"
nuclei_measurements.to_csv(nuclei_measurements_path, index=False)

print("저장된 파일:", nuclei_measurements_path)
print(pd.read_csv(nuclei_measurements_path).head())

# 16단계. 이미지별 요약표 만들기
image_summary = (
    nuclei_measurements
    .groupby(["image_file", "mask_file", "plate"], as_index=False)
    .agg(
        nucleus_count=("label", "count"),
        mean_area_pixels=("area_pixels", "mean"),
        median_area_pixels=("area_pixels", "median"),
        mean_intensity=("mean_intensity", "mean"),
        median_intensity=("mean_intensity", "median"),
    )
)

print(image_summary.head())

# 17단계. 이미지별 요약 CSV 저장하기
image_summary_path = OUTPUT_DIR / "image_summary.csv"
image_summary.to_csv(image_summary_path, index=False)

print("저장된 파일:", image_summary_path)
print(pd.read_csv(image_summary_path).head())

# 18단계. nucleus 면적 분포 그리기
plt.figure(figsize=(7, 4))
plt.hist(nuclei_measurements["area_pixels"], bins=40, color="#4C78A8")
plt.xlabel("Nucleus area (pixels)")
plt.ylabel("Count")
plt.title("Nucleus area distribution")
plt.tight_layout()

area_plot_path = OUTPUT_DIR / "nucleus_area_distribution.png"
plt.savefig(area_plot_path, dpi=150)
plt.close()

print("저장된 파일:", area_plot_path)

# 19단계. nucleus 평균 밝기 분포 그리기
plt.figure(figsize=(7, 4))
plt.hist(nuclei_measurements["mean_intensity"], bins=40, color="#F58518")
plt.xlabel("Mean nucleus intensity")
plt.ylabel("Count")
plt.title("Nucleus intensity distribution")
plt.tight_layout()

intensity_plot_path = OUTPUT_DIR / "nucleus_intensity_distribution.png"
plt.savefig(intensity_plot_path, dpi=150)
plt.close()

print("저장된 파일:", intensity_plot_path)

# 20단계. 이미지별 nucleus 개수 그리기
plot_summary = image_summary.sort_values("nucleus_count", ascending=False).copy()
plot_summary["image_index"] = range(1, len(plot_summary) + 1)

plt.figure(figsize=(8, 4))
plt.bar(plot_summary["image_index"], plot_summary["nucleus_count"], color="#54A24B")
plt.xlabel("Selected image")
plt.ylabel("Nucleus count")
plt.title("Nucleus count by image")
plt.tight_layout()

count_plot_path = OUTPUT_DIR / "image_nuclei_count.png"
plt.savefig(count_plot_path, dpi=150)
plt.close()

print("저장된 파일:", count_plot_path)
