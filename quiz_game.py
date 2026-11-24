"""게임 전체를 관리하는 QuizGame 클래스."""

# 타입 힌트(list[str], int | None 등)를 실행 시점에 계산하지 않게 해서 Python 3.8·3.9에서도 시작 오류가 나지 않게 한다.
from __future__ import annotations

from default_quizzes import get_default_quizzes
from quiz import Quiz

LINE = "=" * 40


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


class QuizGame:
    """퀴즈 목록과 최고 점수를 가지고 게임 전체를 진행한다."""

    MENU_ITEMS = ("퀴즈 풀기", "퀴즈 추가", "퀴즈 목록", "점수 확인", "종료")
    EXIT_CHOICE = len(MENU_ITEMS)

    def __init__(self):
        self.quizzes: list[Quiz] = get_default_quizzes()
        self.best_score: int | None = None  # 아직 풀지 않았으면 None

    def run(self) -> None:
        """프로그램의 메인 루프. 종료를 고를 때까지 메뉴를 반복한다."""
        self.print_header()
        while True:
            self.show_menu()
            choice = self.select_menu()
            if choice == self.EXIT_CHOICE:
                self.exit_game()
                break
            self.handle_choice(choice)

    def print_header(self) -> None:
        print(LINE)
        print("        🎯 나만의 퀴즈 게임 🎯")
        print(LINE)
        print(f"📚 퀴즈 {len(self.quizzes)}개가 준비되어 있습니다.")

    def show_menu(self) -> None:
        print(LINE)
        for number, name in enumerate(self.MENU_ITEMS, start=1):
            print(f"{number}. {name}")
        print(LINE)

    def select_menu(self) -> int:
        return ask_int("선택: ", 1, len(self.MENU_ITEMS))

    def handle_choice(self, choice: int) -> None:
        """메뉴 번호에 맞는 기능을 실행한다."""
        print(f"\n🚧 '{self.MENU_ITEMS[choice - 1]}' 기능은 준비 중입니다.\n")

    def exit_game(self) -> None:
        print("👋 프로그램을 종료합니다. 다음에 또 만나요!")
