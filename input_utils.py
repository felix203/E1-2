"""사용자 입력을 안전하게 받기 위한 함수 모음.

공통 규칙
- 입력 앞뒤 공백은 제거한 뒤 처리한다.
- 빈 입력, 숫자 변환 실패, 범위 밖 숫자는 안내 메시지를 출력하고 다시 입력받는다.
- Ctrl+C(KeyboardInterrupt)와 입력 종료(EOFError)는 여기서 잡지 않고
  QuizGame.run()까지 올려 보내서, 저장 후 안전하게 종료하도록 한다.
"""

# 타입 힌트(list[str], int | None 등)를 실행 시점에 계산하지 않게 해서 Python 3.8·3.9에서도 시작 오류가 나지 않게 한다.
from __future__ import annotations


def read_line(prompt: str) -> str:
    """한 줄을 입력받아 앞뒤 공백을 제거해서 돌려준다."""
    return input(prompt).strip()


def parse_int(text: str, minimum: int, maximum: int) -> int | None:
    """공백이 제거된 text를 minimum~maximum 범위의 정수로 바꾼다.

    빈 입력 / 숫자가 아님 / 범위 밖이면 안내 메시지를 출력하고 None을 돌려준다.
    """
    if not text:
        print(f"⚠️ 입력이 비어 있습니다. {minimum}-{maximum} 사이의 숫자를 입력하세요.")
        return None
    try:
        number = int(text)
    except ValueError:
        print(f"⚠️ 잘못된 입력입니다. {minimum}-{maximum} 사이의 숫자를 입력하세요.")
        return None
    if not minimum <= number <= maximum:
        print(f"⚠️ 잘못된 입력입니다. {minimum}-{maximum} 사이의 숫자를 입력하세요.")
        return None
    return number


def ask_int(prompt: str, minimum: int, maximum: int) -> int:
    """minimum~maximum 범위의 정수를 올바르게 입력할 때까지 반복해서 묻는다."""
    while True:
        number = parse_int(read_line(prompt), minimum, maximum)
        if number is not None:
            return number


def ask_text(prompt: str, allow_empty: bool = False) -> str:
    """문자열을 입력받는다. allow_empty가 False면 빈 입력을 다시 묻는다."""
    while True:
        text = read_line(prompt)
        if text or allow_empty:
            return text
        print("⚠️ 입력이 비어 있습니다. 내용을 입력하세요.")
