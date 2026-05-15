"""
프로젝트 2. RNA-seq 발현 데이터로 유전자 발현 패턴 보기 참고용 완성 코드.

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

# 2단계. 폴더와 파일 경로 준비하기
PROJECT_DIR = Path(__file__).resolve().parents[1] / "02_rnaseq_expression_patterns"
DATA_DIR = PROJECT_DIR / "data" / "raw"
OUTPUT_DIR = PROJECT_DIR / "outputs"

DATA_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

print("데이터 폴더:", DATA_DIR)
print("출력 폴더:", OUTPUT_DIR)

# 3단계. 데이터 다운로드하고 압축 풀기
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

# 4단계. 발현값 데이터와 metadata 불러오기
counts = pd.read_csv(COUNTS_FILE)
metadata = pd.read_csv(METADATA_FILE)

print("발현값 데이터 크기:", counts.shape)
print("metadata 크기:", metadata.shape)

print(counts.head())
print(metadata.head())

# 5단계. 열 이름 정리하기
counts = counts.rename(columns={"Unnamed: 0": "gene_id"})
metadata = metadata.rename(
    columns={
        "Unnamed: 0": "Sample",
        "developmental stage": "stage",
    }
)

print(counts.columns.tolist())
print(metadata.columns.tolist())

# 6단계. sample 열과 metadata 확인하기
sample_columns = [column for column in counts.columns if column.startswith("GSM")]

print("sample 수:", len(sample_columns))
print(sample_columns)

# 6단계. sample 열과 metadata 확인하기
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

# 7단계. wide format을 long format으로 바꾸기
long_counts = counts.melt(
    id_vars=["gene_id", "gene_symbol"],
    value_vars=sample_columns,
    var_name="Sample",
    value_name="Count",
)

print("long format 데이터 크기:", long_counts.shape)
print(long_counts.head())

# 8단계. 발현값 데이터와 metadata 합치기
expression = long_counts.merge(
    metadata[["Sample", "cell_type", "stage", "group"]],
    on="Sample",
    how="left",
)

print("합친 데이터 크기:", expression.shape)
print(expression.head())

# 8단계. 발현값 데이터와 metadata 합치기
missing_metadata_count = expression["group"].isna().sum()
print("metadata가 붙지 않은 행 수:", missing_metadata_count)

# 9단계. log2 발현값 만들기
print(expression["Count"].describe(percentiles=[0.5, 0.9, 0.99]))

# 9단계. log2 발현값 만들기
expression["log2_count"] = np.log2(expression["Count"] + 1)

print(expression[["gene_symbol", "Sample", "Count", "log2_count"]].head())

# 10단계. sample별 전체 발현 분포 그리기
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

# 11단계. marker gene 고르기
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

# 12단계. 조건 순서 정하기
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

# 13단계. marker gene 발현 패턴 그리기
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

# 14단계. 조건별 평균 발현값 계산하기
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

# 15단계. 요약 CSV 저장하기
summary_path = OUTPUT_DIR / "marker_gene_summary.csv"
summary.to_csv(summary_path, index=False)

print("저장된 파일:", summary_path)
print(pd.read_csv(summary_path).head())

# 16단계. heatmap 만들기
heatmap_table = summary.pivot(
    index="gene_symbol",
    columns="group",
    values="mean_log2_count",
)

heatmap_table = heatmap_table.loc[gene_order, group_order]

print(heatmap_table)

# 16단계. heatmap 만들기
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
