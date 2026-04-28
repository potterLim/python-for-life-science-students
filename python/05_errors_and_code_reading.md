# 05. 에러 메시지 읽기와 코드 읽기 연습

에러를 완벽하게 분석하려고 하기보다, 어디에서 막혔는지 차분히 찾는 연습을 해봅니다.

```text
에러가 났을 때 당황하지 않고,
대략 어디를 봐야 하는지 감을 잡는 것.
```

실제 코드를 실행하다 보면 에러를 피할 수 없습니다. 에러는 실패가 아니라, Python이 “여기에서 문제가 생겼다”고 알려주는 신호입니다.

## 파일 만들기

`05_errors_and_code_reading.py` 파일을 만듭니다. 이 문서의 코드는 위에서 아래로 단계별로 직접 입력하고 실행해 보세요.

이 문서에서는 일부러 에러가 나는 코드를 잠깐 입력해 보고, 에러 메시지를 확인한 뒤 바로 고칩니다. 잘못된 코드를 그대로 남기면 다음 코드가 실행되지 않으니, 에러를 확인한 뒤에는 반드시 수정한 상태로 넘어가세요.

## 1. 에러 메시지는 마지막 줄부터 봅니다

Python 에러 메시지는 길게 보일 때가 많습니다. 처음에는 전부 읽으려고 하지 않아도 됩니다.

우선 마지막 줄을 봅니다. 마지막 줄에는 보통 에러의 종류와 가장 중요한 단서가 나옵니다.

예를 들어 마지막 줄이 이렇게 끝난다고 해봅니다.

```text
NameError: name 'sample_nam' is not defined
```

이 한 줄만 읽어도 `sample_nam`이라는 이름을 Python이 찾지 못했다는 것을 알 수 있습니다. 위쪽의 긴 내용은 어디를 지나오다가 문제가 생겼는지 보여주고, 마지막 줄은 그래서 무엇이 문제였는지 알려주는 문장에 가깝습니다.

## 2. NameError: 이름을 찾을 수 없음

먼저 변수 이름을 잘못 쓴 상황을 만들어 봅니다.

```python
sample_name = "sample_1"
print(sample_nam)
```

파일을 실행하면 에러 메시지의 마지막 줄이 대략 이렇게 나옵니다.

```text
NameError: name 'sample_nam' is not defined
```

실제로 만든 변수 이름은 `sample_name`인데, 출력할 때는 `sample_nam`이라고 적었습니다. 철자가 하나 빠져 있어서 Python이 그 이름을 찾지 못한 것입니다.

이제 파일에서 잘못된 줄을 아래처럼 고칩니다.

```python
sample_name = "sample_1"
print(sample_name)
```

다시 실행했을 때 `sample_1`이 출력되면 잘 고친 것입니다.

## 3. TypeError: 자료형이 맞지 않음

이번에는 자료형이 맞지 않아서 생기는 에러입니다.

```python
value = "0.42"
result = value + 1
print(result)
```

`"0.42"`는 숫자처럼 보이지만 따옴표로 감싸져 있기 때문에 문자열입니다. 이 코드를 실행하면 마지막 줄이 대략 이렇게 나옵니다.

```text
TypeError: can only concatenate str (not "int") to str
```

표현은 조금 낯설지만, 핵심은 문자열과 숫자를 바로 더할 수 없다는 뜻입니다.

숫자로 계산하려면 값 자체가 숫자여야 합니다.

```python
value = 0.42
result = value + 1
print(result)
```

문자열로 들어온 숫자를 실제 숫자로 바꿔야 할 때는 `float()`을 사용할 수 있습니다.

```python
value_text = "0.42"
value_number = float(value_text)

print(value_number + 1)
```

## 4. IndexError: 리스트 위치가 범위를 벗어남

리스트에서 값을 꺼낼 때는 위치 번호를 사용합니다. Python의 위치 번호는 0부터 시작합니다.

다음 코드는 값이 3개뿐인데, 네 번째 값을 꺼내려고 합니다.

```python
values = [0.12, 0.18, 0.25]
print(values[3])
```

이 코드를 실행하면 마지막 줄이 대략 이렇게 나옵니다.

```text
IndexError: list index out of range
```

리스트에 값이 3개 있으면 위치 번호는 0, 1, 2입니다. `values[3]`은 네 번째 값을 찾으려는 코드라서 에러가 납니다.

실제로 있는 위치 번호를 사용하면 됩니다.

```python
values = [0.12, 0.18, 0.25]

print(values[0])
print(values[1])
print(values[2])
```

## 5. KeyError: 딕셔너리에 없는 이름표를 찾음

딕셔너리에서는 이름표를 사용해서 값을 꺼냅니다. 그런데 딕셔너리 안에 없는 이름표를 찾으면 에러가 납니다.

```python
sample = {"name": "sample_1", "od600": 0.42}
print(sample["condition"])
```

이 코드를 실행하면 마지막 줄이 대략 이렇게 나옵니다.

```text
KeyError: 'condition'
```

이 딕셔너리에는 `name`과 `od600`만 있습니다. `condition`이라는 이름표가 없기 때문에 에러가 납니다.

수정하려면 실제로 있는 이름표를 사용하거나, 딕셔너리에 필요한 이름표를 추가해야 합니다.

```python
sample = {"name": "sample_1", "condition": "control", "od600": 0.42}

print(sample["condition"])
```

## 6. ModuleNotFoundError: 불러오려는 기능이 없음

Python에서 어떤 기능을 불러오려면 그 기능이 현재 환경에 준비되어 있어야 합니다.

예를 들어 현재 설치되어 있지 않은 라이브러리를 불러오려고 하면 다음과 같은 에러가 날 수 있습니다.

```python
import some_library
```

마지막 줄은 대략 이렇게 나옵니다.

```text
ModuleNotFoundError: No module named 'some_library'
```

이 말은 `some_library`라는 이름의 라이브러리를 찾지 못했다는 뜻입니다. 이 경우에는 보통 두 가지를 확인합니다.

1. 라이브러리 이름을 잘못 쓰지 않았는가?
2. 아직 설치하지 않은 라이브러리인가?

## 7. 에러가 났을 때 보는 순서

에러가 났을 때는 다음 순서로 확인하면 됩니다.

```text
1. 마지막 줄의 에러 종류를 본다.
2. 에러 메시지에 나온 변수 이름이나 딕셔너리 이름표를 확인한다.
3. 바로 위쪽 코드에서 그 이름을 만들었는지 확인한다.
4. 철자가 같은지 확인한다.
5. 자료형이 숫자인지 문자열인지 확인한다.
```

처음부터 모든 에러를 해결할 필요는 없습니다. 다만 에러 메시지를 보고 “아예 모르겠다”에서 “어디를 봐야 할지 알겠다”로 넘어가는 것이 중요합니다.

## 8. 코드 읽기 연습 1

아래 코드를 실행하기 전에, 어떤 결과가 나올지 먼저 예상해 보세요.

```python
condition = "control"
od600 = 0.42

if od600 >= 0.3:
    label = "high"
else:
    label = "low"

print(condition, label)
```

이 코드는 다음 순서로 읽을 수 있습니다.

```text
condition에 control을 저장한다.
od600에 0.42를 저장한다.
od600이 0.3 이상인지 확인한다.
맞으면 label에 high를 저장한다.
condition과 label을 출력한다.
```

## 9. 코드 읽기 연습 2

리스트와 반복문이 함께 나오는 예시입니다.

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

반복문을 읽을 때는 “리스트에서 값을 하나씩 꺼낸다”고 생각하면 됩니다.

```text
0.12를 꺼낸다 -> low
0.18을 꺼낸다 -> low
0.25를 꺼낸다 -> low
0.42를 꺼낸다 -> high
```

## 10. 코드 읽기 연습 3

이번 예시에는 함수까지 포함되어 있습니다.

```python
def classify_growth(od_value):
    if od_value >= 0.3:
        return "high"
    else:
        return "low"

samples = [
    {"name": "sample_1", "od600": 0.42},
    {"name": "sample_2", "od600": 0.18},
    {"name": "sample_3", "od600": 0.25},
]

for sample in samples:
    label = classify_growth(sample["od600"])
    print(sample["name"], label)
```

여기에는 앞에서 배운 내용이 조금씩 들어 있습니다.

```text
함수를 만든다.
샘플 정보를 리스트와 딕셔너리로 만든다.
샘플을 하나씩 꺼낸다.
각 샘플의 OD600 값을 함수에 넣는다.
결과를 출력한다.
```

실제 분석 코드에서도 이런 식으로 여러 요소가 함께 등장할 수 있습니다. 한 줄씩 끊어서 읽으면 충분히 따라갈 수 있습니다.

## 11. 직접 고쳐보기

아래 코드에서 기준값 `threshold`를 바꿔 보고, 결과가 어떻게 달라지는지 확인해 보세요.

```python
def classify_growth(od_value, threshold):
    if od_value >= threshold:
        return "high"
    else:
        return "low"

threshold = 0.3
od_values = [0.12, 0.18, 0.25, 0.42]

for od in od_values:
    label = classify_growth(od, threshold)
    print(od, label)
```

## 마무리

여기서 기억하면 좋은 내용은 다음입니다.

```text
에러 메시지는 마지막 줄부터 본다.
NameError는 이름 문제일 가능성이 크다.
TypeError는 자료형 문제일 가능성이 크다.
IndexError는 리스트 위치 문제일 가능성이 크다.
KeyError는 딕셔너리 이름표 문제일 가능성이 크다.
긴 코드도 변수, 조건문, 반복문, 함수로 나누어 읽으면 따라갈 수 있다.
```
