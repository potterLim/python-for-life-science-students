# 생명과학 데이터 프로젝트

이 디렉토리는 실제 공개 생명과학 데이터를 사용해 Python을 어떻게 활용할 수 있는지 따라 해보는 프로젝트 모음입니다.

목표는 Python 문법을 더 많이 익히는 것이 아닙니다. 생명과학 전공자가 실제로 마주칠 수 있는 데이터 파일을 열고, 필요한 정보를 꺼내고, 표와 그래프로 정리하며, 이미지와 서열 데이터까지 다뤄 보면서 Python이 실험 데이터를 다루는 도구로 어떻게 쓰이는지 경험하는 것입니다.

공개 데이터셋을 사용하는 이유는 예제용으로 만든 숫자보다 실제 데이터의 파일 구조, 변수 이름, 반복 측정 방식, 저장 형식을 더 자연스럽게 접할 수 있기 때문입니다.

각 프로젝트는 문서의 안내에 따라 작업 파일을 만들고, 코드를 단계별로 입력해 실행하는 방식으로 진행합니다. 미리 준비된 결과만 보는 것이 아니라, 직접 데이터 파일을 내려받고 코드가 어떤 중간 결과를 만드는지 확인하면서 따라가도록 구성했습니다.

## 진행 방식

프로젝트는 번호 순서대로 진행하는 것을 권장합니다.

각 프로젝트는 앞 프로젝트에서 배운 내용을 바탕으로 조금씩 새로운 내용을 더합니다. 그래서 이전 프로젝트에서 이미 자세히 설명한 내용은 뒤 프로젝트에서 다시 길게 반복하지 않습니다.

예를 들어 CSV 파일을 읽고, 폴더를 만들고, 그래프를 저장하는 기본 흐름은 프로젝트 1에서 자세히 다룹니다. 이후 프로젝트에서는 그 내용을 다시 처음부터 설명하기보다, 새로 등장하는 개념에 더 집중합니다.

이 방식에 익숙해지면 프로젝트가 진행될수록 설명은 조금씩 압축되지만, 다룰 수 있는 데이터의 종류와 작업 범위는 넓어집니다.

## 프로젝트 목록

| 번호 | 프로젝트 |
| --- | --- |
| 1 | [세균 성장 곡선 분석하기](01_bacterial_growth_curve.md) |
| 2 | [RNA-seq 발현 데이터로 유전자 발현 패턴 보기](02_rnaseq_expression_patterns.md) |
| 3 | [GenBank 파일로 바이러스 유전체 구조 살펴보기](03_genbank_viral_genome.md) |
| 4 | ~~현미경 이미지에서 세포핵 측정하기~~ |
| 5 | ~~YOLO로 현미경 이미지 속 세포핵 탐지하기~~ |

## 프로젝트별 핵심

1. 세균 성장 곡선 분석하기  
   공개 CSV 데이터를 내려받고, 필요한 열을 골라 성장 곡선을 그린 뒤, 조건 비교와 AUC 요약까지 해봅니다.

2. RNA-seq 발현 데이터로 유전자 발현 패턴 보기  
   발현값 표와 sample metadata를 연결하고, wide format을 long format으로 바꾼 뒤, 조건별 발현 패턴과 heatmap을 만듭니다.

3. GenBank 파일로 바이러스 유전체 구조 살펴보기  
   GenBank와 FASTA 파일을 읽고, CDS annotation에서 gene 위치와 protein sequence를 꺼내 genome map과 GC content profile을 만듭니다.

4. 현미경 이미지에서 세포핵 측정하기  
   현미경 이미지를 숫자 배열로 읽고, mask와 label image를 이용해 nucleus의 면적, 밝기, 중심 좌표, bounding box를 측정합니다.

5. YOLO로 현미경 이미지 속 세포핵 탐지하기  
   mask에서 nucleus 위치를 bounding box로 바꾸어 YOLO 학습용 label을 만들고, 작은 object detection 모델을 학습한 뒤 예측된 nucleus 수를 mask 기반 ground truth와 비교합니다.

이 과정에서 Python은 복잡한 프로그래밍 언어라기보다, 실험 데이터의 모양을 바꾸고 필요한 결과를 만들어내는 도구로 다가오게 됩니다.

## 프로젝트별 데이터

| 프로젝트 | 공개 데이터셋 | 데이터 형태 |
| --- | --- | --- |
| 1 | [Bacterial bioindicators growth curves](https://figshare.com/articles/dataset/Bacterial_bioindicators_growth_curves/28684982) | bacterial growth curve CSV |
| 2 | [GSE60450](https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=GSE60450) | RNA-seq normalized count CSV, metadata CSV |
| 3 | [NCBI Nucleotide NC_045512.2](https://www.ncbi.nlm.nih.gov/nuccore/1798174254) | GenBank, FASTA |
| 4 | [BBBC039](https://bbbc.broadinstitute.org/BBBC039/) | 현미경 TIFF 이미지, PNG mask |
| 5 | [BBBC039](https://bbbc.broadinstitute.org/BBBC039/) | 현미경 이미지, mask, YOLO label |

## 권장 학습 방식

각 문서의 코드를 한 번에 복사해서 실행하기보다, 안내된 순서대로 작업 파일에 직접 입력하면서 실행해 보세요. 중간에 출력되는 표의 크기, 열 이름, 저장되는 파일을 확인하면 데이터가 코드 안에서 어떻게 바뀌는지 훨씬 잘 보입니다.

처음에는 결과가 완벽하게 예쁘게 나오는 것보다, 다음 질문을 따라가는 것이 더 중요합니다.

- 어떤 파일을 읽었나?
- 어떤 열이나 영역을 골랐나?
- 어떤 기준으로 데이터를 묶었나?
- 어떤 결과 파일이 만들어졌나?

프로젝트를 마친 뒤에는 만들어진 `outputs/` 폴더를 확인해 보세요. 각 프로젝트는 그래프, CSV, FASTA, 예측 이미지처럼 눈으로 확인할 수 있는 결과물을 남기도록 구성했습니다.
