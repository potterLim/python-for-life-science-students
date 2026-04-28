# 03. 조건문과 반복문

실험 데이터를 다루다 보면 기준에 따라 값을 나누거나, 여러 샘플에 같은 작업을 반복해야 할 때가 많습니다.

이때 자주 쓰는 방식이 두 가지입니다.

1. 조건문: 어떤 기준을 만족할 때만 실행하기
2. 반복문: 여러 값을 하나씩 처리하기

`if`, `else`, `for`의 흐름을 읽을 수 있으면 여러 샘플을 처리하는 코드를 훨씬 편하게 따라갈 수 있습니다.

## 파일 만들기

`03_conditions_loops.py` 파일을 만듭니다. 이 문서의 코드는 위에서 아래로 단계별로 직접 입력하고 실행해 보세요.

## 1. 비교의 결과는 True 또는 False입니다

조건문을 이해하려면 먼저 비교 결과를 봐야 합니다.

```python
od600 = 0.42

print(od600 > 0.3)
print(od600 < 0.3)
print(od600 == 0.42)
```

아래 기호들은 값을 비교하고 `True` 또는 `False`를 돌려줍니다.

| 표현 | 의미 |
| --- | --- |
| `a > b` | a가 b보다 크다 |
| `a < b` | a가 b보다 작다 |
| `a == b` | a와 b가 같다 |
| `a != b` | a와 b가 다르다 |
| `a >= b` | a가 b보다 크거나 같다 |
| `a <= b` | a가 b보다 작거나 같다 |

주의할 점은 `=`와 `==`가 다르다는 것입니다.

```python
od600 = 0.42   # 값을 저장
od600 == 0.42  # 같은지 비교
```

## 2. if는 조건이 참일 때만 실행됩니다

```python
od600 = 0.42

if od600 > 0.3:
    print("growth is high")
```

`if` 뒤의 조건이 `True`이면, 들여쓰기 된 코드가 실행됩니다.

Python에서는 들여쓰기가 중요합니다. `if`에 속한 코드는 보통 네 칸 정도 들여써서 작성합니다.

## 3. else는 조건이 아닐 때 실행됩니다

```python
od600 = 0.18

if od600 > 0.3:
    print("growth is high")
else:
    print("growth is low")
```

`if` 조건이 참이면 첫 번째 문장이 실행되고, 거짓이면 `else` 아래 문장이 실행됩니다.

## 4. elif는 조건을 여러 개 나눌 때 사용합니다

```python
od600 = 0.25

if od600 >= 0.4:
    print("high")
elif od600 >= 0.2:
    print("medium")
else:
    print("low")
```

`elif`는 “그렇지 않고, 이번에는 이 조건이라면” 정도로 읽으면 됩니다.

위 코드는 OD600 값을 세 구간으로 나눕니다.

```text
0.4 이상          -> high
0.2 이상 0.4 미만  -> medium
0.2 미만          -> low
```

## 5. for는 리스트 안의 값을 하나씩 꺼냅니다

```python
conditions = ["control", "treatment", "recovery"]

for condition in conditions:
    print(condition)
```

이 코드는 다음처럼 읽을 수 있습니다.

```text
conditions 리스트 안에서 condition을 하나씩 꺼내라.
꺼낸 condition을 출력하라.
```

반복문에서 `condition`이라는 변수 이름은 직접 정한 이름입니다. 꼭 `condition`이어야 하는 것은 아니지만, 의미가 드러나는 이름을 쓰는 것이 좋습니다.

## 6. 여러 측정값을 반복해서 처리하기

```python
od_values = [0.12, 0.18, 0.25, 0.42]

for od in od_values:
    print(od)
```

반복문 안에서 조건문을 함께 사용할 수 있습니다.

```python
od_values = [0.12, 0.18, 0.25, 0.42]

for od in od_values:
    if od >= 0.3:
        print(od, "high")
    else:
        print(od, "low")
```

이런 구조는 여러 샘플이나 여러 측정값을 같은 기준으로 분류할 때 자주 사용됩니다.

## 7. 결과를 리스트에 모으기

반복문에서 계산한 결과를 빈 리스트에 하나씩 담을 수 있습니다.

```python
od_values = [0.12, 0.18, 0.25, 0.42]
labels = []

for od in od_values:
    if od >= 0.3:
        labels.append("high")
    else:
        labels.append("low")

print(labels)
```

흐름은 다음과 같습니다.

```text
빈 리스트를 만든다.
각 OD600 값을 하나씩 확인한다.
기준에 따라 high 또는 low를 정한다.
정한 값을 리스트에 추가한다.
```

여러 샘플의 판정 결과나 계산 결과를 한곳에 모을 때 이 패턴이 자주 등장합니다.

## 8. 딕셔너리 리스트와 반복문

앞에서 샘플 하나를 딕셔너리로 표현했습니다. 이제 여러 샘플을 반복해서 처리해 봅니다.

```python
samples = [
    {"name": "sample_1", "condition": "control", "od600": 0.42},
    {"name": "sample_2", "condition": "control", "od600": 0.39},
    {"name": "sample_3", "condition": "treatment", "od600": 0.21},
]

for sample in samples:
    name = sample["name"]
    od = sample["od600"]

    if od >= 0.3:
        label = "high"
    else:
        label = "low"

    print(name, label)
```

처음에는 길어 보이지만, 구조는 단순합니다.

```text
샘플을 하나 꺼낸다.
샘플 이름과 OD600 값을 꺼낸다.
OD600 값으로 high/low를 판단한다.
결과를 출력한다.
```

## 9. range로 정해진 횟수만큼 반복하기

`range()`는 숫자 범위를 만들 때 사용합니다.

```python
for i in range(5):
    print(i)
```

`range(5)`는 0부터 4까지의 숫자를 만듭니다. Python에서는 이런 식으로 0부터 시작하는 경우가 많습니다.

## 10. 직접 고쳐보기

아래 코드에서 기준값 `threshold`를 바꿔 보세요. 기준값이 바뀌면 high/low 결과도 달라집니다.

```python
od_values = [0.12, 0.18, 0.25, 0.42]
threshold = 0.3

for od in od_values:
    if od >= threshold:
        print(od, "high")
    else:
        print(od, "low")
```

## 마무리

여기서 기억하면 좋은 내용은 다음입니다.

```text
조건문은 기준에 따라 실행할 코드를 고른다.
반복문은 여러 값을 하나씩 처리한다.
조건문과 반복문은 함께 자주 쓰인다.
반복문으로 만든 결과는 리스트에 모을 수 있다.
```
