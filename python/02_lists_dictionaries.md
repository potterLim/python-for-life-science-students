# 02. 리스트와 딕셔너리

실험 데이터는 보통 값 하나로 끝나지 않습니다. 여러 샘플과 조건, 측정값이 함께 등장합니다.

이런 값을 정리해서 담을 때 가장 자주 쓰는 두 가지가 있습니다.

1. 리스트
2. 딕셔너리

리스트는 여러 값을 순서대로 담습니다. 딕셔너리는 이름표가 붙은 값을 묶어둡니다.

## 파일 만들기

`02_lists_dictionaries.py` 파일을 만듭니다. 이 문서의 코드는 위에서 아래로 단계별로 직접 입력하고 실행해 보세요.

## 1. 리스트는 여러 값을 순서대로 담습니다

리스트는 대괄호 `[]`를 사용합니다.

```python
conditions = ["control", "treatment"]
print(conditions)

od_values = [0.05, 0.12, 0.31, 0.42]
print(od_values)
```

리스트에는 여러 값이 순서대로 들어갑니다.

```python
[0.05, 0.12, 0.31, 0.42]
```

이런 구조는 여러 시간의 측정값을 담을 때 유용합니다. 여러 샘플 이름이나 조건 이름을 담을 때도 자주 사용합니다.

## 2. 리스트의 길이 확인하기

`len()`은 리스트 안에 값이 몇 개 있는지 알려줍니다.

```python
sample_names = ["sample_1", "sample_2", "sample_3"]
od_values = [0.05, 0.12, 0.31, 0.42]

print(len(sample_names))
print(len(od_values))
```

데이터를 다룰 때는 값의 개수가 맞는지 확인하는 일이 중요합니다. 예를 들어 샘플 이름은 3개인데 측정값은 4개라면 어딘가 맞지 않는 상태일 수 있습니다.

## 3. 리스트에서 값 하나 꺼내기

리스트 안의 값은 위치 번호로 꺼낼 수 있습니다. Python의 위치 번호는 0부터 시작합니다.

```python
sample_names = ["sample_1", "sample_2", "sample_3"]

print(sample_names[0])
print(sample_names[1])
print(sample_names[2])
```

처음에는 0부터 시작한다는 점이 낯설 수 있습니다. 그래도 실험 데이터 정리나 분석 자동화 코드를 읽다 보면 자주 보게 됩니다.

```text
sample_names[0] -> 첫 번째 값
sample_names[1] -> 두 번째 값
sample_names[2] -> 세 번째 값
```

## 4. 리스트에 값 추가하기

`append()`를 사용하면 리스트의 맨 뒤에 값을 추가할 수 있습니다.

```python
samples = []

samples.append("sample_1")
samples.append("sample_2")
samples.append("sample_3")

print(samples)
```

빈 리스트를 만든 뒤 계산 결과를 하나씩 넣는 방식은 자주 사용됩니다. 여러 측정값을 처리하고 결과를 모을 때 특히 유용합니다.

## 5. 리스트 안의 숫자 계산하기

리스트 안에 숫자가 들어 있으면 합계나 평균을 계산할 수 있습니다.

```python
values = [0.20, 0.25, 0.30]

total = sum(values)
count = len(values)
mean_value = total / count

print(total)
print(count)
print(mean_value)
```

중요한 점은 평균 공식 자체가 아닙니다. 리스트 안의 여러 값을 한 번에 계산에 사용할 수 있다는 점입니다.

## 6. 딕셔너리는 이름표가 붙은 값을 담습니다

딕셔너리는 중괄호 `{}`를 사용합니다. 이름은 낯설 수 있지만 실제로는 값마다 이름표를 붙여 둔 묶음이라고 생각하면 됩니다.

```python
sample = {
    "name": "sample_1",
    "condition": "control",
    "od600": 0.42,
}

print(sample)
```

딕셔너리는 `key: value`라는 형태로 값을 담습니다.

```text
"name": "sample_1"
```

여기서 `"name"`은 값을 꺼낼 때 사용하는 이름표입니다. Python에서는 이런 이름표를 key라고 부릅니다. `"sample_1"`은 실제 값입니다.

## 7. 딕셔너리에서 값 꺼내기

딕셔너리에서는 위치 번호가 아니라 이름표로 값을 꺼냅니다. 이 이름표를 key라고 부릅니다.

```python
print(sample["name"])
print(sample["condition"])
print(sample["od600"])
```

리스트는 몇 번째 값인지가 중요합니다. 딕셔너리는 어떤 이름표가 붙어 있는지가 중요합니다.

```text
리스트: 몇 번째 값인가?
딕셔너리: 어떤 이름의 값인가?
```

## 8. 여러 샘플을 리스트와 딕셔너리로 표현하기

실제 데이터에서는 샘플이 하나만 있지 않습니다. 여러 샘플을 표현하려면 딕셔너리를 리스트 안에 넣을 수 있습니다.

```python
samples = [
    {"name": "sample_1", "condition": "control", "od600": 0.42},
    {"name": "sample_2", "condition": "control", "od600": 0.39},
    {"name": "sample_3", "condition": "treatment", "od600": 0.21},
]

print(samples)
```

이 구조는 처음에는 조금 복잡해 보일 수 있습니다. 의미는 단순합니다.

```text
샘플 하나 = 딕셔너리
여러 샘플 = 딕셔너리들의 리스트
```

## 9. 여러 샘플에서 특정 값만 꺼내기

반복문은 뒤에서 더 자세히 다룹니다. 먼저 리스트와 딕셔너리가 어떻게 함께 쓰이는지만 가볍게 봅니다.

```python
for sample in samples:
    print(sample["name"], sample["od600"])
```

이 코드는 `samples` 리스트 안의 샘플을 하나씩 꺼냅니다. 그리고 각 샘플 딕셔너리에서 `name`과 `od600` 값을 출력합니다.

조건문과 반복문을 배우면 이 구조를 더 자연스럽게 읽을 수 있습니다.

## 10. 직접 고쳐보기

아래 리스트에 샘플 하나를 더 추가해 보세요.

```python
samples = [
    {"name": "sample_1", "condition": "control", "od600": 0.42},
    {"name": "sample_2", "condition": "control", "od600": 0.39},
    {"name": "sample_3", "condition": "treatment", "od600": 0.21},
]

print(samples)
```

## 마무리

여기서 기억하면 좋은 내용은 다음입니다.

```text
리스트는 여러 값을 순서대로 담는다.
딕셔너리는 이름표가 붙은 값을 담는다.
여러 샘플은 딕셔너리들의 리스트로 표현할 수 있다.
```
