# 04. 함수와 import

같은 계산이나 판단을 여러 번 반복해야 할 때가 있습니다. 그럴 때는 매번 같은 코드를 다시 쓰지 않고 작은 작업에 이름을 붙여둘 수 있습니다.

먼저 두 가지를 구분해두면 좋습니다.

1. 함수: 반복해서 쓰는 작업에 이름 붙이기
2. import: 이미 만들어진 기능 불러오기

## 파일 만들기

`04_functions_imports.py` 파일을 만듭니다. 이 문서의 코드는 위에서 아래로 단계별로 직접 입력하고 실행해 보세요.

## 1. 함수가 필요한 이유

같은 계산을 여러 번 해야 한다고 생각해 봅니다.

```python
initial_od = 0.05
final_od = 0.42

increase = final_od - initial_od
print(increase)
```

샘플이 여러 개라면 같은 계산을 계속 반복해야 합니다. 이런 작업에 이름을 붙여두면 편합니다. 그것이 함수입니다.

## 2. 함수 만들기

Python에서는 `def`라는 말로 함수를 만듭니다.

```python
def calculate_increase(initial_value, final_value):
    increase = final_value - initial_value
    return increase
```

아래 함수는 다음처럼 읽을 수 있습니다.

```text
calculate_increase라는 함수를 만든다.
initial_value와 final_value를 입력으로 받는다.
final_value - initial_value를 계산한다.
그 결과를 돌려준다.
```

`return`은 함수 안에서 만든 결과를 밖으로 내보내는 역할을 합니다.

## 3. 함수 사용하기

함수를 사용한다는 것은 붙여둔 이름을 부르고 필요한 값을 넣어 실행한다는 뜻입니다.

```python
result = calculate_increase(0.05, 0.42)
print(result)
```

## 4. 여러 값에 같은 함수 적용하기

함수는 반복문과 함께 쓰면 더 유용합니다.

```python
samples = [
    {"name": "sample_1", "initial": 0.05, "final": 0.42},
    {"name": "sample_2", "initial": 0.06, "final": 0.36},
    {"name": "sample_3", "initial": 0.05, "final": 0.18},
]

for sample in samples:
    increase = calculate_increase(sample["initial"], sample["final"])
    print(sample["name"], increase)
```

함수를 만들어두면 같은 계산을 여러 샘플에 반복해서 적용할 수 있습니다. 실제 분석 코드에서 함수가 보이면 "자주 쓰는 작은 작업을 따로 묶어두었구나"라고 생각하면 됩니다.

## 5. 함수는 한 가지 일을 분명하게 하는 것이 좋습니다

처음에는 함수 하나가 너무 많은 일을 하게 만들 필요가 없습니다. 작은 계산 하나나 작은 판단 하나를 함수로 만들면 충분합니다.

```python
def classify_growth(od_value):
    if od_value >= 0.3:
        return "high"
    else:
        return "low"

print(classify_growth(0.42))
print(classify_growth(0.18))
```

위 함수는 OD600 값을 받아 `high` 또는 `low`를 돌려줍니다. 이름만 봐도 무엇을 하려는 함수인지 어느 정도 알 수 있습니다.

## 6. 함수 안의 변수는 함수 밖과 구분됩니다

함수 안에서 만든 변수는 보통 함수 안에서만 사용한다고 생각하면 됩니다.

```python
def make_message(sample_name, value):
    message = f"{sample_name}: {value}"
    return message

text = make_message("sample_1", 0.42)
print(text)
```

처음부터 함수 안팎의 규칙을 깊게 이해할 필요는 없습니다. 우선 함수는 값을 받고 안에서 처리한 뒤 결과를 밖으로 내보낸다는 흐름을 기억하면 됩니다.

## 7. import는 필요한 기능을 불러오는 방법입니다

Python 자체에 모든 기능이 처음부터 들어 있는 것은 아닙니다. 필요할 때 이미 만들어진 기능을 불러와서 사용할 수 있습니다.

```python
import math

print(math.sqrt(16))
```

`import math`는 Python에 포함된 `math`라는 기능 묶음을 불러옵니다. 그 안에 있는 `sqrt()` 함수를 사용하면 제곱근을 계산할 수 있습니다.

## 8. 필요한 것만 불러올 수도 있습니다

```python
from statistics import mean

values = [0.20, 0.25, 0.30]
print(mean(values))
```

`from statistics import mean`은 `statistics`라는 기능 묶음에서 평균을 계산하는 `mean`만 가져오겠다는 뜻입니다.

이렇게 가져오면 `statistics.mean(values)`가 아니라 `mean(values)`처럼 바로 사용할 수 있습니다.

## 9. 별명을 붙여 불러올 수도 있습니다

다른 사람이 작성한 분석 예제나 라이브러리 사용 코드를 보면 `import something as short_name` 형태를 자주 보게 됩니다.

```python
import statistics as stats

values = [0.20, 0.25, 0.30]
print(stats.mean(values))
```

`as stats`는 `statistics`를 앞으로 `stats`라는 짧은 이름으로 부르겠다는 뜻입니다.

다른 기능을 불러올 때도 이런 형태를 자주 보게 됩니다. 지금은 "긴 이름에 짧은 별명을 붙이는구나" 정도로 이해하면 충분합니다.

## 10. 직접 고쳐보기

아래 함수의 기준값을 바꿔 보세요.

```python
def classify_growth(od_value):
    if od_value >= 0.3:
        return "high"
    else:
        return "low"

od_values = [0.12, 0.18, 0.25, 0.42]

for od in od_values:
    label = classify_growth(od)
    print(od, label)
```

## 마무리

여기서 기억하면 좋은 내용은 다음입니다.

```text
함수는 반복해서 쓰는 작업에 이름을 붙이는 방법이다.
함수는 값을 받고 결과를 밖으로 내보낸다.
import는 이미 만들어진 기능을 불러오는 방법이다.
```
