"""
프로젝트 3. GenBank 파일로 바이러스 유전체 구조 살펴보기 참고용 완성 코드.

프로젝트 문서의 단계별 코드를 하나로 모은 파일입니다.
먼저 문서를 따라 직접 입력해 보고, 실행이 막히거나 전체 구조를 확인하고 싶을 때 참고하세요.
"""

# 1단계. 필요한 기능 불러오기
from pathlib import Path
from urllib.request import urlretrieve

import pandas as pd
import matplotlib.pyplot as plt
from Bio import SeqIO

# 2단계. 폴더와 파일 경로 준비하기
PROJECT_DIR = Path(__file__).resolve().parents[1] / "03_genbank_viral_genome"
DATA_DIR = PROJECT_DIR / "data" / "raw"
OUTPUT_DIR = PROJECT_DIR / "outputs"

DATA_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

GENBANK_FILE = DATA_DIR / "NC_045512.2.gb"
FASTA_FILE = DATA_DIR / "NC_045512.2.fasta"

print("데이터 폴더:", DATA_DIR)
print("출력 폴더:", OUTPUT_DIR)

# 3단계. GenBank 파일과 FASTA 파일 다운로드하기
GENBANK_URL = (
    "https://www.ncbi.nlm.nih.gov/sviewer/viewer.cgi"
    "?id=NC_045512.2&db=nuccore&report=genbank&retmode=text"
)
FASTA_URL = (
    "https://www.ncbi.nlm.nih.gov/sviewer/viewer.cgi"
    "?id=NC_045512.2&db=nuccore&report=fasta&retmode=text"
)

download_targets = [
    (GENBANK_URL, GENBANK_FILE),
    (FASTA_URL, FASTA_FILE),
]

for url, output_path in download_targets:
    if output_path.exists():
        print("이미 파일이 있습니다:", output_path.name)
    else:
        print("다운로드합니다:", output_path.name)
        urlretrieve(url, output_path)
        print("다운로드 완료:", output_path.name)

print("GenBank 파일:", GENBANK_FILE)
print("FASTA 파일:", FASTA_FILE)

# 4단계. GenBank 파일 읽기
record = SeqIO.read(GENBANK_FILE, "genbank")

print("record ID:", record.id)
print("description:", record.description)
print("genome length:", len(record.seq))
print("molecule type:", record.annotations.get("molecule_type"))
print("feature 수:", len(record.features))

# 5단계. 염기 조성과 GC content 계산하기
genome_seq = record.seq.upper()

base_counts = {
    "A": genome_seq.count("A"),
    "C": genome_seq.count("C"),
    "G": genome_seq.count("G"),
    "T": genome_seq.count("T"),
}

gc_count = base_counts["G"] + base_counts["C"]
gc_percent = gc_count / len(genome_seq) * 100

print("염기 개수:", base_counts)
print(f"GC content: {gc_percent:.2f}%")

# 6단계. GenBank feature 종류 확인하기
feature_type_counts = {}

for feature in record.features:
    feature_type = feature.type
    feature_type_counts[feature_type] = feature_type_counts.get(feature_type, 0) + 1

print(feature_type_counts)

# 7단계. CDS 정보를 표로 정리하기
def get_first_value(qualifiers, key, default=""):
    values = qualifiers.get(key, [default])
    return values[0]


cds_rows = []

for feature in record.features:
    if feature.type != "CDS":
        continue

    qualifiers = feature.qualifiers

    start = int(feature.location.start) + 1
    end = int(feature.location.end)

    if feature.location.strand == 1:
        strand = "+"
    elif feature.location.strand == -1:
        strand = "-"
    else:
        strand = "?"

    nucleotide_sequence = feature.extract(record.seq)
    protein_sequence = get_first_value(qualifiers, "translation")

    cds_rows.append(
        {
            "gene": get_first_value(qualifiers, "gene"),
            "product": get_first_value(qualifiers, "product"),
            "protein_id": get_first_value(qualifiers, "protein_id"),
            "start": start,
            "end": end,
            "strand": strand,
            "nucleotide_length": len(nucleotide_sequence),
            "protein_length": len(protein_sequence),
        }
    )

features_df = pd.DataFrame(cds_rows).sort_values(["start", "end"])

print(features_df)

# 8단계. CDS 표 저장하기
features_path = OUTPUT_DIR / "genome_features.csv"
features_df.to_csv(features_path, index=False)

print("저장된 파일:", features_path)
print(pd.read_csv(features_path).head())

# 9단계. genome map 그리기
genome_length = len(record.seq)
structural_genes = {"S", "E", "M", "N"}

fig, ax = plt.subplots(figsize=(12, 3.8))

for row_index, row in features_df.reset_index(drop=True).iterrows():
    y_position = row_index % 2
    width = row["end"] - row["start"] + 1

    if row["gene"] in structural_genes:
        color = "#E45756"
    else:
        color = "#4C78A8"

    ax.barh(
        y=y_position,
        width=width,
        left=row["start"],
        height=0.35,
        color=color,
        edgecolor="black",
    )

    label_x = row["start"] + width / 2
    ax.text(
        label_x,
        y_position + 0.25,
        row["gene"],
        ha="center",
        va="bottom",
        fontsize=8,
        rotation=45,
    )

ax.set_xlim(1, genome_length)
ax.set_ylim(-0.6, 2.0)
ax.set_yticks([])
ax.set_xlabel("Genome position (bp)")
ax.set_title("SARS-CoV-2 reference genome CDS map")

ax.plot([1, genome_length], [-0.35, -0.35], color="black", linewidth=1)

plt.tight_layout()

genome_map_path = OUTPUT_DIR / "genome_map.png"
plt.savefig(genome_map_path, dpi=150)
plt.close()

print("저장된 파일:", genome_map_path)

# 10단계. sliding window로 GC content 계산하기
def calculate_gc_percent(sequence):
    sequence = str(sequence).upper()
    gc_count = sequence.count("G") + sequence.count("C")
    return gc_count / len(sequence) * 100

# 10단계. sliding window로 GC content 계산하기
window_size = 500
step_size = 100

gc_rows = []

for start_index in range(0, len(genome_seq) - window_size + 1, step_size):
    end_index = start_index + window_size
    window_sequence = genome_seq[start_index:end_index]

    gc_rows.append(
        {
            "position": start_index + window_size // 2 + 1,
            "gc_percent": calculate_gc_percent(window_sequence),
        }
    )

gc_df = pd.DataFrame(gc_rows)

print(gc_df.head())

# 11단계. GC content profile 그리기
plt.figure(figsize=(10, 4))
plt.plot(gc_df["position"], gc_df["gc_percent"], color="#4C78A8")
plt.axhline(gc_percent, color="#E45756", linestyle="--", label="Genome average")
plt.xlabel("Genome position (bp)")
plt.ylabel("GC content (%)")
plt.title("GC content profile")
plt.legend()
plt.tight_layout()

gc_plot_path = OUTPUT_DIR / "gc_content_profile.png"
plt.savefig(gc_plot_path, dpi=150)
plt.close()

print("저장된 파일:", gc_plot_path)

# 12단계. spike CDS 찾기
spike_feature = None

for feature in record.features:
    if feature.type != "CDS":
        continue

    gene_name = get_first_value(feature.qualifiers, "gene")

    if gene_name == "S":
        spike_feature = feature
        break

if spike_feature is None:
    raise ValueError("spike CDS를 찾지 못했습니다.")

spike_start = int(spike_feature.location.start) + 1
spike_end = int(spike_feature.location.end)

print("spike CDS 위치:", spike_start, "~", spike_end)
print("product:", get_first_value(spike_feature.qualifiers, "product"))

# 13단계. spike nucleotide sequence 꺼내기
spike_sequence = spike_feature.extract(record.seq)

print("spike nucleotide 길이:", len(spike_sequence))
print(spike_sequence[:60])

# 14단계. spike nucleotide sequence를 protein sequence로 번역하기
spike_protein = spike_sequence.translate(to_stop=True)

print("spike protein 길이:", len(spike_protein))
print(spike_protein[:60])

# 15단계. spike sequence를 FASTA 파일로 저장하기
def write_fasta(name, sequence, output_path, line_width=70):
    sequence = str(sequence)

    with output_path.open("w", encoding="utf-8") as file:
        file.write(f">{name}\n")

        for start in range(0, len(sequence), line_width):
            file.write(sequence[start:start + line_width] + "\n")


spike_sequence_path = OUTPUT_DIR / "spike_sequence.fasta"
spike_protein_path = OUTPUT_DIR / "spike_protein.fasta"

write_fasta("NC_045512.2_spike_CDS", spike_sequence, spike_sequence_path)
write_fasta("NC_045512.2_spike_protein", spike_protein, spike_protein_path)

print("저장된 파일:", spike_sequence_path)
print("저장된 파일:", spike_protein_path)

# 16단계. spike protein에서 짧은 motif 찾기
motifs = [
    "RRAR",
    "RGVYYPDKVFR",
    "KRSFIEDLLFNKV",
]

spike_protein_text = str(spike_protein)
motif_rows = []

for motif in motifs:
    motif_index = spike_protein_text.find(motif)

    if motif_index == -1:
        motif_rows.append(
            {
                "motif": motif,
                "found": False,
                "protein_start": "",
                "protein_end": "",
            }
        )
    else:
        protein_start = motif_index + 1
        protein_end = protein_start + len(motif) - 1

        motif_rows.append(
            {
                "motif": motif,
                "found": True,
                "protein_start": protein_start,
                "protein_end": protein_end,
            }
        )

motif_df = pd.DataFrame(motif_rows)

motif_path = OUTPUT_DIR / "spike_motif_positions.csv"
motif_df.to_csv(motif_path, index=False)

print(motif_df)
print("저장된 파일:", motif_path)
