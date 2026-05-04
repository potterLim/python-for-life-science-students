# 프로젝트 3. GenBank 파일로 바이러스 유전체 구조 살펴보기

실제 공개 바이러스 reference genome을 내려받아, 서열과 annotation을 함께 살펴봅니다.

전체 흐름은 다음과 같습니다.

1. NCBI에서 바이러스 reference genome 파일을 내려받습니다.
2. GenBank 파일에서 서열과 annotation을 함께 읽습니다.
3. CDS 위치를 표와 genome map으로 정리합니다.
4. genome의 GC content 변화를 보고, spike sequence를 꺼내 활용합니다.

이 프로젝트를 마치면 바이러스 genome feature 표, genome map 이미지, GC content profile 이미지, spike sequence FASTA 파일, motif 위치 CSV 파일이 만들어집니다.

## 사용할 데이터셋

데이터셋: [NCBI Nucleotide NC_045512.2](https://www.ncbi.nlm.nih.gov/nuccore/1798174254)

출처:

- 저장소: [NCBI Nucleotide](https://www.ncbi.nlm.nih.gov/nuccore/)
- accession: [NC_045512.2](https://www.ncbi.nlm.nih.gov/nuccore/1798174254)
- record name: Severe acute respiratory syndrome coronavirus 2 isolate Wuhan-Hu-1, complete genome

이 데이터는 SARS-CoV-2 reference genome으로 자주 사용되는 서열입니다. NCBI record에는 전체 서열뿐 아니라 gene과 CDS 위치 같은 annotation도 함께 들어 있습니다.

| 항목 | 값 |
| --- | --- |
| accession | `NC_045512.2` |
| organism | Severe acute respiratory syndrome coronavirus 2 |
| genome length | 29,903 bp |
| molecule type | ss-RNA |
| file format | GenBank, FASTA |

이번 프로젝트에서는 GenBank 파일과 FASTA 파일을 모두 다운로드합니다. 다만 실제 분석은 GenBank 파일을 중심으로 진행합니다.

FASTA 파일은 서열 자체를 담는 단순한 형식입니다.

```text
>sequence name
ATTAAAGGTTTATACCTTCCC...
```

GenBank 파일은 서열뿐 아니라 annotation을 함께 담습니다. 예를 들어 어느 위치에 어떤 gene이 있는지, CDS가 어디서 시작하고 끝나는지, 어떤 protein으로 번역되는지 같은 정보가 들어 있습니다.

```text
FEATURES
  gene            21563..25384
  CDS             21563..25384
                  /gene="S"
                  /product="surface glycoprotein"
```

프로젝트 1, 2가 표 데이터를 다루는 연습이었다면, 이번 프로젝트는 생명정보학에서 자주 만나는 서열 파일을 직접 읽고 활용하는 연습입니다.

## 작업 파일 만들기

먼저 `projects/03_genbank_viral_genome/` 폴더를 만들고, 그 안에 `analysis.py` 파일을 만듭니다.

이번에는 `Biopython`이라는 생명정보학용 Python 라이브러리를 사용합니다. CSV 파일을 다룰 때 `pandas`를 사용했던 것처럼, FASTA나 GenBank 같은 생명정보학 파일을 다룰 때는 `Biopython`을 자주 사용합니다.

진행을 마치면 아래와 같은 구조가 됩니다.

```text
projects/
└── 03_genbank_viral_genome/
    ├── analysis.py
    ├── data/
    │   └── raw/
    │       ├── NC_045512.2.gb
    │       └── NC_045512.2.fasta
    └── outputs/
        ├── genome_features.csv
        ├── genome_map.png
        ├── gc_content_profile.png
        ├── spike_sequence.fasta
        ├── spike_protein.fasta
        └── spike_motif_positions.csv
```

## 1단계. 필요한 기능 불러오기

먼저 `analysis.py`에 아래 코드를 입력합니다.

```python
from pathlib import Path
from urllib.request import urlretrieve

import pandas as pd
import matplotlib.pyplot as plt
from Bio import SeqIO
```

프로젝트 1, 2에서 사용했던 `Path`, `urlretrieve`, `pandas`, `matplotlib`을 다시 사용합니다.

이번에 새로 사용하는 것은 `SeqIO`입니다. `SeqIO`는 Biopython에서 FASTA, GenBank 같은 서열 파일을 읽고 쓸 때 사용하는 기능입니다.

아직 Biopython을 설치하지 않았다면 아래 명령을 한 번 실행합니다.

```bash
python -m pip install biopython pandas matplotlib
```

## 2단계. 폴더와 파일 경로 준비하기

데이터 파일과 출력 파일을 저장할 위치를 정합니다.

```python
PROJECT_DIR = Path(__file__).resolve().parent
DATA_DIR = PROJECT_DIR / "data" / "raw"
OUTPUT_DIR = PROJECT_DIR / "outputs"

DATA_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

GENBANK_FILE = DATA_DIR / "NC_045512.2.gb"
FASTA_FILE = DATA_DIR / "NC_045512.2.fasta"

print("데이터 폴더:", DATA_DIR)
print("출력 폴더:", OUTPUT_DIR)
```

폴더를 만드는 방식은 앞 프로젝트들과 같습니다. 이번에는 원본 데이터 파일이 두 개입니다.

- `NC_045512.2.gb`: GenBank 형식 파일
- `NC_045512.2.fasta`: FASTA 형식 파일

## 3단계. GenBank 파일과 FASTA 파일 다운로드하기

NCBI에서 같은 genome을 두 가지 형식으로 내려받습니다. 같은 accession이지만, FASTA와 GenBank는 담고 있는 정보가 다릅니다.

```python
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
```

두 파일은 같은 genome을 담고 있지만, 담고 있는 정보의 양이 다릅니다.

FASTA 파일은 서열을 가볍게 저장하기 좋습니다. GenBank 파일은 서열과 annotation을 함께 다룰 때 좋습니다.

## 4단계. GenBank 파일 읽기

이번 프로젝트에서는 gene 위치와 CDS 정보를 함께 봐야 하므로 GenBank 파일을 중심으로 읽습니다. Biopython의 `SeqIO.read()`를 사용합니다.

```python
record = SeqIO.read(GENBANK_FILE, "genbank")

print("record ID:", record.id)
print("description:", record.description)
print("genome length:", len(record.seq))
print("molecule type:", record.annotations.get("molecule_type"))
print("feature 수:", len(record.features))
```

`record` 안에는 크게 두 종류의 정보가 들어 있습니다.

| 속성 | 들어 있는 정보 |
| --- | --- |
| `record.seq` | 실제 genome sequence |
| `record.features` | gene, CDS, UTR 같은 annotation |

`len(record.seq)`는 genome 길이를 보여주고, `len(record.features)`는 이 record 안에 annotation이 몇 개 들어 있는지 보여줍니다.

## 5단계. 염기 조성과 GC content 계산하기

annotation을 보기 전에, 먼저 genome sequence 자체를 간단히 확인합니다. A, C, G, T가 각각 몇 번 나오는지 계산합니다.

```python
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
```

GC content는 전체 염기 중 G와 C가 차지하는 비율입니다.

```text
GC content = (G 개수 + C 개수) / 전체 염기 수 * 100
```

GenBank record에는 `ss-RNA`라고 적혀 있지만, FASTA나 GenBank 파일에서는 보통 `U` 대신 `T`로 표시된 서열을 다룹니다. 그래서 여기서도 A, C, G, T를 기준으로 계산합니다.

## 6단계. GenBank feature 종류 확인하기

GenBank 파일을 읽었을 때 FASTA와 가장 크게 다른 부분은 `features`입니다. feature는 genome 위에 표시된 annotation 하나를 뜻합니다.

예를 들어 이런 것들이 feature입니다.

```text
gene
CDS
5'UTR
3'UTR
mat_peptide
```

어떤 annotation을 사용할 수 있는지 알아보기 위해, 먼저 feature 종류가 얼마나 들어 있는지 확인합니다.

```python
feature_type_counts = {}

for feature in record.features:
    feature_type = feature.type
    feature_type_counts[feature_type] = feature_type_counts.get(feature_type, 0) + 1

print(feature_type_counts)
```

출력 결과에는 `source`, `gene`, `CDS`, `mat_peptide` 같은 feature 종류가 보입니다. 이번 프로젝트에서는 여러 feature 중 `CDS`를 중심으로 봅니다.

CDS는 coding sequence의 줄임말입니다. 단백질로 번역되는 nucleotide sequence 영역을 뜻합니다.

## 7단계. CDS 정보를 표로 정리하기

CDS를 중심으로 보기로 했으니, 이제 CDS feature에서 gene 이름, product, 위치, 길이 정보를 꺼냅니다. 이 표를 만들면 genome map을 그릴 때도, 특정 gene을 찾을 때도 같은 정보를 사용할 수 있습니다.

```python
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
```

`feature.qualifiers`에는 GenBank feature에 붙어 있는 설명 정보가 들어 있습니다.

예를 들어 CDS feature에는 보통 이런 정보가 들어 있습니다.

```text
/gene="S"
/product="surface glycoprotein"
/protein_id="YP_009724390.1"
/translation="MFVFLVLLPLVSSQCV..."
```

Biopython에서 `feature.location.start`는 Python 방식의 0부터 시작하는 위치입니다. 하지만 생명과학 문서에서는 보통 첫 염기를 1번으로 셉니다. 그래서 표로 저장할 때는 `start + 1`을 사용했습니다.

```text
Python index: 0부터 시작
일반적인 genome coordinate: 1부터 시작
```

## 8단계. CDS 표 저장하기

정리한 CDS 표를 CSV 파일로 저장합니다. 서열 파일 안에 있던 annotation을 표로 꺼내 두면, 엑셀이나 다른 분석 도구에서도 이어서 다룰 수 있습니다.

```python
features_path = OUTPUT_DIR / "genome_features.csv"
features_df.to_csv(features_path, index=False)

print("저장된 파일:", features_path)
print(pd.read_csv(features_path).head())
```

이 파일에는 각 CDS의 gene 이름, product, genome 위치, 길이 정보가 들어 있습니다.

## 9단계. genome map 그리기

CDS 표에는 `start`와 `end`가 숫자로 들어 있습니다. 숫자 표만으로도 정보를 확인할 수 있지만, genome 위에서 어떤 순서로 놓이는지는 그림으로 보는 편이 훨씬 쉽습니다.

이번에는 CDS 위치를 genome 위에 막대처럼 표시합니다.

```python
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
```

각 막대는 하나의 CDS를 뜻합니다. 막대의 시작과 끝은 genome coordinate를 기준으로 그립니다.

색은 두 가지로 나누었습니다.

- 빨간색: structural gene인 `S`, `E`, `M`, `N`
- 파란색: 그 외 CDS

이 그림을 보면 CDS들이 genome 위에 어떤 순서로 놓여 있는지 한눈에 볼 수 있습니다. 특히 `S`, `E`, `M`, `N`처럼 자주 언급되는 structural gene이 genome의 어느 위치에 있는지도 함께 확인할 수 있습니다.

## 10단계. sliding window로 GC content 계산하기

앞에서 전체 genome의 평균 GC content를 계산했습니다. 하지만 평균값 하나만 보면 genome 안에서 위치별로 값이 어떻게 달라지는지는 알 수 없습니다.

여기서는 일정한 길이의 창을 조금씩 옮기면서 GC content를 계산합니다. 이런 방식을 sliding window라고 부릅니다.

```text
1번째 창: 1~500 bp
2번째 창: 101~600 bp
3번째 창: 201~700 bp
...
```

먼저 GC content를 계산하는 함수를 만듭니다.

```python
def calculate_gc_percent(sequence):
    sequence = str(sequence).upper()
    gc_count = sequence.count("G") + sequence.count("C")
    return gc_count / len(sequence) * 100
```

이제 500 bp 크기의 창을 100 bp씩 움직이면서 GC content를 계산합니다. 이 두 값은 위치별 변화를 보기 위한 출발값입니다. window를 크게 잡으면 선이 더 부드러워지고, 작게 잡으면 더 세밀하게 보이지만 값이 더 흔들릴 수 있습니다.

```python
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
```

`position`은 각 window의 가운데 위치입니다. 이렇게 하면 x축에 genome 위치를 두고, y축에 GC content를 둘 수 있습니다.

## 11단계. GC content profile 그리기

계산한 GC content를 선 그래프로 저장합니다.

```python
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
```

빨간 점선은 전체 genome의 평균 GC content입니다. 파란 선은 genome 위치별 GC content 변화를 보여줍니다.

## 12단계. spike CDS 찾기

앞에서 만든 CDS 표를 보면 `gene` 열에 `S`가 들어 있는 행이 있습니다. 이 행이 spike glycoprotein에 해당합니다.

좌표를 손으로 입력해서 서열을 자를 수도 있지만, 여기서는 GenBank annotation에서 `gene` 값이 `S`인 CDS를 직접 찾아 사용합니다.

```python
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
```

여기서는 `gene` 값이 `S`인 CDS를 찾았습니다.

GenBank annotation을 사용하면 좌표를 직접 외우지 않아도, 원하는 gene의 위치를 코드로 찾아낼 수 있습니다.

## 13단계. spike nucleotide sequence 꺼내기

spike CDS feature를 찾았으니, 그 feature가 가리키는 nucleotide sequence를 꺼냅니다.

```python
spike_sequence = spike_feature.extract(record.seq)

print("spike nucleotide 길이:", len(spike_sequence))
print(spike_sequence[:60])
```

`feature.extract(record.seq)`는 해당 feature 위치에 해당하는 서열만 꺼내는 기능입니다.

직접 start와 end를 이용해 자를 수도 있지만, GenBank feature를 사용하면 strand나 복잡한 location을 Biopython이 함께 처리해 줍니다.

## 14단계. spike nucleotide sequence를 protein sequence로 번역하기

CDS는 단백질로 번역되는 영역입니다. 따라서 spike nucleotide sequence를 amino acid sequence로 바꿀 수 있습니다.

```python
spike_protein = spike_sequence.translate(to_stop=True)

print("spike protein 길이:", len(spike_protein))
print(spike_protein[:60])
```

`translate()`는 nucleotide sequence를 protein sequence로 번역합니다.

`to_stop=True`는 stop codon을 만나면 거기서 번역을 멈추라는 뜻입니다.

여기서는 spike protein 길이가 1,273 amino acids로 나옵니다.

## 15단계. spike sequence를 FASTA 파일로 저장하기

꺼낸 spike nucleotide sequence와 번역한 protein sequence를 FASTA 파일로 저장합니다.

```python
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
```

FASTA 파일은 서열을 저장하고 공유할 때 많이 쓰입니다.

첫 줄은 `>`로 시작하는 sequence 이름이고, 그 아래 줄부터 실제 sequence가 들어갑니다.

## 16단계. spike protein에서 짧은 motif 찾기

마지막으로 spike protein sequence에서 짧은 amino acid motif가 어디에 있는지 찾아봅니다. 서열을 꺼냈다면 가장 간단하게 해볼 수 있는 활용 중 하나가 “긴 서열 안에서 특정 짧은 서열을 찾기”입니다.

이 단계에서는 복잡한 alignment를 하지 않고, 긴 문자열 안에서 짧은 문자열의 위치를 찾는 방식만 사용합니다.

아래 motif 목록은 기능을 엄밀하게 분석하기 위한 목록이라기보다, protein sequence에서 짧은 서열을 검색하는 방법을 연습하기 위한 예시입니다.

```python
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
```

`find()`는 문자열 안에서 특정 문자열이 처음 등장하는 위치를 찾습니다.

Python의 문자열 위치도 0부터 시작합니다. 그래서 protein 위치로 저장할 때는 `+ 1`을 했습니다.

## 최종적으로 만들어지는 파일

끝까지 실행하면 `outputs/` 폴더에 다음 파일들이 생깁니다.

```text
projects/03_genbank_viral_genome/outputs/
├── genome_features.csv
├── genome_map.png
├── gc_content_profile.png
├── spike_sequence.fasta
├── spike_protein.fasta
└── spike_motif_positions.csv
```

| 파일명 | 의미 |
| --- | --- |
| `genome_features.csv` | CDS별 gene 이름, product, 위치, 길이 정보 |
| `genome_map.png` | CDS 위치를 genome 위에 표시한 그림 |
| `gc_content_profile.png` | genome 위치별 GC content 변화 |
| `spike_sequence.fasta` | spike CDS nucleotide sequence |
| `spike_protein.fasta` | spike protein sequence |
| `spike_motif_positions.csv` | spike protein에서 찾은 motif 위치 |

## 자주 생기는 문제

### `ModuleNotFoundError: No module named 'Bio'`가 뜨는 경우

Biopython이 설치되어 있지 않은 상태입니다. 1단계의 설치 명령을 실행한 뒤 다시 실행합니다.

### GenBank 파일을 읽는 단계에서 에러가 나는 경우

파일이 다운로드되는 도중에 끊겼을 수 있습니다. `data/raw/NC_045512.2.gb` 파일을 지운 뒤 다시 실행합니다.

### `spike CDS를 찾지 못했습니다.`가 뜨는 경우

앞 단계에서 GenBank 파일이 제대로 읽혔는지, 그리고 `record.features` 안에 `CDS` feature가 있는지 확인합니다.

```python
for feature in record.features:
    print(feature.type, feature.qualifiers.get("gene"))
```

### genome map에서 글자가 겹쳐 보이는 경우

짧은 CDS가 가까이 붙어 있어서 생기는 문제입니다. `figsize`를 더 크게 하거나, `rotation` 값을 조정하면 됩니다.

## 이 프로젝트에서 해본 것

실제 바이러스 reference genome으로 다음 흐름을 따라갔습니다.

```text
1. NCBI에서 GenBank 파일과 FASTA 파일 다운로드하기
2. Biopython으로 GenBank 파일 읽기
3. genome 길이와 GC content 계산하기
4. GenBank feature 종류 확인하기
5. CDS annotation을 표로 정리하기
6. genome map 그리기
7. sliding window로 GC content profile 만들기
8. spike CDS sequence 꺼내기
9. nucleotide sequence를 protein sequence로 번역하기
10. protein sequence에서 motif 위치 찾기
```

프로젝트 1, 2에서는 표 형태의 실험 데이터를 중심으로 다뤘습니다. 이번에는 서열과 annotation이 함께 들어 있는 GenBank 파일을 읽고, genome 구조와 특정 gene sequence를 직접 꺼내 보았습니다.

이 흐름은 바이러스 genome뿐 아니라 plasmid, bacterial genome, mitochondrial genome처럼 annotation이 붙어 있는 다른 서열 데이터에도 비슷하게 적용할 수 있습니다.
