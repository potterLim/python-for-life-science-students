"""
프로젝트 1. 세균 성장 곡선 분석하기 참고용 완성 코드.

프로젝트 문서의 단계별 코드를 하나로 모은 파일입니다.
먼저 문서를 따라 직접 입력해 보고, 실행이 막히거나 전체 구조를 확인하고 싶을 때 참고하세요.
"""

# 1단계. 필요한 기능 불러오기
from pathlib import Path
from urllib.request import urlretrieve

import pandas as pd
import matplotlib.pyplot as plt

# 2단계. 폴더와 파일 경로 준비하기
PROJECT_DIR = Path(__file__).resolve().parents[1] / "01_bacterial_growth_curve"
DATA_DIR = PROJECT_DIR / "data" / "raw"
OUTPUT_DIR = PROJECT_DIR / "outputs"

DATA_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

print("데이터 폴더:", DATA_DIR)
print("출력 폴더:", OUTPUT_DIR)

# 3단계. 데이터 다운로드하기
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

# 4단계. CSV 파일 불러오기
df = pd.read_csv(DATA_FILE)

print("데이터 크기:", df.shape)
print(df.head())

# 5단계. 열 이름과 주요 열 확인하기
print(df.columns.tolist())

# 6단계. CSV에서 열을 꺼내 그래프로 저장하기
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

# 7단계. 데이터 전체를 가볍게 살펴보기
print("Time 범위:", df["Time"].min(), "~", df["Time"].max())
print("OD600 범위:", df["OD600"].min(), "~", df["OD600"].max())
print("Community 목록:", df["Community"].unique())
print(df["Compound"].value_counts().head(10))

# 8단계. 분석할 작은 데이터만 고르기
selected_community = 4
selected_library = "PS1"

candidate = df[
    (df["Community"] == selected_community)
    & (df["Library"] == selected_library)
].copy()

print("Community 4, PS1 데이터 크기:", candidate.shape)
print(candidate["Compound"].value_counts().head(20))

# 8단계. 분석할 작은 데이터만 고르기
selected_compounds = ["DMSO", "HEXACHLOROPHENE"]

subset = candidate[candidate["Compound"].isin(selected_compounds)].copy()

print("선택한 데이터 크기:", subset.shape)
print(subset[["Time", "OD600", "Community", "Library", "Rep", "Well", "Compound"]].head())
print(subset["Compound"].value_counts())

# 9단계. 한 조건의 원자료 성장 곡선 그리기
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

# 10단계. 시간별 평균 성장 곡선 만들기
subset["Time_rounded"] = subset["Time"].round()
print(subset[["Time", "Time_rounded"]].head())

# 10단계. 시간별 평균 성장 곡선 만들기
mean_curve = (
    subset
    .groupby(["Compound", "Time_rounded"], as_index=False)
    ["OD600"]
    .mean()
)

print(mean_curve.head())

# 11단계. control과 treatment 성장 곡선 비교하기
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

# 12단계. 최대 OD600과 마지막 OD600 계산하기
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

# 13단계. AUC 계산하기
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

# 14단계. 요약표와 AUC 그래프 저장하기
summary_path = OUTPUT_DIR / "growth_summary.csv"
summary.to_csv(summary_path, index=False)

print("저장된 파일:", summary_path)
print(pd.read_csv(summary_path))

# 14단계. 요약표와 AUC 그래프 저장하기
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
