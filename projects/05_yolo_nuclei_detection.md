# 프로젝트 5. YOLO로 현미경 이미지 속 세포핵 탐지하기

실제 공개 현미경 이미지와 nucleus mask를 사용해, YOLO object detection 모델이 학습할 수 있는 데이터셋을 만들고 작은 탐지 모델을 학습합니다.

전체 흐름은 다음과 같습니다.

1. 실행 환경을 확인하고, 필요한 YOLO 파라미터를 찾아봅니다.
2. 현미경 이미지와 mask를 YOLO 학습용 데이터셋으로 바꿉니다.
3. 작은 object detection 모델을 짧게 학습합니다.
4. 예측 결과를 확인하고, 실제 mask 기준과 간단히 비교합니다.

이 프로젝트를 마치면 YOLO 학습용 이미지와 label 파일, dataset YAML 파일, 학습 결과 폴더, 예측 이미지, 개수 비교 CSV와 그래프가 만들어집니다.

## 사용할 데이터셋

데이터셋: [BBBC039 - Nuclei of U2OS cells in a chemical screen](https://bbbc.broadinstitute.org/BBBC039/)

출처:

- 저장소: [Broad Bioimage Benchmark Collection](https://bbbc.broadinstitute.org/)
- accession: [BBBC039](https://bbbc.broadinstitute.org/BBBC039/)
- 이미지 파일: [images.zip](https://data.broadinstitute.org/bbbc/BBBC039/images.zip)
- mask 파일: [masks.zip](https://data.broadinstitute.org/bbbc/BBBC039/masks.zip)
- metadata 파일: [metadata.zip](https://data.broadinstitute.org/bbbc/BBBC039/metadata.zip)
- 라이선스: CC0

프로젝트 4에서 사용한 데이터셋과 같습니다. 다만 이번에는 목적이 조금 다릅니다. YOLO는 mask 이미지를 그대로 학습하지 않고, 이미지와 bounding box label을 짝으로 받아 object detection을 학습합니다.

그래서 원본 TIFF 이미지는 YOLO가 다루기 쉬운 PNG 이미지로 바꾸고, nucleus mask에서는 각 nucleus를 감싸는 bounding box를 계산해 YOLO label 파일로 저장합니다. 그다음 작은 모델을 짧게 학습해 validation 이미지에서 nucleus를 탐지해 봅니다.

이 프로젝트에서 YOLO는 이미지 안에서 nucleus가 있을 만한 위치를 사각형으로 찾아내는 도구로 사용합니다. 모델 구조를 직접 만들지는 않습니다. 대신 현미경 이미지와 bounding box label을 준비해서, 이미 만들어진 YOLO 모델이 이 데이터셋에 맞게 nucleus를 찾도록 짧게 학습시킵니다.

## 참고할 공식 문서

YOLO는 파라미터가 많습니다. 이 프로젝트에서는 모든 파라미터를 외우는 것이 아니라, 필요한 파라미터를 공식 문서에서 찾아 적용하는 연습도 함께 합니다.

주로 볼 공식 문서는 세 곳입니다.

| 문서 | 언제 보는가 |
| --- | --- |
| [Ultralytics Train Docs](https://docs.ultralytics.com/modes/train/) | `epochs`, `imgsz`, `batch`, `device`, `workers`, `project`, `name` 같은 학습 파라미터를 확인할 때 |
| [Ultralytics Detection Dataset Docs](https://docs.ultralytics.com/datasets/detect/) | dataset YAML 구조와 YOLO label 형식을 확인할 때 |
| [Ultralytics Predict Docs](https://docs.ultralytics.com/modes/predict/) | 예측 결과, bounding box, confidence score를 다룰 때 |

공식 문서에서 원하는 파라미터를 찾을 때는 페이지 검색을 사용하면 됩니다.

예를 들어 학습 속도가 너무 느리다면 Train Docs에서 다음 단어를 검색합니다.

```text
imgsz
batch
device
workers
epochs
```

예측 결과가 너무 많이 나오거나 너무 적게 나온다면 Predict Docs에서 다음 단어를 검색합니다.

```text
conf
boxes
Results
```

문서를 읽을 때는 다음 순서로 보는 것이 좋습니다.

1. 지금 바꾸고 싶은 문제가 무엇인지 먼저 정합니다.
2. 공식 문서에서 관련 파라미터 이름을 찾습니다.
3. 기본값과 의미를 확인합니다.
4. 한 번에 하나의 값만 바꿔서 실행합니다.
5. 결과가 어떻게 달라졌는지 기록합니다.

여러 값을 한 번에 바꾸면 어떤 값 때문에 결과가 달라졌는지 알기 어렵습니다.

## 실행 환경과 사양 안내

이 프로젝트는 작은 YOLO 모델을 짧게 학습하는 실습입니다. 최고 성능의 모델을 만드는 것이 목표가 아니라, 생명과학 이미지 데이터를 YOLO 학습 형식으로 바꾸고 실제 예측까지 이어 보는 것이 목표입니다.

권장 환경은 다음과 같습니다.

| 항목 | 권장 |
| --- | --- |
| Python | 3.10 이상 |
| RAM | 8 GB 이상 |
| 저장 공간 | 5 GB 이상 |
| GPU | 있으면 좋지만 필수는 아님 |
| 운영체제 | macOS, Windows, Linux 모두 가능 |

CPU만 있어도 실행할 수 있습니다. 다만 학습 시간이 더 오래 걸릴 수 있습니다.

환경별로 처음 시도할 설정은 다음과 같이 잡으면 됩니다.

| 환경 | 추천 설정 |
| --- | --- |
| CPU만 있음 | `epochs=3`, `imgsz=416`, `batch=2`, train 이미지 20장 |
| 일반적인 개인 컴퓨터 | `epochs=5`, `imgsz=512`, `batch=4`, train 이미지 40장 |
| Apple Silicon Mac | `device="mps"`를 시도하고, 문제가 생기면 `device="cpu"` |
| NVIDIA GPU | `device=0`, `batch=8`, `imgsz=640`도 시도 가능 |
| RAM 부족 | `batch`를 1 또는 2로 낮춤 |
| 너무 오래 걸림 | `epochs`, `imgsz`, train 이미지 수를 줄임 |
| 성능을 조금 더 보고 싶음 | `epochs`나 train 이미지 수를 늘림 |

## 이번 프로젝트에서 사용할 기본값

문서에서는 다음 기본값으로 시작합니다.

```text
model: yolo26n.pt
epochs: 5
imgsz: 512
batch: 4
device: cpu
workers: 0
confidence: 0.25
train images: 40
val images: 10
```

이 값들은 성능을 가장 좋게 내기 위한 값이 아닙니다. 처음 실행했을 때 비교적 덜 막히고, 결과까지 확인하기 위한 출발값입니다. train 이미지 40장과 validation 이미지 10장도 좋은 모델을 만들기 위한 충분한 데이터 수가 아니라, 전체 흐름을 개인 컴퓨터에서 끝까지 확인하기 위한 작은 실습용 크기입니다.

파라미터는 정답을 외우는 값이 아니라, 내 컴퓨터 환경과 실습 목적에 맞게 조절하는 값입니다. 처음에는 문서의 기본값으로 실행하고, 전체 흐름이 끝까지 돌아간 뒤 하나씩 바꿔 보는 편이 좋습니다. 작성자가 실제로 바꾸어 실행한 값은 2단계에서 함께 설명합니다.

각 파라미터의 의미는 다음과 같습니다.

| 파라미터 | 의미 | 처음 조절할 때 |
| --- | --- | --- |
| `model` | 사용할 YOLO 모델 파일 | 작게 시작하려면 nano 모델 사용 |
| `epochs` | 전체 train 데이터를 몇 번 반복해서 볼지 | 오래 걸리면 낮추고, 더 학습하고 싶으면 높임 |
| `imgsz` | 모델에 넣을 이미지 크기 | 작게 하면 빠르고, 크게 하면 더 자세히 봄 |
| `batch` | 한 번에 몇 장씩 학습할지 | 메모리 부족이면 낮춤 |
| `device` | CPU, GPU, Apple MPS 중 무엇을 쓸지 | 처음에는 `cpu`가 가장 안정적 |
| `workers` | 데이터를 불러오는 작업자 수 | 초보 실습에서는 `0`이 덜 복잡함 |
| `conf` | 예측 결과를 남길 confidence threshold | 탐지가 너무 많으면 높이고, 너무 적으면 낮춤 |

## 작업 파일 만들기

먼저 `projects/05_yolo_nuclei_detection/` 폴더를 만들고, 그 안에 `analysis.py` 파일을 만듭니다.

진행을 마치면 아래와 같은 구조가 됩니다.

```text
projects/
└── 05_yolo_nuclei_detection/
    ├── analysis.py
    ├── data/
    │   ├── raw/
    │   │   ├── images.zip
    │   │   ├── masks.zip
    │   │   ├── metadata.zip
    │   │   ├── images/
    │   │   ├── masks/
    │   │   └── metadata/
    │   └── yolo_dataset/
    │       ├── images/
    │       │   ├── train/
    │       │   └── val/
    │       ├── labels/
    │       │   ├── train/
    │       │   └── val/
    │       └── nuclei.yaml
    └── outputs/
        ├── dataset_preview.png
        ├── count_comparison.csv
        ├── count_comparison.png
        ├── predictions/
        └── runs/
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
from PIL import Image
from skimage import exposure, io, measure
```

프로젝트 4에서 사용했던 이미지 처리 기능을 다시 사용합니다.

YOLO 자체는 학습 단계에서 불러옵니다. 그러면 데이터셋을 만드는 코드와 모델을 학습하는 코드가 조금 더 분리되어 보입니다.

필요한 라이브러리가 없다면 아래 명령을 한 번 실행합니다.

```bash
python -m pip install numpy pandas matplotlib scikit-image pillow ultralytics
```

`ultralytics`를 설치하면 YOLO 모델을 Python 코드에서 불러와 학습하고 예측할 수 있습니다.

## 2단계. 폴더와 기본 파라미터 준비하기

데이터와 출력 파일을 저장할 위치를 정하고, 이번 실습에서 사용할 기본 파라미터를 적어 둡니다.

```python
PROJECT_DIR = Path(__file__).resolve().parent
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
EPOCHS = 5
IMAGE_SIZE = 512
BATCH_SIZE = 4
DEVICE = "cpu"
WORKERS = 0
CONFIDENCE = 0.25

print("YOLO 데이터셋 폴더:", YOLO_DATASET_DIR)
print("출력 폴더:", OUTPUT_DIR)
```

파라미터를 코드 위쪽에 모아 두면 나중에 조절하기 쉽습니다. 여기 적은 값들은 처음 실습을 시작하기 위한 출발값이며, 정답처럼 외울 필요는 없습니다.

`EPOCHS = 5`는 최대 5번까지 학습할 수 있다는 뜻입니다. 뒤에서 `patience=3`을 함께 사용하므로, validation 성능이 더 좋아지지 않으면 정해 둔 epoch를 모두 채우기 전에 학습이 끝날 수도 있습니다.

`IMAGE_SIZE = 512`는 YOLO가 이미지를 어느 정도 크기로 맞춰 보고 학습할지 정하는 값입니다. 값이 클수록 작은 nucleus를 더 자세히 볼 수 있지만, 학습 시간이 늘고 메모리를 더 사용합니다.

`DEVICE = "cpu"`는 CPU로 실행하겠다는 뜻입니다. 가장 빠른 설정은 아니지만, 여러 환경에서 비교적 안정적으로 시작할 수 있습니다.

작성자는 Apple Silicon Mac에서 조금 더 긴 학습 결과를 보고 싶어서 아래처럼 바꾸어 실행했습니다.

```text
EPOCHS = 50
IMAGE_SIZE = 640
DEVICE = "mps"
```

이렇게 바꾸면 학습 시간이 늘어날 수 있지만, 모델이 더 여러 번 학습하고 더 큰 이미지 크기로 nucleus를 볼 수 있습니다. 반대로 CPU에서 너무 오래 걸리면 아래 값부터 줄여 봅니다.

```text
TRAIN_IMAGE_COUNT
EPOCHS
IMAGE_SIZE
BATCH_SIZE
```

## 3단계. 데이터 다운로드하기

BBBC039에서 이미지, mask, metadata ZIP 파일을 다운로드합니다. 프로젝트 4와 같은 데이터셋을 사용하지만, 이번에는 YOLO 학습용 데이터셋을 새로 만드는 데 사용합니다.

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

다운로드한 ZIP 파일을 풉니다. 압축을 푼 뒤에는 이미지와 mask가 실제로 들어왔는지 먼저 확인합니다.

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

이미지 파일은 `.tif`, mask 파일은 `.png` 형식입니다. 이 둘은 파일 이름의 앞부분이 같고 확장자만 다릅니다. 이후에는 이 규칙을 사용해 이미지와 mask를 짝지어 처리합니다.

## 5단계. train/validation 이미지 목록 만들기

딥러닝 모델을 학습할 때는 학습에 사용할 train 이미지와, 학습 뒤 확인에 사용할 validation 이미지를 나누어 둡니다. BBBC039 metadata에는 이미 `training.txt`와 `validation.txt`가 들어 있으므로 그 목록을 사용합니다.

이번 프로젝트에서 각 목록은 다음 역할을 합니다.

| 구분 | 이 프로젝트에서의 역할 |
| --- | --- |
| train | 모델이 이미지와 label을 보고 nucleus의 모양을 배우는 데 사용합니다. |
| validation | 학습 중간과 학습 뒤에, train에 직접 쓰지 않은 이미지에서도 어느 정도 찾는지 확인하는 데 사용합니다. |
| test | 최종 평가를 위해 따로 남겨 두는 데이터입니다. 이 프로젝트에서는 흐름을 단순하게 유지하기 위해 사용하지 않습니다. |

여기서 validation은 시험 문제를 미리 외우는 용도가 아닙니다. 모델이 train 이미지에만 맞춰진 상태인지, 아니면 처음 보는 이미지에서도 nucleus를 어느 정도 찾는지 확인하는 기준에 가깝습니다.

```python
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
```

BBBC039 metadata는 train, validation, test 목록을 제공합니다. 여기서는 그 목록을 그대로 사용하되, 실행 시간을 줄이기 위해 앞에서 정한 개수만 선택합니다.

## 6단계. mask를 label image로 바꾸는 함수 만들기

mask는 nucleus 영역을 색으로 표시한 PNG 이미지입니다. 하지만 bounding box를 계산하려면 먼저 nucleus 하나하나를 숫자 label로 구분해야 합니다.

이 단계가 조금 낯설 수 있습니다. 지금 하고 싶은 일은 “이미지 안의 nucleus마다 사각형을 하나씩 만들기”입니다. 그런데 원본 mask는 사람이 보기에는 색으로 구분되어 있지만, YOLO가 바로 읽을 수 있는 형식은 아닙니다.

그래서 중간에 한 번 더 바꿉니다.

```text
색으로 표시된 mask
-> nucleus마다 다른 숫자를 붙인 label image
-> nucleus마다 하나의 bounding box
-> YOLO가 읽는 TXT label
```

label image에서는 배경을 `0`으로 두고, 첫 번째 nucleus는 `1`, 두 번째 nucleus는 `2`처럼 표시합니다. 이렇게 숫자로 구분해 두면 Python이 각 nucleus의 위치와 크기를 따로 계산할 수 있습니다.

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
```

YOLO는 mask를 직접 읽는 것이 아니라 bounding box label을 읽습니다. 그래서 먼저 mask에서 nucleus object를 구분하고, 각 object를 감싸는 bounding box를 계산해야 합니다.

코드 안의 `color_code`는 RGB 색을 하나의 숫자로 바꾸기 위한 값입니다. 같은 색으로 표시된 pixel을 먼저 찾고, `measure.label()`로 서로 붙어 있는 부분을 nucleus object로 구분합니다. 이 과정이 끝나면 “색으로 된 그림”이 “object 번호가 붙은 숫자 배열”로 바뀝니다.

## 7단계. TIFF 이미지를 PNG로 변환하는 함수 만들기

원본 현미경 이미지는 16-bit TIFF입니다. 일반적인 YOLO 학습에서는 PNG나 JPG처럼 다루기 쉬운 이미지 형식을 많이 사용합니다. 여기서는 원본 intensity를 보기 좋게 0부터 255 사이로 맞춘 뒤, 8-bit RGB PNG 이미지로 저장합니다.

```python
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
```

여기서는 흑백 이미지를 RGB 3채널 이미지처럼 저장합니다. 세 채널 값은 모두 같습니다.

```text
R = grayscale
G = grayscale
B = grayscale
```

## 8단계. bounding box를 YOLO label 형식으로 바꾸기

mask에서 nucleus를 label image로 바꾸면, nucleus마다 `bbox`를 계산할 수 있습니다. `bbox`는 pixel 좌표로 된 사각형입니다.

Ultralytics detection dataset 문서에 따르면 YOLO label 파일은 이미지마다 하나씩 만들고, 한 줄에 object 하나를 적습니다.

형식은 다음과 같습니다.

```text
class x_center y_center width height
```

좌표는 pixel 값이 아니라 0부터 1 사이로 정규화된 값입니다. 그래서 pixel 좌표로 얻은 bounding box를 이미지의 가로, 세로 크기로 나누어 YOLO 형식에 맞춥니다.

```python
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
```

이번 프로젝트의 class는 하나뿐입니다.

```text
0: nucleus
```

그래서 모든 줄의 첫 값은 `0`입니다.

`min_area_pixels=20`은 너무 작은 조각을 label에서 제외하기 위한 기준입니다. 생물학적으로 정해진 기준이라기보다, mask를 label로 바꾸는 과정에서 생길 수 있는 아주 작은 object를 제외하고 시작하기 위한 실습용 기준입니다.

## 9단계. YOLO label 파일 저장 함수 만들기

YOLO label 파일은 텍스트 파일입니다. 각 줄에는 nucleus 하나의 class와 bounding box 좌표가 들어갑니다.

```python
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
```

소수점은 여섯 자리까지만 저장합니다. 이 정도면 이미지 좌표를 표현하기에 충분합니다.

## 10단계. 이미지와 mask를 YOLO 데이터셋으로 변환하기

이제 선택한 train/validation 이미지를 YOLO 형식으로 변환합니다. 한 이미지에 대해 할 일은 세 가지입니다.

1. mask 이름에서 대응되는 TIFF 이미지 이름을 찾습니다.
2. TIFF 이미지를 PNG 이미지로 저장합니다.
3. mask에서 bounding box를 계산해 같은 이름의 TXT label 파일로 저장합니다.

```python
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
```

이 단계가 프로젝트 5의 핵심입니다. 기존 mask에서 object를 구분하고, object마다 bounding box를 계산한 뒤, YOLO가 읽을 수 있는 TXT label로 저장했습니다. 그래서 bounding box를 손으로 직접 그리지 않아도 학습용 label을 만들 수 있습니다.

여기까지 오면 아직 모델을 학습한 것은 아닙니다. 대신 학습에 필요한 재료를 만든 상태입니다.

```text
원본 TIFF 이미지
-> YOLO 학습용 PNG 이미지

원본 PNG mask
-> YOLO 학습용 TXT label
```

딥러닝 모델은 이 이미지와 label의 짝을 보면서 “이런 모양과 밝기를 가진 부분이 nucleus구나”를 학습합니다.

## 11단계. label preview 저장하기

학습을 시작하기 전에 YOLO label이 원본 이미지와 잘 맞는지 먼저 눈으로 확인합니다. label이 잘못 만들어졌다면 모델은 잘못된 위치를 배우게 됩니다.

```python
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
```

초록색 사각형이 nucleus를 잘 감싸고 있으면 label 변환이 제대로 된 것입니다. 이 확인을 거친 뒤에 학습으로 넘어갑니다.

## 12단계. dataset YAML 파일 만들기

Ultralytics YOLO는 학습할 데이터셋 정보를 YAML 파일에서 읽습니다. 이미지와 label 파일을 만들어 두었더라도, YOLO에게 train 이미지가 어디 있고 validation 이미지가 어디 있는지 알려줘야 합니다. 이번 프로젝트에서는 그 설정 파일을 `nuclei.yaml`이라는 이름으로 저장합니다.

```python
DATASET_YAML_FILE = YOLO_DATASET_DIR / "nuclei.yaml"

dataset_yaml_text = f"""path: {YOLO_DATASET_DIR.as_posix()}
train: images/train
val: images/val
names:
  0: nucleus
"""

DATASET_YAML_FILE.write_text(dataset_yaml_text, encoding="utf-8")

print(DATASET_YAML_FILE.read_text(encoding="utf-8"))
```

이 YAML 파일은 YOLO에게 세 가지를 알려줍니다.

```text
데이터셋 루트 폴더가 어디인지
train 이미지가 어디 있는지
validation 이미지가 어디 있는지
class 이름이 무엇인지
```

즉, `nuclei.yaml`은 학습 데이터 자체가 아니라 데이터셋의 주소록에 가깝습니다. 이미지와 label 파일은 이미 만들어져 있고, YAML 파일은 YOLO에게 그 파일들이 어디에 있는지 알려줍니다.

## 13단계. 학습 파라미터 다시 확인하기

학습을 시작하기 전에 이번 프로젝트의 파라미터를 출력합니다. 앞에서 정한 값들이 실제로 어떤 설정으로 들어가는지 한 번 확인하고 넘어갑니다.

```python
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
```

이 값들이 바로 Ultralytics Train Docs에서 확인할 수 있는 주요 파라미터입니다.

처음에는 이 값으로 실행하고, 바꿔 보고 싶다면 한 번에 하나씩만 바꿉니다.

예를 들어 CPU에서 너무 느리면 이렇게 바꿔 봅니다.

```text
EPOCHS = 3
IMAGE_SIZE = 416
BATCH_SIZE = 2
TRAIN_IMAGE_COUNT = 20
DEVICE = "cpu"
```

Apple Silicon Mac에서 더 빠르게 실행해보고 싶다면 `DEVICE = "mps"`를 시도할 수 있습니다. 이 설정은 CPU보다 빠르게 학습을 진행할 수 있지만, 환경에 따라 `mps`를 지원하지 않는 경우도 있습니다. 그때는 성능보다 실습 완료를 우선해서 `DEVICE = "cpu"`로 돌아옵니다.

## 14단계. YOLO 모델 학습하기

데이터셋 구조와 YAML 파일, 학습 파라미터가 준비되었습니다. 이제 작은 YOLO 모델을 학습합니다.

```python
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
```

처음 실행하면 pretrained 모델 파일을 다운로드한 뒤 학습을 시작합니다. 이 과정은 컴퓨터 사양에 따라 시간이 걸립니다. 프로젝트의 목표는 최고 성능을 내는 것이 아니라, 생명과학 이미지 데이터를 object detection 학습 형식으로 바꾸고 실제 학습까지 이어 보는 것입니다.

학습 결과는 다음 폴더에 저장됩니다.

```text
outputs/runs/nuclei_yolo/
```

그 안의 `weights/best.pt`가 이번 실습에서 학습된 모델 파일입니다.

학습 코드 안의 `patience=3`은 성능이 더 좋아지지 않을 때 너무 오래 기다리지 않도록 하는 값이고, `seed=0`은 실행할 때마다 결과가 크게 흔들리지 않도록 난수의 출발점을 고정하는 값입니다. 둘 다 모델 성능의 정답이라기보다, 실습을 안정적으로 진행하기 위한 설정입니다.

작성자처럼 `EPOCHS = 50`으로 바꾸어 실행하더라도 항상 50 epoch를 모두 실행하는 것은 아닙니다. 이 코드에서는 `patience=3`을 함께 사용합니다. validation 성능이 3 epoch 동안 더 좋아지지 않으면 YOLO가 자동으로 학습을 멈추고, 가장 좋았던 모델을 `best.pt`로 저장합니다.

예를 들어 실제 실행에서 다음과 같은 메시지가 나올 수 있습니다.

```text
EarlyStopping: Training stopped early as no improvement observed in last 3 epochs.
Best results observed at epoch 12, best model saved as best.pt.
```

이것은 에러가 아닙니다. 최대 50 epoch까지 갈 수 있지만, 12 epoch에서 가장 좋은 결과가 나왔고 그 뒤로 3 epoch 동안 더 좋아지지 않아 15 epoch에서 멈춘 것입니다. 불필요하게 오래 돌리지 않고 가장 좋은 모델을 남긴 정상적인 종료입니다.

학습 로그를 보면 어떤 epoch에서는 `mAP50`이 더 높아 보일 수도 있습니다. 하지만 YOLO가 `best.pt`를 고를 때는 `mAP50` 하나만 보지 않고 더 엄격한 지표까지 함께 반영합니다. 그래서 최종적으로는 학습이 끝난 뒤 다시 출력되는 `Validating ... best.pt` 아래의 숫자를 이번 모델의 결과로 보면 됩니다.

학습 중에는 여러 숫자가 출력됩니다. 처음에는 전부 이해하려고 하기보다, 아래 정도만 보면 충분합니다.

| 출력값 | 의미 |
| --- | --- |
| `box_loss`, `cls_loss`, `dfl_loss` | 모델이 아직 얼마나 틀리고 있는지 나타내는 값입니다. 보통 낮아지는 방향이면 학습이 진행되고 있다고 볼 수 있습니다. |
| `Box(P)` | 모델이 nucleus라고 예측한 것 중 실제 nucleus와 맞는 비율에 가깝습니다. |
| `R` | 실제 nucleus 중 모델이 찾아낸 비율에 가깝습니다. |
| `mAP50` | detection이 전체적으로 얼마나 잘 맞는지 보는 대표 지표입니다. 숫자가 클수록 좋습니다. |
| `mAP50-95` | `mAP50`보다 더 엄격한 기준으로 본 지표입니다. |

아래 숫자는 작성자가 `EPOCHS = 50`, `IMAGE_SIZE = 640`, `DEVICE = "mps"`로 실행했을 때의 예시입니다. 기본값이나 다른 컴퓨터 환경에서는 숫자가 달라질 수 있습니다.

실제 검증 실행에서는 validation 이미지 10장, nucleus 1070개 기준으로 다음과 비슷한 결과가 나왔습니다.

```text
Box(P)    0.714
R         0.673
mAP50     0.717
mAP50-95  0.561
```

이 결과는 모델이 nucleus를 완벽하게 찾은 것은 아니지만, 실제로 학습이 진행되었고 validation 이미지에서도 꽤 많은 nucleus를 찾아낸 상태로 볼 수 있습니다. 이 프로젝트는 연구용 모델을 완성하는 과정이 아니라, YOLO용 데이터셋을 만들고 학습과 예측까지 이어 보는 실습이므로 이 정도면 목표에 충분히 맞는 결과입니다.

Windows에서 학습 중 multiprocessing 관련 에러가 난다면 Ultralytics Train Docs의 Windows 안내처럼 학습 코드를 `if __name__ == "__main__":` 아래에 두어야 할 수 있습니다. 이 문서의 기본값은 `workers=0`이라 그런 문제를 줄이는 쪽으로 잡았습니다.

## 15단계. validation 이미지에서 예측하기

학습이 끝났다면, train에 쓰지 않은 validation 이미지에서 예측을 실행합니다. 이렇게 하면 모델이 학습에 직접 사용하지 않은 이미지에서도 nucleus를 어느 정도 찾는지 볼 수 있습니다.

```python
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
```

여기서는 모델을 다시 학습하는 것이 아니라, 앞에서 저장된 `best.pt` 모델을 불러와 validation 이미지에 적용합니다. 출력에 `85 nucleuss`처럼 보이는 줄은 해당 이미지에서 YOLO가 nucleus box를 85개 예측했다는 뜻입니다. Ultralytics가 class 이름 뒤에 자동으로 `s`를 붙여 출력하다 보니 `nucleuss`처럼 어색하게 보일 수 있지만, 실행 오류는 아닙니다.

예측 이미지는 `outputs/predictions/val_examples/` 폴더에 저장됩니다. 이미지 위에 파란 bounding box와 confidence score가 그려져 있으면 모델이 실제로 어디를 nucleus로 봤는지 눈으로 확인할 수 있습니다.

`conf`는 confidence threshold입니다. 모델이 어느 정도 이상 확신하는 detection만 남길지 정하는 값입니다.

예측 결과가 너무 많이 나오면 `CONFIDENCE`를 높여 봅니다.

```text
CONFIDENCE = 0.40
```

예측 결과가 너무 적게 나오면 낮춰 봅니다.

```text
CONFIDENCE = 0.15
```

## 16단계. 실제 nucleus 수와 예측 nucleus 수 비교하기

마지막으로 validation 이미지에서 실제 mask 기반 nucleus 수와 YOLO가 예측한 nucleus 수를 비교합니다. object detection에서는 비교 기준이 되는 label을 ground truth라고 부릅니다. 이미 YOLO label 파일을 만들 때 mask 기반 nucleus 수, 즉 ground truth count를 알고 있으므로 예측 결과의 box 개수와 나란히 놓을 수 있습니다.

```python
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
```

이 비교는 정밀한 모델 평가가 아닙니다. 다만 YOLO가 nucleus를 어느 정도 탐지하고 있는지 빠르게 감을 잡는 데 도움이 됩니다.

실제 검증 실행에서는 validation 이미지 10장에 대해 다음과 같은 결과가 나왔습니다.

```text
ground truth count 합계: 1070
YOLO predicted count 합계: 940
difference 합계: -130
```

`difference`는 `predicted_count - ground_truth_count`입니다. 음수라면 YOLO가 실제 mask 기준보다 적게 찾았다는 뜻이고, 양수라면 더 많이 찾았다는 뜻입니다. 위 결과에서는 전체적으로 nucleus를 조금 덜 잡는 경향이 있지만, validation 이미지마다 예측 개수가 ground truth count와 같은 방향으로 움직이고 있음을 확인할 수 있습니다.

## 17단계. 개수 비교 그래프 저장하기

실제 nucleus 수와 예측 nucleus 수를 막대그래프로 비교합니다.

```python
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
```

처음 학습한 모델은 완벽하지 않을 수 있습니다. 이 프로젝트의 목표는 좋은 성능을 달성하는 것이 아니라, 데이터 준비부터 학습과 예측까지 전체 흐름을 직접 경험하는 것입니다.

## 파라미터를 바꿔볼 때의 기준

학습이 끝까지 돌아간 뒤에만 파라미터를 바꿔 봅니다. 처음부터 여러 값을 바꾸면 문제가 생겼을 때 원인을 찾기 어렵습니다.

가장 먼저 조절할 만한 값은 다음과 같습니다.

| 상황 | 먼저 바꿀 값 | 예시 |
| --- | --- | --- |
| 학습이 너무 오래 걸림 | `EPOCHS` | `5`에서 `3`으로 줄임 |
| 학습이 너무 오래 걸림 | `IMAGE_SIZE` | `512`에서 `416`으로 줄임 |
| 메모리 부족 에러 | `BATCH_SIZE` | `4`에서 `2` 또는 `1`로 줄임 |
| GPU를 쓰고 싶음 | `DEVICE` | NVIDIA GPU는 `0`, Apple Silicon은 `"mps"` |
| 탐지가 너무 많음 | `CONFIDENCE` | `0.25`에서 `0.40`으로 높임 |
| 탐지가 너무 적음 | `CONFIDENCE` | `0.25`에서 `0.15`로 낮춤 |
| 성능을 더 보고 싶음 | `EPOCHS` | `5`에서 `10` 또는 `50`으로 늘림 |
| 데이터가 더 필요해 보임 | `TRAIN_IMAGE_COUNT` | `40`에서 `80`으로 늘림 |
| validation 비교를 더 보고 싶음 | `VAL_IMAGE_COUNT` | `10`에서 `20`으로 늘림 |

파라미터를 바꾸기 전에는 먼저 공식 문서에서 해당 이름을 찾아봅니다.

예를 들어 `batch`를 바꾸고 싶다면 Ultralytics Train Docs에서 `batch`를 검색합니다. 문서에서 기본값과 의미를 확인한 뒤, 내 컴퓨터 사양에 맞게 값을 조절합니다.

## 최종적으로 만들어지는 파일

끝까지 실행하면 `outputs/`와 `data/yolo_dataset/`에 다음 파일들이 생깁니다.

```text
projects/05_yolo_nuclei_detection/
├── data/
│   └── yolo_dataset/
│       ├── images/
│       │   ├── train/
│       │   └── val/
│       ├── labels/
│       │   ├── train/
│       │   └── val/
│       └── nuclei.yaml
└── outputs/
    ├── dataset_preview.png
    ├── count_comparison.csv
    ├── count_comparison.png
    ├── predictions/
    │   └── val_examples/
    └── runs/
        └── nuclei_yolo/
```

| 파일 또는 폴더 | 의미 |
| --- | --- |
| `data/yolo_dataset/images/` | YOLO 학습용 PNG 이미지 |
| `data/yolo_dataset/labels/` | YOLO 학습용 bounding box label |
| `data/yolo_dataset/nuclei.yaml` | YOLO dataset YAML 파일 |
| `dataset_preview.png` | label이 이미지에 잘 맞는지 확인하는 preview |
| `outputs/runs/nuclei_yolo/` | YOLO 학습 결과 |
| `outputs/predictions/val_examples/` | validation 이미지 예측 결과 |
| `count_comparison.csv` | 실제 nucleus 수와 예측 nucleus 수 비교표 |
| `count_comparison.png` | 실제 nucleus 수와 예측 nucleus 수 비교 그래프 |

## 자주 생기는 문제

### `ModuleNotFoundError: No module named 'ultralytics'`가 뜨는 경우

`ultralytics`가 설치되어 있지 않은 상태입니다. 1단계의 설치 명령을 실행한 뒤 다시 실행합니다.

### 학습이 너무 오래 걸리는 경우

처음에는 아래처럼 값을 줄입니다.

```text
TRAIN_IMAGE_COUNT = 20
VAL_IMAGE_COUNT = 5
EPOCHS = 3
IMAGE_SIZE = 416
BATCH_SIZE = 2
DEVICE = "cpu"
```

### 메모리 부족 에러가 나는 경우

`BATCH_SIZE`를 먼저 낮춥니다.

```text
BATCH_SIZE = 1
```

그래도 어렵다면 `IMAGE_SIZE`도 낮춥니다.

```text
IMAGE_SIZE = 416
```

### `1 backgrounds`처럼 출력되는 경우

YOLO가 label이 비어 있는 이미지를 background image로 인식한 것입니다. 이 데이터셋에는 실제로 nucleus가 없는 mask가 포함될 수 있으므로, `0 corrupt`와 함께 출력된다면 에러로 보지 않아도 됩니다.

### Apple Silicon Mac에서 에러가 나는 경우

Apple Silicon Mac에서 속도를 높이기 위해 아래 값을 시도할 수 있습니다.

```text
DEVICE = "mps"
```

만약 `mps` 관련 에러가 나면 CPU로 바꿔서 전체 흐름을 먼저 완료합니다.

```text
DEVICE = "cpu"
```

### NVIDIA GPU를 사용하고 싶은 경우

CUDA가 설정되어 있다면 아래처럼 바꿔 볼 수 있습니다.

```text
DEVICE = 0
BATCH_SIZE = 8
```

GPU가 제대로 잡히지 않으면 `DEVICE = "cpu"`로 돌아와 먼저 전체 흐름을 완료합니다.

### 예측 결과가 너무 많은 경우

confidence threshold를 높입니다.

```text
CONFIDENCE = 0.40
```

### 예측 결과가 너무 적은 경우

confidence threshold를 낮춥니다.

```text
CONFIDENCE = 0.15
```

## 이 프로젝트에서 해본 것

실제 현미경 이미지와 nucleus mask로 다음 흐름을 따라갔습니다.

```text
1. 이미지와 mask 다운로드하기
2. mask에서 nucleus bounding box 만들기
3. YOLO label 형식으로 저장하기
4. train/validation 데이터셋 구조 만들기
5. dataset YAML 파일 만들기
6. YOLO 학습 파라미터 의미 확인하기
7. 작은 YOLO 모델 학습하기
8. validation 이미지에서 nucleus 탐지하기
9. 실제 nucleus 수와 예측 nucleus 수 비교하기
10. 공식 문서에서 파라미터를 찾아 조절하는 법 익히기
```

프로젝트 4에서는 mask를 이용해 nucleus를 측정했습니다. 이번 프로젝트에서는 같은 mask에서 bounding box를 만들고, 그 bounding box를 이용해 YOLO object detection 모델을 학습했습니다.

이 프로젝트의 핵심은 좋은 모델을 완성하는 것이 아니라, 생명과학 이미지 데이터를 딥러닝 모델이 학습할 수 있는 형식으로 바꾸고, 학습과 예측까지 이어 보는 것입니다.
