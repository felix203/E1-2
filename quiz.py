"""개별 퀴즈 한 문제를 표현하는 Quiz 클래스."""

# 타입 힌트(list[str], int | None 등)를 실행 시점에 계산하지 않게 해서 Python 3.8·3.9에서도 시작 오류가 나지 않게 한다.
from __future__ import annotations


class Quiz:
    """문제, 선택지 4개, 정답 번호(1~4)를 가진 퀴즈 한 문제."""

    CHOICE_COUNT = 4  # 선택지 개수는 4개로 고정

    def __init__(self, question: str, choices: list[str], answer: int):
        # 잘못된 데이터로 객체가 만들어지지 않도록 생성 시점에 검사한다.
        if not isinstance(question, str) or not question.strip():
            raise ValueError("문제는 비어 있지 않은 문자열이어야 합니다.")
        if not isinstance(choices, list) or len(choices) != self.CHOICE_COUNT:
            raise ValueError(f"선택지는 {self.CHOICE_COUNT}개여야 합니다.")
        if not all(isinstance(c, str) and c.strip() for c in choices):
            raise ValueError("선택지는 모두 비어 있지 않은 문자열이어야 합니다.")
        # bool은 int의 하위 타입이라 True가 1로 통과하지 않도록 따로 막는다.
        if isinstance(answer, bool) or not isinstance(answer, int):
            raise ValueError("정답은 정수여야 합니다.")
        if not 1 <= answer <= self.CHOICE_COUNT:
            raise ValueError(f"정답은 1~{self.CHOICE_COUNT} 사이여야 합니다.")

        self.question = question.strip()
        self.choices = [c.strip() for c in choices]
        self.answer = answer

    def display(self, number: int | None = None) -> None:
        """문제와 선택지를 화면에 출력한다."""
        title = f"[문제 {number}]" if number is not None else "[문제]"
        print(title)
        print(self.question)
        print()
        for index, choice in enumerate(self.choices, start=1):
            print(f"{index}. {choice}")
        print()

    def is_correct(self, user_answer: int) -> bool:
        """사용자가 고른 번호가 정답인지 확인한다."""
        return user_answer == self.answer

    def correct_choice_text(self) -> str:
        """정답 번호에 해당하는 선택지 문구."""
        return self.choices[self.answer - 1]
