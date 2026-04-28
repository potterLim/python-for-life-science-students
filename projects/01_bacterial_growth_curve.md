# 프로젝트 1. 세균 성장 곡선 분석하기

실제 공개 실험 데이터로 세균 community의 성장 곡선을 그려 봅니다.

전체 흐름은 다음과 같습니다.

1. CSV 파일을 Python으로 불러옵니다.
2. 시간과 OD600 열을 꺼내 그래프로 저장합니다.
3. control 조건과 화학물질 처리 조건의 성장 곡선을 비교합니다.
4. 성장 곡선을 AUC라는 숫자로 간단히 요약합니다.

이 프로젝트를 마치면 성장 곡선 이미지, AUC 비교 이미지, 요약 CSV 파일이 만들어집니다.

## 사용할 데이터셋

데이터셋: [Bacterial bioindicators growth curves](https://figshare.com/articles/dataset/Bacterial_bioindicators_growth_curves/28684982)

출처:

- 저장소: [Figshare](https://figshare.com)
- DOI: [10.6084/m9.figshare.28684982.v1](https://doi.org/10.6084/m9.figshare.28684982.v1)
- 라이선스: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)

이 데이터셋은 세균 isolate 또는 세균 community를 여러 화학물질 조건에서 배양하면서, 시간에 따라 OD600을 측정한 데이터입니다.

OD600은 600 nm 파장에서 측정한 optical density 값입니다. 세균이 많이 자랄수록 배양액이 더 탁해지고, 일반적으로 OD600 값이 증가합니다. 그래서 OD600을 시간에 따라 그리면 세균이 어떻게 자랐는지 곡선으로 볼 수 있습니다.

데이터셋에는 두 개의 주요 CSV 파일이 있습니다.

| 파일명 | 크기 | 설명 |
| --- | ---: | --- |
| `community-growth-curves.csv` | 약 32 MB | 세균 community 성장 곡선 데이터 |
| `isolate-growth-curves.csv` | 약 340 MB | 개별 세균 isolate 성장 곡선 데이터 |

여기서는 `community-growth-curves.csv`만 사용합니다. 파일 크기가 비교적 작아 처음 다루기에 부담이 덜하고, 성장 곡선을 그려보기에 충분한 정보를 담고 있습니다.

다운로드할 파일:

- 파일명: `community-growth-curves.csv`
- 직접 다운로드 링크: <https://ndownloader.figshare.com/files/53285993>
- 파일 크기: 약 32 MB

## 작업 파일 만들기

먼저 `projects/01_bacterial_growth_curve/` 폴더를 만들고, 그 안에 `analysis.py` 파일을 만듭니다.

이 문서의 코드는 위에서 아래로 `analysis.py`에 단계별로 직접 입력하고 실행해 보세요. 코드를 조금씩 추가하면서 실행하면, 어느 부분에서 어떤 파일이 생기고 어떤 값이 출력되는지 더 쉽게 따라갈 수 있습니다.

진행을 마치면 아래와 같은 구조가 됩니다.

```text
projects/
└── 01_bacterial_growth_curve/
    ├── analysis.py
    ├── data/
    │   └── raw/
    │       └── community-growth-curves.csv
    └── outputs/
        ├── first_5_measurements.png
        ├── raw_dmso_points.png
        ├── growth_curve_dmso_vs_hexachlorophene.png
        ├── growth_auc_comparison.png
        └── growth_summary.csv
```

`data/raw/`에는 다운로드한 원본 데이터를 저장합니다. `outputs/`에는 직접 만든 그래프와 요약 파일을 저장합니다.

## 1단계. 필요한 기능 불러오기

먼저 `analysis.py`에 아래 코드를 입력합니다.

```python
from pathlib import Path
from urllib.request import urlretrieve

import pandas as pd
import matplotlib.pyplot as plt
```

여기서는 네 가지를 불러옵니다.

- `Path`: 파일과 폴더 경로를 다루기 위해 사용합니다.
- `urlretrieve`: 인터넷 주소에서 데이터 파일을 다운로드할 때 사용합니다.
- `pandas`: CSV 파일처럼 행과 열로 이루어진 표 데이터를 다룰 때 사용합니다.
- `matplotlib`: 그래프를 그릴 때 사용합니다.

만약 `pandas` 또는 `matplotlib`이 없다는 에러가 나오면 아래 명령을 한 번 실행해 설치합니다.

```bash
python -m pip install pandas matplotlib
```

## 2단계. 폴더와 파일 경로 준비하기

데이터 파일과 출력 파일을 저장할 위치를 정합니다.

```python
PROJECT_DIR = Path(__file__).resolve().parent
DATA_DIR = PROJECT_DIR / "data" / "raw"
OUTPUT_DIR = PROJECT_DIR / "outputs"

DATA_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

print("데이터 폴더:", DATA_DIR)
print("출력 폴더:", OUTPUT_DIR)
```

`PROJECT_DIR`은 지금 작성 중인 `analysis.py` 파일이 있는 폴더를 뜻합니다. 그래서 터미널을 어느 위치에서 실행하더라도, 데이터와 출력 파일은 프로젝트 1 폴더 안에 정리됩니다.

`mkdir()`는 폴더를 만드는 기능입니다. 이미 폴더가 있더라도 에러가 나지 않도록 `exist_ok=True`를 사용했습니다.

## 3단계. 데이터 다운로드하기

Figshare에서 `community-growth-curves.csv` 파일을 다운로드합니다.

```python
DATA_URL = "https://ndownloader.figshare.com/files/53285993"
DATA_FILE = DATA_DIR / "community-growth-curves.csv"

if DATA_FILE.exists():
    print("이미 데이터 파일이 있습니다:", DATA_FILE)
else:
    print("데이터를 다운로드합니다...")
    urlretrieve(DATA_URL, DATA_FILE)
    print("다운로드 완료:", DATA_FILE)

file_size_mb = DATA_FILE.stat().st_size / (1024 * 1024)
print(f"파일 크기: {file_size_mb:.1f} MB")
```

한 번 다운로드한 뒤에는 같은 파일을 다시 받지 않습니다. 같은 코드를 다시 실행해도 불필요하게 다운로드가 반복되지 않습니다.

정상적으로 다운로드되었다면 파일 크기가 약 31 MB 정도로 표시됩니다.

## 4단계. CSV 파일 불러오기

CSV는 comma-separated values의 줄임말입니다. 이름 그대로 쉼표로 열을 구분한 표 형식의 파일입니다.

엑셀 파일처럼 행과 열이 있다고 생각하면 됩니다. 다만 CSV는 서식, 색깔, 여러 시트 같은 정보 없이 값만 저장하는 단순한 표 파일입니다.

`pandas`는 CSV 파일을 `DataFrame`이라는 형태로 읽어옵니다. `DataFrame`은 Python에서 표 데이터를 다루기 위한 자료구조입니다.

```python
df = pd.read_csv(DATA_FILE)

print("데이터 크기:", df.shape)
print(df.head())
```

`df`라는 변수 안에 CSV 파일 전체가 들어왔습니다.

`df.shape`는 행과 열의 개수를 알려줍니다. 예상 결과는 대략 다음과 같습니다.

```text
(225888, 18)
```

앞의 숫자 `225888`은 행의 개수이고, 뒤의 숫자 `18`은 열의 개수입니다. 즉, 이 데이터는 약 22만 개의 측정값과 18개의 열로 이루어져 있습니다.

처음 몇 줄을 확인할 때는 `head()`를 사용합니다. CSV를 처음 불러온 뒤에는 데이터 모양을 먼저 보는 습관을 들이면 좋습니다.

## 5단계. 열 이름과 주요 열 확인하기

열 이름만 따로 확인해 봅니다.

```python
print(df.columns.tolist())
```

앞으로 자주 사용할 열은 다음과 같습니다.

| 열 이름 | 의미 |
| --- | --- |
| `Time` | 측정 시간. 단위는 hour |
| `OD600` | 600 nm에서 측정한 optical density |
| `Community` | 세균 community 번호 |
| `Library` | 화학물질 library 구분 |
| `Rep` | 반복 실험 번호 |
| `LibRep` | library와 replicate를 합친 구분값 |
| `Well` | 96-well plate의 well 위치 |
| `Compound` | 처리한 화학물질 이름 |
| `Target` | 화학물질의 큰 분류 |
| `Specific.Target` | 화학물질의 더 구체적인 target 설명 |

## 6단계. CSV에서 열을 꺼내 그래프로 저장하기

그래프를 그리려면 결국 x축에 넣을 값과 y축에 넣을 값이 필요합니다.

이 데이터에서는 다음처럼 생각할 수 있습니다.

```text
x축: Time
y축: OD600
```

먼저 데이터의 앞 5개 값만 꺼내 작은 그래프로 저장해 봅니다.

```python
preview = df[["Time", "OD600"]].head(5)

time_list = preview["Time"].tolist()
od_list = preview["OD600"].tolist()

print("time_list:", time_list)
print("od_list:", od_list)

plt.figure(figsize=(5, 3))
plt.plot(time_list, od_list, marker="o")
plt.xlabel("Time (hours)")
plt.ylabel("OD600")
plt.title("First 5 measurements")
plt.tight_layout()

first_plot_path = OUTPUT_DIR / "first_5_measurements.png"
plt.savefig(first_plot_path, dpi=150)
plt.close()

print("저장된 파일:", first_plot_path)
```

대괄호를 두 번 쓴 이유는 여러 열을 한 번에 고르기 위해서입니다.

```text
df[["Time", "OD600"]]
```

이 코드는 `df`에서 `Time` 열과 `OD600` 열만 골라 새 표처럼 보여줍니다.

여기서 중요한 흐름은 CSV 파일을 `pandas`로 읽어 표처럼 다룰 수 있는 형태로 만들고, 그중 필요한 열만 고른 뒤, 열에 들어 있는 값을 그래프의 x축과 y축으로 사용하는 것입니다.

`plt.plot(x값, y값)`은 x축 값과 y축 값을 받아 그래프를 그립니다. `plt.savefig()`는 그래프를 이미지 파일로 저장합니다.

## 7단계. 데이터 전체를 가볍게 살펴보기

본격적인 분석 전에 데이터의 범위와 구조를 확인합니다.

```python
print("Time 범위:", df["Time"].min(), "~", df["Time"].max())
print("OD600 범위:", df["OD600"].min(), "~", df["OD600"].max())
print("Community 목록:", df["Community"].unique())
print(df["Compound"].value_counts().head(10))
```

이 데이터는 대략 0시간부터 72시간까지의 성장 곡선을 포함합니다.

`DMSO`가 많이 등장합니다. 이 데이터셋에서 DMSO는 화학물질을 녹이는 solvent 조건으로, 비교 기준 control로 사용할 수 있습니다.

## 8단계. 분석할 작은 데이터만 고르기

전체 데이터를 한 번에 다루려고 하면 처음에는 복잡합니다. 먼저 작은 부분만 골라서 같은 흐름을 따라가 봅니다.

여기서는 다음 조건만 사용합니다.

- `Community == 4`
- `Library == "PS1"`
- `Compound`는 `DMSO`와 `HEXACHLOROPHENE`만 사용

`DMSO`는 control 조건이고, `HEXACHLOROPHENE`은 DMSO와 비교할 treatment 조건으로 사용합니다.

```python
selected_community = 4
selected_library = "PS1"
selected_compounds = ["DMSO", "HEXACHLOROPHENE"]

subset = df[
    (df["Community"] == selected_community)
    & (df["Library"] == selected_library)
    & (df["Compound"].isin(selected_compounds))
].copy()

print("선택한 데이터 크기:", subset.shape)
print(subset[["Time", "OD600", "Community", "Library", "Rep", "Well", "Compound"]].head())
print(subset["Compound"].value_counts())
```

위 코드는 조건에 맞는 행만 골라 `subset`이라는 새 DataFrame을 만듭니다.

세 조건 사이의 `&`는 “그리고”라는 뜻입니다. 즉, 세 조건을 모두 만족하는 행만 남깁니다.

## 9단계. 한 조건의 원자료 성장 곡선 그리기

먼저 control인 `DMSO` 데이터만 골라서 시간에 따른 OD600을 점으로 그대로 그립니다.

여기서 원자료(raw data)는 평균을 내기 전의 측정값을 뜻합니다.

```python
dmso = subset[subset["Compound"] == "DMSO"]

dmso_time = dmso["Time"].tolist()
dmso_od = dmso["OD600"].tolist()

print("time 값 개수:", len(dmso_time))
print("OD600 값 개수:", len(dmso_od))

plt.figure(figsize=(8, 5))
plt.plot(dmso_time, dmso_od, ".", alpha=0.2)
plt.xlabel("Time (hours)")
plt.ylabel("OD600")
plt.title("Raw OD600 measurements: DMSO")
plt.tight_layout()

raw_plot_path = OUTPUT_DIR / "raw_dmso_points.png"
plt.savefig(raw_plot_path, dpi=150)
plt.close()

print("저장된 파일:", raw_plot_path)
```

x축에 들어갈 `dmso_time`과 y축에 들어갈 `dmso_od`의 길이가 같아야 합니다. 그래야 첫 번째 시간 값에는 첫 번째 OD600 값이, 두 번째 시간 값에는 두 번째 OD600 값이 짝지어져 그래프에 찍힙니다.

추가로 사용한 옵션의 의미는 다음과 같습니다.

- `.`: 선이 아니라 점으로 표시합니다.
- `alpha=0.2`: 점을 투명하게 표시합니다.
- `figsize=(8, 5)`: 그래프 크기를 지정합니다.
- `xlabel`, `ylabel`: x축과 y축 이름을 붙입니다.
- `title`: 그래프 제목을 붙입니다.

같은 시간대에 여러 well과 replicate가 있기 때문에 점이 많이 겹칩니다. 그래서 투명도를 낮추면 데이터가 겹쳐 있는 정도를 보기 쉽습니다.

## 10단계. 시간별 평균 성장 곡선 만들기

원자료를 그대로 그리면 점이 너무 많습니다. 그래서 같은 시간과 같은 compound에 해당하는 OD600 값을 평균 내서 더 보기 쉬운 성장 곡선을 만듭니다.

먼저 시간 값을 반올림합니다.

```python
subset["Time_rounded"] = subset["Time"].round()
print(subset[["Time", "Time_rounded"]].head())
```

실제 시간 값은 `1.00138888888889`처럼 아주 작은 오차를 포함합니다. 이런 값은 그래프에서는 사실상 1시간으로 보아도 충분합니다. 그래서 `round()`로 시간 값을 0, 1, 2, 3처럼 정리합니다.

이제 compound와 시간별로 평균 OD600을 계산합니다.

```python
mean_curve = (
    subset
    .groupby(["Compound", "Time_rounded"], as_index=False)
    ["OD600"]
    .mean()
)

print(mean_curve.head())
```

`groupby()`는 데이터를 그룹으로 묶는 기능입니다.

여기서는 `Compound`와 `Time_rounded`를 기준으로 데이터를 묶었습니다. 즉, 이런 단위로 데이터를 묶습니다.

```text
DMSO, 0시간
DMSO, 1시간
DMSO, 2시간
HEXACHLOROPHENE, 0시간
HEXACHLOROPHENE, 1시간
...
```

그다음 각 그룹 안에서 `OD600`의 평균을 계산합니다. 이렇게 하면 원자료의 많은 점을 시간별 평균 성장 곡선으로 정리할 수 있습니다.

## 11단계. Control과 treatment 성장 곡선 비교하기

이제 DMSO와 HEXACHLOROPHENE의 평균 성장 곡선을 같은 그래프에 그립니다.

```python
plt.figure(figsize=(8, 5))

for compound in selected_compounds:
    curve = mean_curve[mean_curve["Compound"] == compound]

    time_values = curve["Time_rounded"].tolist()
    mean_od_values = curve["OD600"].tolist()

    plt.plot(
        time_values,
        mean_od_values,
        marker="o",
        label=compound,
    )

plt.xlabel("Time (hours)")
plt.ylabel("Mean OD600")
plt.title("Bacterial community growth curve")
plt.legend()
plt.tight_layout()

growth_curve_path = OUTPUT_DIR / "growth_curve_dmso_vs_hexachlorophene.png"
plt.savefig(growth_curve_path, dpi=150)
plt.close()

print("저장된 파일:", growth_curve_path)
```

`for compound in selected_compounds:`는 DMSO와 HEXACHLOROPHENE을 하나씩 꺼내 같은 작업을 반복합니다.

반복문 안에서는 다음 일을 합니다.

1. 현재 compound에 해당하는 평균 곡선만 고릅니다.
2. `Time_rounded` 열을 리스트로 꺼냅니다.
3. `OD600` 열을 리스트로 꺼냅니다.
4. 두 리스트를 `plt.plot()`에 넣어 선 그래프를 그립니다.

`label=compound`는 각 선의 이름을 지정합니다. `plt.legend()`를 실행하면 그래프 안에 어떤 선이 어떤 조건인지 표시됩니다.

## 12단계. 최대 OD600과 마지막 OD600 계산하기

그래프는 직관적이지만, 숫자로도 요약해보면 좋습니다.

먼저 각 조건에서 가장 높은 평균 OD600 값을 계산합니다.

```python
max_od = (
    mean_curve
    .groupby("Compound", as_index=False)
    ["OD600"]
    .max()
    .rename(columns={"OD600": "max_mean_OD600"})
)

last_time = mean_curve["Time_rounded"].max()

final_od = (
    mean_curve[mean_curve["Time_rounded"] == last_time]
    [["Compound", "OD600"]]
    .rename(columns={"OD600": "final_mean_OD600"})
)

summary = max_od.merge(final_od, on="Compound")
print(summary)
```

`max_mean_OD600`은 각 조건에서 가장 높았던 평균 OD600 값입니다.

`final_mean_OD600`은 마지막 시간대의 평균 OD600 값입니다.

## 13단계. AUC 계산하기

성장 곡선을 숫자 하나로 요약하는 방법 중 하나가 AUC입니다. AUC는 area under the curve의 줄임말로, 곡선 아래 면적을 뜻합니다.

여기서는 AUC를 다음처럼 이해하면 충분합니다.

```text
AUC가 크다 -> 전체 시간 동안 OD600이 비교적 높았다
AUC가 작다 -> 전체 시간 동안 OD600이 비교적 낮았다
```

즉, AUC는 “전체 성장량을 거칠게 요약한 값”으로 사용할 수 있습니다.

```python
def calculate_auc(curve):
    curve = curve.sort_values("Time_rounded")
    time = curve["Time_rounded"].tolist()
    od = curve["OD600"].tolist()

    auc = 0
    for i in range(len(time) - 1):
        width = time[i + 1] - time[i]
        height = (od[i] + od[i + 1]) / 2
        auc += width * height

    return auc


auc_values = []

for compound, curve in mean_curve.groupby("Compound"):
    auc = calculate_auc(curve)
    auc_values.append({"Compound": compound, "AUC": auc})

auc_table = pd.DataFrame(auc_values)
summary = summary.merge(auc_table, on="Compound")

print(summary)
```

`calculate_auc()` 함수는 인접한 두 점 사이를 사다리꼴로 보고 면적을 더합니다.

반복문 안에서 하는 일은 다음과 같습니다.

1. 현재 시간과 다음 시간 사이의 간격을 구합니다.
2. 현재 OD600과 다음 OD600의 평균 높이를 구합니다.
3. `간격 * 평균 높이`를 면적으로 더합니다.

정확한 수학적 적분을 몰라도, “그래프 아래쪽 면적을 잘게 나누어 더한다”고 이해하면 됩니다.

## 14단계. 요약표와 AUC 그래프 저장하기

요약표를 CSV 파일로 저장합니다.

```python
summary_path = OUTPUT_DIR / "growth_summary.csv"
summary.to_csv(summary_path, index=False)

print("저장된 파일:", summary_path)
print(pd.read_csv(summary_path))
```

`to_csv()`는 DataFrame을 CSV 파일로 저장하는 함수입니다.

- `summary_path`: 저장할 파일 경로입니다.
- `index=False`: 행 번호를 CSV 파일에 따로 저장하지 않겠다는 뜻입니다.

이제 조건별 AUC를 막대그래프로 비교합니다.

```python
compound_names = summary["Compound"].tolist()
auc_values = summary["AUC"].tolist()

plt.figure(figsize=(6, 4))
plt.bar(compound_names, auc_values)
plt.ylabel("AUC")
plt.title("Growth curve AUC")
plt.xticks(rotation=20)
plt.tight_layout()

auc_plot_path = OUTPUT_DIR / "growth_auc_comparison.png"
plt.savefig(auc_plot_path, dpi=150)
plt.close()

print("저장된 파일:", auc_plot_path)
```

`plt.bar()`는 막대그래프를 그리는 함수입니다.

```text
plt.bar(x축_이름, y축_값)
```

위 코드에서는 다음 두 리스트를 사용했습니다.

```text
x축: compound_names
y축: auc_values
```

즉, CSV에서 시작한 데이터가 DataFrame으로 들어오고, 필요한 열이 리스트로 바뀐 뒤, 그 리스트가 그래프의 x축과 y축으로 사용되는 흐름을 다시 한 번 확인할 수 있습니다.

## 최종적으로 만들어지는 파일

끝까지 실행하면 `outputs/` 폴더에 다음 파일들이 생깁니다.

```text
projects/01_bacterial_growth_curve/outputs/
├── first_5_measurements.png
├── raw_dmso_points.png
├── growth_curve_dmso_vs_hexachlorophene.png
├── growth_auc_comparison.png
└── growth_summary.csv
```

| 파일명 | 의미 |
| --- | --- |
| `first_5_measurements.png` | CSV에서 꺼낸 앞 5개 측정값 그래프 |
| `raw_dmso_points.png` | DMSO 조건의 원자료 점 그래프 |
| `growth_curve_dmso_vs_hexachlorophene.png` | DMSO와 HEXACHLOROPHENE의 평균 성장 곡선 비교 |
| `growth_auc_comparison.png` | 두 조건의 AUC 막대그래프 |
| `growth_summary.csv` | 최대 OD600, 마지막 OD600, AUC 요약표 |

## 자주 생기는 문제

### `ModuleNotFoundError`가 뜨는 경우

`pandas` 또는 `matplotlib`이 설치되어 있지 않은 상태입니다. 1단계의 설치 명령을 실행한 뒤 다시 실행합니다.

```bash
python -m pip install pandas matplotlib
```

### `FileNotFoundError`가 뜨는 경우

데이터 파일 경로가 잘못되었을 가능성이 큽니다. `DATA_FILE`이 실제로 존재하는지 확인합니다.

```python
print(DATA_FILE.exists())
```

`False`가 나오면 다운로드 코드부터 다시 실행합니다.

### 그래프가 너무 복잡하게 보이는 경우

원자료에는 replicate와 well이 여러 개 들어 있습니다. 처음부터 모든 점을 보려고 하기보다, `groupby()`로 평균 곡선을 만든 뒤 비교합니다.

### `DMSO` 또는 `HEXACHLOROPHENE` 데이터가 비어 있는 경우

필터 조건을 다시 확인합니다.

```python
print(df["Compound"].unique())
```

또는 선택한 조건에서 compound 목록을 확인합니다.

```python
print(
    df[
        (df["Community"] == 4)
        & (df["Library"] == "PS1")
    ]["Compound"].unique()
)
```

## 이 프로젝트에서 해본 것

실제 생명과학 실험 데이터로 다음 흐름을 따라갔습니다.

1. 표 형태의 실험 데이터 읽기
2. 시간과 OD600 열 확인하기
3. 비교할 조건만 골라내기
4. 필요한 열을 리스트로 꺼내 그래프에 사용하기
5. 조건별 시간 평균 성장 곡선 만들기
6. 성장 곡선을 그래프로 저장하기
7. 최대 OD600, 마지막 OD600, AUC로 간단히 요약하기
8. 요약표와 비교 그래프 저장하기

이 흐름은 다른 실험 데이터에도 비슷하게 적용할 수 있습니다. 예를 들어 세포 viability assay, 효소 활성 측정, 시간별 형광 intensity 측정 데이터도 표 형태로 정리되어 있다면 비슷한 방식으로 불러오고 시각화할 수 있습니다.
