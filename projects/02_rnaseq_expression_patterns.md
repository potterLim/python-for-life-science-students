# 프로젝트 2. RNA-seq 발현 데이터로 유전자 발현 패턴 보기

실제 공개 RNA-seq 데이터로 유전자 발현값을 sample 정보와 연결하고, 조건별 발현 패턴을 그래프로 확인합니다.

전체 흐름은 다음과 같습니다.

1. RNA-seq 발현값 표와 sample metadata를 함께 살펴봅니다.
2. sample 이름을 기준으로 발현값과 조건 정보를 연결합니다.
3. 비교하기 쉬운 형태로 데이터를 정리합니다.
4. marker gene의 발현 패턴을 그래프와 heatmap으로 확인합니다.

이 프로젝트를 마치면 sample별 발현 분포 이미지, marker gene 발현 패턴 이미지, heatmap 이미지, 요약 CSV 파일이 만들어집니다.

## 사용할 데이터셋

데이터셋: [GSE60450](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE60450)

출처:

- 저장소: [NCBI Gene Expression Omnibus](https://www.ncbi.nlm.nih.gov/geo/)
- GEO accession: [GSE60450](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE60450)
- 실습용 CSV 파일: [Melbourne Bioinformatics data.zip](https://github.com/melbournebioinformatics/r-intro-biologists/raw/master/data.zip)

이 데이터셋은 마우스 mammary gland에서 luminal cell과 basal cell을 분리한 뒤, virgin, pregnant, lactating 단계에서 RNA-seq으로 유전자 발현을 측정한 데이터입니다.

GEO 설명에 따르면 전체 sample은 12개입니다. 조건은 cell type과 developmental stage의 조합으로 나뉘고, 각 조건에는 2개의 replicate가 있습니다.

| 구분 | 값 |
| --- | --- |
| organism | `Mus musculus` |
| experiment type | RNA-seq |
| cell type | luminal cell, basal cell |
| developmental stage | virgin, 18.5 day pregnancy, 2 day lactation |
| sample 수 | 12 |

실습에서는 원본 데이터를 바로 내려받아 복잡하게 전처리하지 않고, CSV 형태로 정리되어 있는 파일을 사용합니다.

| 파일명 | 설명 |
| --- | --- |
| `GSE60450_GeneLevel_Normalized(CPM.and.TMM)_data.csv` | gene별 normalized count |
| `GSE60450_filtered_metadata.csv` | sample별 cell type과 stage 정보 |

여기서 사용하는 발현값은 raw count가 아니라 normalized count입니다. 즉, sample마다 sequencing depth가 다르다는 문제를 어느 정도 보정한 값입니다. 그래서 이 프로젝트에서는 normalization 자체를 새로 계산하지 않고, 이미 정리된 값을 이용해 데이터 모양을 바꾸고 그래프로 보는 데 집중합니다.

## 작업 파일 만들기

먼저 `projects/02_rnaseq_expression_patterns/` 폴더를 만들고, 그 안에 `analysis.py` 파일을 만듭니다.

이 프로젝트는 프로젝트 1을 마친 뒤 진행한다고 가정합니다. CSV 파일을 불러오고, 그래프를 저장하고, 폴더를 만드는 흐름은 길게 반복해서 설명하지 않습니다. 대신 이번에 새로 나오는 `metadata`, `wide format`, `long format`, `merge`, `log2`, `heatmap`을 중심으로 봅니다.

진행을 마치면 아래와 같은 구조가 됩니다.

```text
projects/
└── 02_rnaseq_expression_patterns/
    ├── analysis.py
    ├── data/
    │   └── raw/
    │       ├── r-intro-biologists-data.zip
    │       ├── GSE60450_GeneLevel_Normalized(CPM.and.TMM)_data.csv
    │       └── GSE60450_filtered_metadata.csv
    └── outputs/
        ├── sample_expression_distribution.png
        ├── selected_gene_expression.png
        ├── marker_gene_heatmap.png
        └── marker_gene_summary.csv
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
```

프로젝트 1에서 사용했던 `Path`, `urlretrieve`, `pandas`, `matplotlib`을 다시 사용합니다.

이번에 새로 사용하는 것은 두 가지입니다.

- `ZipFile`: 다운로드한 ZIP 파일 안에서 필요한 CSV 파일을 꺼낼 때 사용합니다.
- `numpy`: `log2()` 계산을 할 때 사용합니다.

프로젝트 1에서 `pandas`와 `matplotlib`을 이미 설치했다면 대부분 바로 실행할 수 있습니다. 만약 모듈이 없다는 에러가 나오면 아래 명령을 한 번 실행합니다.

```bash
python -m pip install numpy pandas matplotlib
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

프로젝트 1과 같은 방식입니다. `analysis.py`가 있는 폴더를 기준으로 `data/raw/`와 `outputs/`가 만들어집니다.

## 3단계. 데이터 다운로드하고 압축 풀기

실습용 ZIP 파일을 다운로드한 뒤, 그 안에서 필요한 CSV 파일 두 개만 꺼냅니다.

```python
DATA_ZIP_URL = "https://github.com/melbournebioinformatics/r-intro-biologists/raw/master/data.zip"
DATA_ZIP_FILE = DATA_DIR / "r-intro-biologists-data.zip"

COUNTS_FILE = DATA_DIR / "GSE60450_GeneLevel_Normalized(CPM.and.TMM)_data.csv"
METADATA_FILE = DATA_DIR / "GSE60450_filtered_metadata.csv"

if DATA_ZIP_FILE.exists():
    print("이미 ZIP 파일이 있습니다:", DATA_ZIP_FILE)
else:
    print("ZIP 파일을 다운로드합니다...")
    urlretrieve(DATA_ZIP_URL, DATA_ZIP_FILE)
    print("다운로드 완료:", DATA_ZIP_FILE)

files_to_extract = {
    "data/GSE60450_GeneLevel_Normalized(CPM.and.TMM)_data.csv": COUNTS_FILE,
    "data/GSE60450_filtered_metadata.csv": METADATA_FILE,
}

with ZipFile(DATA_ZIP_FILE) as zip_file:
    for zip_path, output_path in files_to_extract.items():
        if output_path.exists():
            print("이미 CSV 파일이 있습니다:", output_path.name)
        else:
            with zip_file.open(zip_path) as source:
                output_path.write_bytes(source.read())
            print("압축 해제 완료:", output_path.name)

print("발현값 파일:", COUNTS_FILE)
print("metadata 파일:", METADATA_FILE)
```

ZIP 파일은 여러 파일을 하나로 묶어 둔 압축 파일입니다. 여기서는 ZIP 안에 있는 두 CSV 파일만 `data/raw/` 폴더로 꺼냅니다.

`files_to_extract`는 “ZIP 안에서의 파일 이름”과 “내 컴퓨터에 저장할 파일 위치”를 짝지어 둔 딕셔너리입니다.

이렇게 적어두면 ZIP 안에 여러 파일이 있어도, 필요한 파일만 골라 원하는 위치에 저장할 수 있습니다.

## 4단계. 발현값 데이터와 metadata 불러오기

압축을 풀었으니 두 CSV 파일을 각각 불러옵니다. 처음부터 두 표를 합치지 않고, 먼저 각 파일의 크기와 앞부분을 확인합니다.

```python
counts = pd.read_csv(COUNTS_FILE)
metadata = pd.read_csv(METADATA_FILE)

print("발현값 데이터 크기:", counts.shape)
print("metadata 크기:", metadata.shape)

print(counts.head())
print(metadata.head())
```

출력된 앞부분을 보면 `counts`와 `metadata`가 서로 다른 역할을 한다는 것을 알 수 있습니다.

`counts`에는 gene별 발현값이 들어 있습니다. 각 행은 gene 하나이고, 각 sample의 발현값은 여러 열에 나뉘어 들어 있습니다.

`metadata`에는 sample 설명이 들어 있습니다. 측정값 자체가 아니라, 각 sample이 어떤 cell type이고 어떤 developmental stage인지 알려주는 표입니다.

생명과학 데이터에서는 이런 식으로 “실험값 표”와 “sample 설명 표”가 따로 있는 경우가 많습니다.

```text
발현값 데이터: gene별 count 값
metadata: sample이 어떤 조건인지 설명하는 정보
```

## 5단계. 열 이름 정리하기

앞에서 `head()`를 출력해 보면 첫 번째 열 이름이 `Unnamed: 0`으로 들어와 있습니다. CSV에 저장될 때 행 이름처럼 쓰이던 값이 다시 열로 들어온 경우입니다. 이후 코드에서 의미가 잘 보이도록 이름을 바꿉니다.

```python
counts = counts.rename(columns={"Unnamed: 0": "gene_id"})
metadata = metadata.rename(
    columns={
        "Unnamed: 0": "Sample",
        "developmental stage": "stage",
    }
)

print(counts.columns.tolist())
print(metadata.columns.tolist())
```

`counts`의 첫 번째 열은 gene ID입니다. 그래서 `gene_id`로 바꿉니다.

`metadata`의 첫 번째 열은 sample ID입니다. `GSM1480291` 같은 이름이 들어 있으므로 `Sample`로 바꿉니다.

`developmental stage`처럼 열 이름에 공백이 들어 있으면 매번 입력하기 조금 불편합니다. 그래서 짧게 `stage`로 바꿉니다.

## 6단계. sample 열과 metadata 확인하기

발현값 표에는 gene 정보 열과 sample 발현값 열이 함께 들어 있습니다. 이제 sample에 해당하는 열만 따로 찾습니다.

```python
sample_columns = [column for column in counts.columns if column.startswith("GSM")]

print("sample 수:", len(sample_columns))
print(sample_columns)
```

출력된 열 이름을 보면 `GSM`으로 시작하는 열들이 있습니다. `GSM1480291` 같은 이름은 GEO에서 sample을 구분할 때 사용하는 accession입니다. 이 열들이 실제 sample별 발현값입니다.

이제 metadata를 조금 더 보기 쉽게 정리합니다.

```python
metadata["cell_type"] = (
    metadata["immunophenotype"]
    .str.replace(" cell population", "", regex=False)
)

metadata["stage"] = metadata["stage"].replace(
    {
        "18.5 day pregnancy": "pregnant",
        "2 day lactation": "lactating",
    }
)

metadata["group"] = metadata["cell_type"] + " / " + metadata["stage"]

print(metadata[["Sample", "cell_type", "stage", "group"]])
```

`immunophenotype` 열에는 `luminal cell population`, `basal cell population` 같은 값이 들어 있습니다. 여기서는 그래프에 쓰기 좋게 `luminal`, `basal`만 남깁니다.

`group`은 cell type과 stage를 합친 새 열입니다.

```text
luminal / virgin
luminal / pregnant
luminal / lactating
basal / virgin
basal / pregnant
basal / lactating
```

나중에 조건별로 발현값을 비교할 때는 `cell_type`과 `stage`를 따로 보는 것보다, 두 정보를 합친 `group` 열을 쓰는 편이 편합니다.

## 7단계. wide format을 long format으로 바꾸기

지금 `counts` 데이터는 gene 하나가 한 행이고, sample들이 여러 열로 펼쳐져 있습니다. 이런 형태를 wide format이라고 합니다.

wide format은 sample마다 열이 따로 있는 형태입니다.

```text
gene_symbol | GSM1480291 | GSM1480292 | GSM1480293 | ...
Gnai3       | 243.28596  | 255.66037  | 239.73819  | ...
Cdc45       | 11.18453   | 13.78314   | 11.60091   | ...
```

사람이 표를 넓게 훑어볼 때는 wide format이 편할 수 있습니다. 하지만 “이 gene이 각 조건에서 얼마나 발현되는가”를 그리려면 sample 이름이 하나의 열로 들어가 있어야 조건 정보와 연결하기 쉽습니다.

long format은 “한 행에 하나의 측정값”이 들어가는 형태입니다.

```text
gene_symbol | Sample     | Count
Gnai3       | GSM1480291 | 243.28596
Gnai3       | GSM1480292 | 255.66037
Cdc45       | GSM1480291 | 11.18453
Cdc45       | GSM1480292 | 13.78314
```

`pandas`에서는 `melt()`로 wide format을 long format으로 바꿀 수 있습니다.

```python
long_counts = counts.melt(
    id_vars=["gene_id", "gene_symbol"],
    value_vars=sample_columns,
    var_name="Sample",
    value_name="Count",
)

print("long format 데이터 크기:", long_counts.shape)
print(long_counts.head())
```

`melt()`에서 중요한 부분은 세 가지입니다.

- `id_vars`: 그대로 유지할 열입니다. 여기서는 gene ID와 gene symbol을 유지합니다.
- `var_name`: 원래 열 이름이 들어갈 새 열 이름입니다. 여기서는 sample 이름이 들어가므로 `Sample`로 정합니다.
- `value_name`: 실제 값이 들어갈 새 열 이름입니다. 여기서는 발현값이 들어가므로 `Count`로 정합니다.

이제 각 행은 “어떤 gene이 어떤 sample에서 얼마만큼 발현되었는지”를 나타냅니다. 아직 조건 정보는 붙어 있지 않고, sample 이름만 들어 있습니다.

## 8단계. 발현값 데이터와 metadata 합치기

`long_counts`에는 발현값이 있고, `metadata`에는 sample 설명이 있습니다. 발현값만 있으면 조건을 알 수 없고, metadata만 있으면 gene별 발현값을 알 수 없습니다.

두 표는 `Sample` 열을 공통으로 가지고 있습니다.

이 공통 열을 기준으로 두 표를 합칩니다.

```python
expression = long_counts.merge(
    metadata[["Sample", "cell_type", "stage", "group"]],
    on="Sample",
    how="left",
)

print("합친 데이터 크기:", expression.shape)
print(expression.head())
```

`merge()`는 두 표를 연결하는 기능입니다.

여기서는 `on="Sample"`이라고 했습니다. 즉, 같은 sample 이름을 가진 행끼리 연결합니다.

```text
발현값 표의 Sample
metadata 표의 Sample
```

두 열의 값이 같으면, 그 sample의 cell type과 stage 정보를 발현값 옆에 붙입니다.

metadata가 제대로 붙었는지도 확인합니다.

```python
missing_metadata_count = expression["group"].isna().sum()
print("metadata가 붙지 않은 행 수:", missing_metadata_count)
```

정상이라면 `0`이 나옵니다. 만약 0보다 큰 값이 나온다면 sample 이름이 서로 맞지 않는다는 뜻입니다.

## 9단계. log2 발현값 만들기

RNA-seq 발현값은 작은 값부터 매우 큰 값까지 범위가 넓습니다. 그대로 그래프를 그리면 큰 값 몇 개 때문에 나머지 값이 잘 보이지 않을 수 있습니다.

먼저 실제 발현값 범위가 어느 정도인지 확인합니다.

```python
print(expression["Count"].describe(percentiles=[0.5, 0.9, 0.99]))
```

이런 표에서는 최솟값, 중앙값, 큰 값 쪽의 범위를 함께 볼 수 있습니다. 값의 범위가 넓게 벌어져 있으면 그래프에서 작은 차이가 잘 보이지 않을 수 있습니다.

그래서 발현값을 `log2(count + 1)`로 바꿔 봅니다.

```python
expression["log2_count"] = np.log2(expression["Count"] + 1)

print(expression[["gene_symbol", "Sample", "Count", "log2_count"]].head())
```

`log2()`는 큰 숫자의 차이를 조금 눌러서 보기 쉽게 만듭니다.

`+ 1`을 하는 이유는 count가 0일 수 있기 때문입니다. `log2(0)`은 계산할 수 없지만, `log2(0 + 1)`은 0이 됩니다.

```text
count가 0이면 log2(0 + 1) = 0
count가 1이면 log2(1 + 1) = 1
count가 1023이면 log2(1023 + 1) = 10
```

## 10단계. sample별 전체 발현 분포 그리기

먼저 sample마다 전체 gene 발현값 분포가 어떻게 생겼는지 boxplot으로 봅니다.

```python
sample_order = metadata["Sample"].tolist()

boxplot_values = []
for sample in sample_order:
    sample_values = expression.loc[
        expression["Sample"] == sample,
        "log2_count",
    ]
    boxplot_values.append(sample_values)

plt.figure(figsize=(10, 5))
plt.boxplot(boxplot_values, showfliers=False)
plt.xlabel("Sample")
plt.ylabel("log2(count + 1)")
plt.title("Expression distribution by sample")
plt.xticks(
    range(1, len(sample_order) + 1),
    sample_order,
    rotation=90,
)
plt.tight_layout()

distribution_plot_path = OUTPUT_DIR / "sample_expression_distribution.png"
plt.savefig(distribution_plot_path, dpi=150)
plt.close()

print("저장된 파일:", distribution_plot_path)
```

boxplot은 값의 분포를 요약해서 보여주는 그래프입니다. sample마다 수만 개 gene의 발현값이 있으므로, 모든 점을 그대로 그리기보다 분포를 요약해서 보는 것이 편합니다.

`showfliers=False`는 아주 멀리 떨어진 값을 그래프에서 숨기는 옵션입니다. 값을 삭제하는 것은 아니고, 그림에서만 숨깁니다. 이렇게 하면 sample별 전체적인 분포가 더 잘 보입니다.

## 11단계. marker gene 고르기

전체 gene을 한 번에 그래프로 그리면 너무 많아서 처음에는 읽기 어렵습니다. 그래서 먼저 발현 패턴을 살펴보기 좋은 gene 몇 개를 작은 목록으로 고릅니다.

여기서는 새로운 marker를 찾아내는 분석까지 진행하지 않고, mammary gland와 epithelial cell 문맥에서 자주 언급되는 gene들을 예시로 사용합니다. lactation과 관련된 gene, basal cell 쪽에서 자주 쓰이는 keratin gene, luminal cell과 관련해 자주 등장하는 gene을 함께 넣어 조건별 발현 패턴을 그려 봅니다.

즉, 아래 목록은 이 데이터에서 새로 찾아낸 marker 목록이 아니라, 발현값을 조건별로 꺼내고 그리는 과정을 연습하기 위한 출발점입니다.

```python
marker_genes = [
    "Csn2",
    "Csn1s1",
    "Lalba",
    "Krt14",
    "Krt5",
    "Krt8",
    "Krt18",
    "Esr1",
    "Pgr",
]

markers = expression[expression["gene_symbol"].isin(marker_genes)].copy()

print("선택한 marker gene 데이터 크기:", markers.shape)
print(markers["gene_symbol"].value_counts())
```

`isin()`은 열의 값이 어떤 목록 안에 들어 있는지 확인할 때 사용합니다.

```text
gene_symbol이 marker_genes 목록 안에 있는 행만 고르기
```

출력에서 gene마다 행 수가 12로 나오면, 선택한 gene이 12개 sample 모두에서 확인되었다는 뜻입니다.

## 12단계. 조건 순서 정하기

그래프와 heatmap에서 조건이 뒤섞여 보이지 않도록 순서를 정합니다. 앞에서 만든 `group` 값은 문자열이기 때문에, 아무 설정을 하지 않으면 알파벳순으로 정렬될 수 있습니다.

```python
group_order = [
    "luminal / virgin",
    "luminal / pregnant",
    "luminal / lactating",
    "basal / virgin",
    "basal / pregnant",
    "basal / lactating",
]

gene_order = marker_genes

markers["group"] = pd.Categorical(
    markers["group"],
    categories=group_order,
    ordered=True,
)

markers["gene_symbol"] = pd.Categorical(
    markers["gene_symbol"],
    categories=gene_order,
    ordered=True,
)
```

`Categorical`은 값의 순서를 정해둘 때 사용합니다.

문자열은 기본적으로 가나다순이나 알파벳순으로 정렬될 수 있습니다. 하지만 생명과학 데이터에서는 원하는 순서가 따로 있는 경우가 많습니다.

여기서는 luminal 조건 3개를 먼저 보고, 그다음 basal 조건 3개를 보도록 순서를 정했습니다. 같은 cell type 안에서는 virgin, pregnant, lactating 순서로 배치합니다.

## 13단계. marker gene 발현 패턴 그리기

선택한 gene들의 조건별 발현값을 한 그림에 모아 봅니다.

```python
fig, axes = plt.subplots(3, 3, figsize=(13, 9), sharey=False)
axes = axes.ravel()

group_colors = {
    "luminal / virgin": "#4C78A8",
    "luminal / pregnant": "#4C78A8",
    "luminal / lactating": "#4C78A8",
    "basal / virgin": "#F58518",
    "basal / pregnant": "#F58518",
    "basal / lactating": "#F58518",
}

for ax, gene in zip(axes, gene_order):
    gene_data = markers[markers["gene_symbol"] == gene]

    for group_index, group in enumerate(group_order):
        values = gene_data.loc[
            gene_data["group"] == group,
            "log2_count",
        ].tolist()

        ax.scatter(
            [group_index] * len(values),
            values,
            color=group_colors[group],
            s=35,
            alpha=0.8,
        )

    ax.set_title(gene)
    ax.set_xticks(range(len(group_order)))
    ax.set_xticklabels(group_order, rotation=70, ha="right", fontsize=7)
    ax.set_ylabel("log2(count + 1)")

plt.tight_layout()

gene_plot_path = OUTPUT_DIR / "selected_gene_expression.png"
plt.savefig(gene_plot_path, dpi=150)
plt.close()

print("저장된 파일:", gene_plot_path)
```

`plt.subplots(3, 3)`은 3행 3열로 작은 그래프들을 한 번에 만듭니다. marker gene이 9개이므로 gene마다 작은 그래프 하나씩 배치합니다.

각 점은 하나의 sample에서 측정된 발현값입니다. 이 데이터에서는 조건마다 replicate가 2개 있으므로, 각 조건에 점이 2개씩 찍힙니다.

`group_colors`는 luminal과 basal을 색으로 구분하기 위해 만든 딕셔너리입니다.

## 14단계. 조건별 평균 발현값 계산하기

앞의 scatter plot은 sample 하나하나의 값을 보여줍니다. 이제 같은 조건에 속한 replicate를 묶어 조건별 평균값을 계산합니다.

```python
summary = (
    markers
    .groupby(["gene_symbol", "cell_type", "stage", "group"], observed=True)
    .agg(
        mean_count=("Count", "mean"),
        mean_log2_count=("log2_count", "mean"),
        sample_count=("Sample", "nunique"),
    )
    .reset_index()
)

summary = summary.sort_values(["gene_symbol", "group"])

print(summary.head(12))
```

`agg()`는 여러 요약값을 한 번에 계산할 때 사용합니다.

여기서는 조건별로 세 가지 값을 계산했습니다.

| 열 이름 | 의미 |
| --- | --- |
| `mean_count` | 조건별 평균 normalized count |
| `mean_log2_count` | 조건별 평균 log2 발현값 |
| `sample_count` | 해당 조건에 들어간 sample 수 |

`sample_count`가 모두 2로 나오면, 조건마다 replicate 2개가 들어갔다는 뜻입니다.

## 15단계. 요약 CSV 저장하기

조건별 평균 발현값을 CSV 파일로 저장합니다.

```python
summary_path = OUTPUT_DIR / "marker_gene_summary.csv"
summary.to_csv(summary_path, index=False)

print("저장된 파일:", summary_path)
print(pd.read_csv(summary_path).head())
```

이 CSV 파일을 저장해 두면, 그래프를 다시 만들거나 다른 도구에서 이어서 다룰 수 있습니다.

## 16단계. heatmap 만들기

마지막으로 marker gene의 조건별 평균 발현값을 heatmap으로 그립니다. scatter plot은 gene마다 작은 그래프를 따로 보기에 좋고, heatmap은 여러 gene과 여러 조건을 한 화면에서 비교하기에 좋습니다.

heatmap은 숫자를 색으로 표현한 표입니다. 행은 gene, 열은 조건이고, 색을 통해 발현값의 크기를 구분할 수 있습니다.

먼저 heatmap에 넣을 표를 만듭니다.

```python
heatmap_table = summary.pivot(
    index="gene_symbol",
    columns="group",
    values="mean_log2_count",
)

heatmap_table = heatmap_table.loc[gene_order, group_order]

print(heatmap_table)
```

`pivot()`은 long format 데이터를 다시 표 형태로 펼칠 때 사용합니다.

여기서는 다음과 같은 모양을 만듭니다.

```text
행: gene_symbol
열: group
값: mean_log2_count
```

이제 이 표를 heatmap으로 저장합니다.

```python
plt.figure(figsize=(9, 5))
image = plt.imshow(heatmap_table, aspect="auto", cmap="viridis")

plt.xticks(
    range(len(group_order)),
    group_order,
    rotation=45,
    ha="right",
)
plt.yticks(range(len(gene_order)), gene_order)
plt.xlabel("Group")
plt.ylabel("Gene")
plt.title("Marker gene expression heatmap")

colorbar = plt.colorbar(image)
colorbar.set_label("Mean log2(count + 1)")

min_value = heatmap_table.to_numpy().min()
max_value = heatmap_table.to_numpy().max()
text_color_threshold = (min_value + max_value) / 2

for row_index, gene in enumerate(gene_order):
    for column_index, group in enumerate(group_order):
        value = heatmap_table.loc[gene, group]
        text_color = "white" if value > text_color_threshold else "black"
        plt.text(
            column_index,
            row_index,
            f"{value:.1f}",
            ha="center",
            va="center",
            color=text_color,
            fontsize=7,
        )

plt.tight_layout()

heatmap_path = OUTPUT_DIR / "marker_gene_heatmap.png"
plt.savefig(heatmap_path, dpi=150)
plt.close()

print("저장된 파일:", heatmap_path)
```

`imshow()`는 숫자로 이루어진 2차원 표를 색상 이미지처럼 보여주는 함수입니다.

`cmap="viridis"`는 사용할 색상표를 고르는 옵션입니다.

셀 안에 숫자를 같이 적어 두면 색뿐 아니라 실제 평균값도 함께 볼 수 있습니다.

## 최종적으로 만들어지는 파일

끝까지 실행하면 `outputs/` 폴더에 다음 파일들이 생깁니다.

```text
projects/02_rnaseq_expression_patterns/outputs/
├── sample_expression_distribution.png
├── selected_gene_expression.png
├── marker_gene_heatmap.png
└── marker_gene_summary.csv
```

| 파일명 | 의미 |
| --- | --- |
| `sample_expression_distribution.png` | sample별 전체 gene 발현값 분포 |
| `selected_gene_expression.png` | marker gene의 조건별 발현 패턴 |
| `marker_gene_heatmap.png` | 조건별 평균 발현값 heatmap |
| `marker_gene_summary.csv` | marker gene의 조건별 평균값 요약표 |

## 완성 참고 코드

완성된 참고 코드는 [프로젝트 2 완성 참고 코드](reference_code/02_rnaseq_expression_patterns.py)에서 확인할 수 있습니다. 먼저 문서를 따라 직접 입력해 보고, 실행이 잘 되지 않거나 전체 구조를 비교하고 싶을 때 참고하는 것을 권장합니다.

## 자주 생기는 문제

### `BadZipFile`이 뜨는 경우

ZIP 파일이 다운로드되는 도중에 끊겼을 가능성이 있습니다. `data/raw/r-intro-biologists-data.zip` 파일을 지운 뒤 다시 실행합니다.

### `KeyError: 'Sample'`이 뜨는 경우

열 이름을 바꾸는 단계를 건너뛰었을 가능성이 큽니다. 5단계의 `rename()` 코드가 실행되었는지 확인합니다.

### `metadata가 붙지 않은 행 수`가 0이 아닌 경우

발현값 데이터의 sample 이름과 metadata의 sample 이름이 서로 맞지 않는다는 뜻입니다. `sample_columns`와 `metadata["Sample"]` 값을 출력해서 비교합니다.

### 그래프의 x축 글자가 겹치는 경우

조건 이름이 길어서 생기는 문제입니다. `figsize`를 더 크게 하거나 `rotation` 값을 조정하면 됩니다.

## 이 프로젝트에서 해본 것

실제 RNA-seq 발현 데이터로 다음 흐름을 따라갔습니다.

```text
1. 발현값 데이터와 sample metadata 불러오기
2. sample 이름과 조건 정보 확인하기
3. wide format을 long format으로 바꾸기
4. sample 이름을 기준으로 두 표 합치기
5. log2(count + 1) 값 만들기
6. sample별 전체 발현 분포 그리기
7. marker gene의 조건별 발현 패턴 그리기
8. 조건별 평균 발현값 계산하기
9. heatmap과 요약 CSV 저장하기
```

프로젝트 1에서는 하나의 표 안에서 필요한 열을 골라 성장 곡선을 그렸습니다. 이번에는 발현값 표와 metadata 표를 연결한 뒤, 조건별로 데이터를 다시 정리하고 시각화했습니다.

이 흐름은 RNA-seq뿐 아니라 sample 정보가 따로 있는 다른 실험 데이터에도 자주 등장합니다.
