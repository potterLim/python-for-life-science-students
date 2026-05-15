# 프로젝트 4. 현미경 이미지에서 세포핵 측정하기

실제 공개 형광 현미경 이미지와 nucleus mask를 사용해, 이미지 속 세포핵의 개수와 크기, 밝기를 측정합니다.

전체 흐름은 다음과 같습니다.

1. 공개 현미경 이미지와 nucleus mask를 내려받습니다.
2. 이미지를 숫자 배열로 읽고, mask와 어떻게 대응되는지 확인합니다.
3. mask를 이용해 nucleus별 측정값을 계산합니다.
4. 여러 이미지의 측정 결과를 표와 그래프로 정리합니다.

이 프로젝트를 마치면 정규화한 예시 이미지, nucleus overlay 이미지, bounding box 이미지, nucleus별 측정 CSV, 이미지별 요약 CSV, 분포 그래프들이 만들어집니다.

## 사용할 데이터셋

데이터셋: [BBBC039 - Nuclei of U2OS cells in a chemical screen](https://bbbc.broadinstitute.org/BBBC039/)

출처:

- 저장소: [Broad Bioimage Benchmark Collection](https://bbbc.broadinstitute.org/)
- accession: [BBBC039](https://bbbc.broadinstitute.org/BBBC039/)
- 이미지 파일: [images.zip](https://data.broadinstitute.org/bbbc/BBBC039/images.zip)
- mask 파일: [masks.zip](https://data.broadinstitute.org/bbbc/BBBC039/masks.zip)
- metadata 파일: [metadata.zip](https://data.broadinstitute.org/bbbc/BBBC039/metadata.zip)
- 라이선스: CC0

BBBC039는 U2OS 세포의 핵을 Hoechst stain으로 촬영한 형광 현미경 이미지 데이터셋입니다. BBBC 설명에 따르면 총 200개의 field of view가 있고, 이미지는 520 x 696 pixel, 16-bit TIFF 형식입니다.

이 데이터셋에는 원본 이미지뿐 아니라 nucleus mask도 함께 들어 있습니다. mask는 이미지에서 어디가 nucleus인지 표시해 둔 annotation입니다.

| 파일 | 크기 | 설명 |
| --- | ---: | --- |
| `images.zip` | 약 77.9 MB | 원본 형광 현미경 TIFF 이미지 |
| `masks.zip` | 약 2.8 MB | nucleus mask PNG 이미지 |
| `metadata.zip` | 약 18 KB | 이미지 목록과 train/validation/test 구분 |

이번 프로젝트에서는 segmentation 모델을 새로 만들지는 않습니다. 이미 제공된 mask를 사용해, 이미지 안의 nucleus를 어떻게 측정하고 표로 정리하는지에 집중합니다.

## 작업 파일 만들기

먼저 `projects/04_microscopy_nuclei_measurement/` 폴더를 만들고, 그 안에 `analysis.py` 파일을 만듭니다.

프로젝트 1, 2에서는 표 데이터를 다뤘고, 프로젝트 3에서는 서열 파일을 다뤘습니다. 이번에는 생명과학에서 자주 만나는 이미지 데이터를 다룹니다.

진행을 마치면 아래와 같은 구조가 됩니다.

```text
projects/
└── 04_microscopy_nuclei_measurement/
    ├── analysis.py
    ├── data/
    │   └── raw/
    │       ├── images.zip
    │       ├── masks.zip
    │       ├── metadata.zip
    │       ├── images/
    │       ├── masks/
    │       └── metadata/
    └── outputs/
        ├── example_raw_image.png
        ├── example_nuclei_overlay.png
        ├── example_bounding_boxes.png
        ├── nucleus_area_distribution.png
        ├── nucleus_intensity_distribution.png
        ├── image_nuclei_count.png
        ├── nuclei_measurements.csv
        └── image_summary.csv
```

## 1단계. 필요한 기능 불러오기

먼저 `analysis.py`에 아래 코드를 입력합니다.

```python
from pathlib import Path
from urllib.request import urlretrieve
from zipfile import ZipFile

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from skimage import exposure, io, measure, segmentation
```

이번 프로젝트에서는 이미지 분석을 위해 `scikit-image`를 사용합니다.

새로 사용하는 기능은 다음과 같습니다.

- `io`: TIFF, PNG 같은 이미지 파일을 읽습니다.
- `exposure`: 이미지 intensity 범위를 보기 좋게 조정합니다.
- `measure`: mask에서 object를 찾고 면적, 중심 좌표, 밝기 같은 값을 측정합니다.
- `segmentation`: mask의 경계선을 찾을 때 사용합니다.
- `Rectangle`: 이미지 위에 bounding box를 그릴 때 사용합니다.

필요한 라이브러리가 없다면 아래 명령을 한 번 실행합니다.

```bash
python -m pip install numpy pandas matplotlib scikit-image
```

## 2단계. 폴더와 파일 경로 준비하기

데이터 파일과 출력 파일을 저장할 위치를 정합니다.

```python
PROJECT_DIR = Path(__file__).resolve().parent
DATA_DIR = PROJECT_DIR / "data" / "raw"
OUTPUT_DIR = PROJECT_DIR / "outputs"

IMAGE_DIR = DATA_DIR / "images"
MASK_DIR = DATA_DIR / "masks"
METADATA_DIR = DATA_DIR / "metadata"

DATA_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

print("데이터 폴더:", DATA_DIR)
print("출력 폴더:", OUTPUT_DIR)
```

폴더를 준비하는 흐름은 앞 프로젝트들과 같습니다. 이번에는 압축을 푼 뒤 `images/`, `masks/`, `metadata/` 폴더가 생깁니다.

## 3단계. 데이터 다운로드하기

BBBC039에서 이미지, mask, metadata ZIP 파일을 다운로드합니다.

```python
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
```

`images.zip`은 약 77.9 MB입니다. 다운로드에 시간이 조금 걸릴 수 있습니다.

## 4단계. 압축 풀기

다운로드한 ZIP 파일을 풉니다. 압축을 푼 뒤에는 이미지, mask, metadata 파일이 실제로 들어왔는지도 함께 확인합니다.

```python
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
```

ZIP 파일 안에는 macOS에서 생긴 보조 파일이 함께 들어 있을 수 있습니다. `__MACOSX/`로 시작하는 파일은 분석에 필요하지 않으므로 건너뜁니다.

이미지 파일은 `.tif`, mask 파일은 `.png` 형식입니다. 파일 수와 첫 파일 이름을 확인해 두면, 이후 단계에서 이미지와 mask를 제대로 짝지었는지 확인하기 쉽습니다.

## 5단계. 분석할 이미지 목록 고르기

BBBC039에는 여러 이미지가 들어 있습니다. 처음에는 metadata 안의 training 목록에서 20개만 골라, 이미지 한 장에서 만든 측정 과정을 여러 장에 적용해 봅니다. `20`은 특별한 생물학적 기준이 아니라, 처음 실행할 때 처리 시간과 결과 파일 크기를 적당하게 유지하기 위한 값입니다.

```python
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
```

metadata의 `training.txt`에는 mask 파일 이름이 들어 있습니다. 앞에서 파일 목록을 확인했을 때, 이미지 파일과 mask 파일은 이름의 앞부분이 같고 확장자만 달랐습니다.

```text
image: IXMtest_A06_... .tif
mask:  IXMtest_A06_... .png
```

그래서 mask 파일 이름에서 `.png`를 `.tif`로 바꾸면 대응되는 원본 이미지 이름을 얻을 수 있습니다. 이 규칙을 사용해 원본 이미지 이름과 mask 이름을 함께 준비합니다.

## 6단계. 현미경 이미지 읽기

먼저 첫 번째 이미지를 읽어 봅니다. 이미지 분석에서는 파일을 읽자마자 크기, 자료형, intensity 범위를 확인하는 습관이 중요합니다.

```python
example_image_name = selected_image_names[0]
example_mask_name = selected_mask_names[0]

example_image_path = IMAGE_DIR / example_image_name
example_mask_path = MASK_DIR / example_mask_name

image = io.imread(example_image_path)

print("이미지 크기:", image.shape)
print("자료형:", image.dtype)
print("최솟값:", image.min())
print("최댓값:", image.max())
```

이미지는 Python에서 숫자 배열로 읽힙니다.

```text
이미지 크기: (520, 696)
```

이 말은 이미지가 520개의 행과 696개의 열로 이루어져 있다는 뜻입니다. 각 위치의 숫자는 해당 pixel의 intensity입니다.

`dtype`은 pixel 값이 어떤 숫자 형식으로 저장되어 있는지 알려줍니다. 이 데이터의 TIFF 이미지는 16-bit 형식입니다. 16-bit 이미지는 0부터 65,535까지의 값을 가질 수 있습니다. 실제 최솟값과 최댓값은 이미지마다 다를 수 있습니다.

## 7단계. 이미지 정규화해서 보기

현미경 이미지는 원본 intensity 범위가 넓어서 그대로 그리면 어둡게 보일 수 있습니다. 그래서 화면에 보기 좋게 0부터 1 사이 값으로 정규화합니다.

```python
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
```

정규화는 화면에 보여주기 위한 처리입니다. 원본 파일을 바꾸는 것은 아닙니다.

`cmap="gray"`는 이미지를 흑백으로 표시하겠다는 뜻입니다.

## 8단계. mask 읽기

이제 같은 이미지에 대응되는 mask 파일을 읽습니다. 원본 이미지는 intensity 값이고, mask는 어느 pixel이 nucleus에 속하는지를 표시한 annotation입니다.

```python
mask_image = io.imread(example_mask_path)

print("mask 크기:", mask_image.shape)
print("mask 자료형:", mask_image.dtype)
print("mask 최솟값:", mask_image.min())
print("mask 최댓값:", mask_image.max())
print("원본 이미지의 세로, 가로:", image.shape[:2])
print("mask의 세로, 가로:", mask_image.shape[:2])
```

BBBC039의 mask는 PNG 파일입니다. 배경은 검은색이고, nucleus 영역은 색으로 표시되어 있습니다.

mask는 원본 이미지와 같은 세로, 가로 크기를 가집니다. PNG mask는 색 정보를 담고 있어서 출력되는 `shape`에 색 채널이 함께 보일 수 있지만, 앞의 두 값이 원본 이미지의 세로, 가로와 같으면 같은 위치의 pixel끼리 대응됩니다.

```text
원본 이미지: 520 x 696
mask 이미지: 520 x 696
```

## 9단계. mask를 nucleus label로 바꾸기

mask를 눈으로 보면 nucleus 영역이 색으로 구분되어 있습니다. 하지만 면적이나 밝기를 계산하려면 각각의 nucleus가 숫자 label로 구분되어 있어야 합니다.

예를 들어 label image는 이런 식으로 생각할 수 있습니다.

```text
0: 배경
1: 첫 번째 nucleus
2: 두 번째 nucleus
3: 세 번째 nucleus
...
```

BBBC039 mask는 색으로 nucleus를 표시합니다. 그래서 색 정보를 label 번호로 바꾸는 함수를 만듭니다.

```python
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
```

여기서 `0`은 배경이고, `1`부터는 각각의 nucleus를 뜻합니다.

`measure.label()`은 서로 붙어 있는 pixel들을 하나의 object로 묶어 번호를 붙입니다. 이 번호가 있어야 nucleus별 면적이나 밝기를 계산할 수 있습니다.

## 10단계. 원본 이미지 위에 nucleus boundary 표시하기

측정으로 넘어가기 전에 mask가 원본 이미지와 잘 맞는지 확인합니다. label image의 경계선을 원본 이미지 위에 겹쳐 보면, nucleus 위치가 제대로 맞는지 눈으로 볼 수 있습니다.

```python
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
```

`find_boundaries()`는 label이 바뀌는 경계선을 찾아줍니다. 여기서는 그 경계선을 빨간색으로 표시했습니다.

이미지 분석을 할 때는 원본 이미지와 mask가 잘 맞는지 눈으로 확인하는 과정이 중요합니다. 여기서 어긋나 보이면 이후에 계산하는 면적과 밝기도 믿기 어렵습니다.

## 11단계. nucleus별 측정값 계산하기

이제 각 nucleus의 면적, 중심 좌표, bounding box, 평균 밝기를 측정합니다. label image는 “어디가 같은 nucleus인지”를 알려주고, 원본 이미지는 “그 nucleus 영역의 밝기가 얼마인지”를 알려줍니다.

```python
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
```

`regionprops_table()`은 label image에서 object별 정보를 표로 만들어 줍니다.

이번에 계산한 값은 다음과 같습니다.

| 열 이름 | 의미 |
| --- | --- |
| `label` | nucleus 번호 |
| `area_pixels` | nucleus 면적. 단위는 pixel 수 |
| `centroid_y`, `centroid_x` | nucleus 중심 좌표 |
| `bbox_min_row`, `bbox_min_col` | bounding box의 왼쪽 위 좌표 |
| `bbox_max_row`, `bbox_max_col` | bounding box의 오른쪽 아래 좌표 |
| `mean_intensity` | nucleus 영역의 평균 밝기 |
| `max_intensity` | nucleus 영역의 최대 밝기 |

`intensity_image=image`를 함께 넣었기 때문에, mask의 각 nucleus가 원본 이미지에서 얼마나 밝은지도 계산할 수 있습니다.

## 12단계. bounding box 그리기

bounding box는 object를 감싸는 사각형입니다. 프로젝트 5에서 YOLO를 다룰 때도 bounding box 개념이 중요하게 나옵니다.

```python
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
```

각 초록색 사각형은 nucleus 하나를 감싸는 bounding box입니다.

segmentation mask는 object의 모양을 pixel 단위로 표시하고, bounding box는 object를 사각형 하나로 간단히 감쌉니다.

## 13단계. 여러 이미지 반복 처리하기

첫 번째 이미지에서 읽기, mask 변환, boundary 확인, 측정까지 해봤습니다. 이제 같은 과정을 선택한 20개 이미지에 반복합니다.

```python
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
```

반복문을 사용하면 같은 측정 과정을 여러 이미지에 적용할 수 있습니다. 한 이미지에서 잘 동작하는 코드를 함수로 묶어 두면, 여러 파일을 처리할 때 같은 실수를 줄일 수 있습니다.

여기서 만들어지는 `nuclei_measurements`는 nucleus 하나가 한 행인 표입니다.

## 14단계. metadata 연결하기

nucleus별 측정표에는 면적과 밝기 같은 측정값이 들어 있습니다. 이제 metadata를 붙여 각 이미지가 어느 plate에서 온 것인지도 함께 보관합니다.

```python
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
```

프로젝트 2에서 sample metadata를 발현값 표에 붙였던 것처럼, 여기서는 이미지 metadata를 nucleus 측정 표에 붙입니다.

공통으로 가지고 있는 열은 `mask_file`입니다.

## 15단계. nucleus별 측정 CSV 저장하기

측정한 nucleus별 정보를 CSV 파일로 저장합니다.

```python
nuclei_measurements_path = OUTPUT_DIR / "nuclei_measurements.csv"
nuclei_measurements.to_csv(nuclei_measurements_path, index=False)

print("저장된 파일:", nuclei_measurements_path)
print(pd.read_csv(nuclei_measurements_path).head())
```

이 파일은 nucleus 하나를 한 행으로 가지는 표입니다. 이후에 면적 분포, 밝기 분포, 이미지별 요약을 만들 때 이 표를 사용합니다.

## 16단계. 이미지별 요약표 만들기

nucleus별 표를 이미지별로 요약합니다.

```python
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
```

`image_summary`는 이미지 하나가 한 행인 표입니다.

예를 들어 `nucleus_count`는 한 이미지 안에 nucleus가 몇 개 있는지 알려줍니다.

## 17단계. 이미지별 요약 CSV 저장하기

이미지별 요약표를 CSV 파일로 저장합니다.

```python
image_summary_path = OUTPUT_DIR / "image_summary.csv"
image_summary.to_csv(image_summary_path, index=False)

print("저장된 파일:", image_summary_path)
print(pd.read_csv(image_summary_path).head())
```

이제 두 종류의 표가 생겼습니다.

| 파일 | 한 행이 의미하는 단위 |
| --- | --- |
| `nuclei_measurements.csv` | nucleus 하나 |
| `image_summary.csv` | 이미지 하나 |

같은 데이터라도 어떤 단위로 요약하느냐에 따라 표의 모양이 달라집니다.

## 18단계. nucleus 면적 분포 그리기

먼저 nucleus 면적 분포를 히스토그램으로 봅니다.

```python
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
```

히스토그램은 값의 분포를 볼 때 사용합니다. 여기서는 nucleus 면적이 어느 범위에 많이 분포하는지 볼 수 있습니다.

## 19단계. nucleus 평균 밝기 분포 그리기

이번에는 nucleus별 평균 밝기 분포를 봅니다.

```python
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
```

Hoechst stain은 DNA와 관련된 fluorescence signal을 보여줍니다. 여기서 계산하는 평균 밝기는 nucleus 영역 안의 평균 pixel intensity입니다.

## 20단계. 이미지별 nucleus 개수 그리기

마지막으로 선택한 이미지마다 nucleus가 몇 개씩 있는지 막대그래프로 저장합니다.

```python
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
```

이미지 파일 이름은 길기 때문에 x축에는 번호만 표시했습니다. 자세한 파일 이름과 nucleus 수는 `image_summary.csv`에서 확인할 수 있습니다.

## 최종적으로 만들어지는 파일

끝까지 실행하면 `outputs/` 폴더에 다음 파일들이 생깁니다.

```text
projects/04_microscopy_nuclei_measurement/outputs/
├── example_raw_image.png
├── example_nuclei_overlay.png
├── example_bounding_boxes.png
├── nucleus_area_distribution.png
├── nucleus_intensity_distribution.png
├── image_nuclei_count.png
├── nuclei_measurements.csv
└── image_summary.csv
```

| 파일명 | 의미 |
| --- | --- |
| `example_raw_image.png` | 정규화한 예시 현미경 이미지 |
| `example_nuclei_overlay.png` | 원본 이미지 위에 nucleus boundary를 표시한 이미지 |
| `example_bounding_boxes.png` | nucleus bounding box를 표시한 이미지 |
| `nucleus_area_distribution.png` | nucleus 면적 분포 |
| `nucleus_intensity_distribution.png` | nucleus 평균 밝기 분포 |
| `image_nuclei_count.png` | 이미지별 nucleus 개수 |
| `nuclei_measurements.csv` | nucleus별 면적, 밝기, 중심 좌표, bounding box |
| `image_summary.csv` | 이미지별 nucleus 개수와 평균 측정값 |

## 완성 참고 코드

완성된 참고 코드는 [프로젝트 4 완성 참고 코드](reference_code/04_microscopy_nuclei_measurement.py)에서 확인할 수 있습니다. 먼저 문서를 따라 직접 입력해 보고, 실행이 잘 되지 않거나 전체 구조를 비교하고 싶을 때 참고하는 것을 권장합니다.

## 자주 생기는 문제

### `ModuleNotFoundError: No module named 'skimage'`가 뜨는 경우

`scikit-image`가 설치되어 있지 않은 상태입니다. 1단계의 설치 명령을 실행한 뒤 다시 실행합니다.

### 다운로드가 오래 걸리는 경우

`images.zip`이 약 77.9 MB라서 네트워크 상태에 따라 시간이 걸릴 수 있습니다. 한 번 다운로드한 뒤에는 같은 파일을 다시 받지 않습니다.

### `FileNotFoundError`가 뜨는 경우

압축을 푸는 단계가 제대로 실행되었는지 확인합니다. `data/raw/images/`, `data/raw/masks/`, `data/raw/metadata/` 폴더가 있는지 확인합니다.

### overlay가 이상하게 보이는 경우

이미지 파일과 mask 파일이 서로 대응되지 않을 수 있습니다. 이미지 파일 이름과 mask 파일 이름에서 확장자를 제외한 부분이 같은지 확인합니다.

```python
print(example_image_name)
print(example_mask_name)
```

## 이 프로젝트에서 해본 것

실제 형광 현미경 이미지와 nucleus mask로 다음 흐름을 따라갔습니다.

```text
1. 현미경 이미지와 mask 파일 다운로드하기
2. TIFF 이미지를 숫자 배열로 읽기
3. 16-bit intensity 이미지를 보기 좋게 정규화하기
4. PNG mask를 nucleus label image로 바꾸기
5. 원본 이미지 위에 nucleus boundary 표시하기
6. nucleus별 면적, 밝기, 중심 좌표, bounding box 측정하기
7. 여러 이미지를 반복 처리하기
8. nucleus별 측정표와 이미지별 요약표 저장하기
9. 면적 분포, 밝기 분포, 이미지별 nucleus 개수 그래프 저장하기
```

프로젝트 4에서는 이미지가 숫자 배열이라는 점, mask가 object를 구분하는 방식, 그리고 object별 측정값을 표로 만드는 흐름을 다뤘습니다.

이 흐름은 세포핵뿐 아니라 세포, colony, organoid, tissue region처럼 이미지 안의 object를 측정해야 하는 다른 생명과학 이미지 데이터에도 비슷하게 적용할 수 있습니다.
