"""게임 전체(메뉴, 퀴즈 풀기/추가/목록, 점수)를 관리하는 QuizGame 클래스."""

# 타입 힌트(list[str], int | None 등)를 실행 시점에 계산하지 않게 해서 Python 3.8·3.9에서도 시작 오류가 나지 않게 한다.
from __future__ import annotations

import random

from default_quizzes import get_default_quizzes
from input_utils import ask_int, ask_text
from quiz import Quiz

LINE = "=" * 40
THIN_LINE = "-" * 40


class QuizGame:
    """퀴즈 목록과 최고 점수를 가지고 게임 전체를 진행한다."""

    MENU_ITEMS = ("퀴즈 풀기", "퀴즈 추가", "퀴즈 목록", "점수 확인", "종료")
    EXIT_CHOICE = len(MENU_ITEMS)

    def __init__(self):
        self.quizzes: list[Quiz] = get_default_quizzes()
        self.best_score: int | None = None     # 아직 풀지 않았으면 None
        self.best_detail: dict | None = None   # 최고 점수를 받은 판의 정답 수/문제 수

    # ------------------------------------------------------------------
    # 실행 / 메뉴
    # ------------------------------------------------------------------
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
        if choice == 1:
            self.play_quiz()
        elif choice == 2:
            self.add_quiz()
        elif choice == 3:
            self.list_quizzes()
        elif choice == 4:
            self.show_score()
        print()

    def exit_game(self) -> None:
        print("👋 프로그램을 종료합니다. 다음에 또 만나요!")

    # ------------------------------------------------------------------
    # 퀴즈 풀기
    # ------------------------------------------------------------------
    def play_quiz(self) -> None:
        """고른 문제 수만큼 랜덤 순서로 출제하고 결과를 보여 준다."""
        if not self.quizzes:
            print("\n⚠️ 등록된 퀴즈가 없습니다. 먼저 '퀴즈 추가'로 퀴즈를 등록해 주세요.")
            return

        total = self.ask_question_count()
        selected = random.sample(self.quizzes, total)  # 랜덤 순서로 total개 뽑기
        print(f"\n📝 퀴즈를 시작합니다! (총 {total}문제)")

        correct = 0
        for number, quiz in enumerate(selected, start=1):
            print()
            print(THIN_LINE)
            quiz.display(number)
            answer = ask_int(f"정답 입력 (1-{Quiz.CHOICE_COUNT}): ", 1, Quiz.CHOICE_COUNT)
            if quiz.is_correct(answer):
                correct += 1
                print("✅ 정답입니다!")
            else:
                print(f"❌ 오답입니다. 정답은 {quiz.answer}번 '{quiz.correct_choice_text()}'입니다.")

        score = self.calculate_score(correct, total)
        is_new_best = self.update_best_score(score, correct, total)
        self.show_result(score, correct, total, is_new_best)

    def ask_question_count(self) -> int:
        """풀 문제 수를 고른다. 퀴즈가 1개뿐이면 묻지 않는다."""
        total = len(self.quizzes)
        if total == 1:
            return 1
        print()
        return ask_int(f"몇 문제를 풀까요? (1-{total}): ", 1, total)

    @staticmethod
    def calculate_score(points: float, total: int) -> int:
        """100점 만점으로 환산한다. (반올림)"""
        return int(points / total * 100 + 0.5)

    def show_result(self, score: int, correct: int, total: int, is_new_best: bool) -> None:
        print()
        print(LINE)
        print(f"🏆 결과: {total}문제 중 {correct}문제 정답! ({score}점)")
        if is_new_best:
            print("🎉 새로운 최고 점수입니다!")
        else:
            print(f"현재 최고 점수: {self.best_score}점")
        print(LINE)

    # ------------------------------------------------------------------
    # 점수
    # ------------------------------------------------------------------
    def update_best_score(self, score: int, correct: int, total: int) -> bool:
        """최고 점수와 비교해서 더 좋은 기록이면 갱신한다. 갱신했으면 True.

        점수가 같으면 더 많은 문제를 푼 기록을 더 좋은 기록으로 본다.
        (1문제만 풀어 받은 100점이 9문제를 풀어 받은 100점보다 앞서지 않도록)
        """
        if self.best_score is None:
            is_better = True
        elif score != self.best_score:
            is_better = score > self.best_score
        else:
            best_total = self.best_detail.get("total", 0) if self.best_detail else 0
            is_better = total > best_total

        if is_better:
            self.best_score = score
            self.best_detail = {"correct": correct, "total": total}
        return is_better

    def show_score(self) -> None:
        """최고 점수를 보여 준다."""
        if self.best_score is None:
            print("\n📭 아직 퀴즈를 푼 기록이 없습니다. '퀴즈 풀기'로 도전해 보세요!")
            return

        if self.best_detail:
            detail = self.best_detail
            print(f"\n🏆 최고 점수: {self.best_score}점 "
                  f"({detail['total']}문제 중 {detail['correct']}문제 정답)")
        else:
            print(f"\n🏆 최고 점수: {self.best_score}점")

    # ------------------------------------------------------------------
    # 퀴즈 추가 / 목록
    # ------------------------------------------------------------------
    def add_quiz(self) -> None:
        """문제, 선택지 4개, 정답 번호를 입력받아 새 퀴즈를 등록한다."""
        print("\n📌 새로운 퀴즈를 추가합니다.\n")
        question = ask_text("문제를 입력하세요: ")

        choices: list[str] = []
        for number in range(1, Quiz.CHOICE_COUNT + 1):
            while True:
                choice = ask_text(f"선택지 {number}: ")
                if choice in choices:
                    print("⚠️ 이미 입력한 선택지입니다. 다른 내용을 입력하세요.")
                    continue
                choices.append(choice)
                break

        answer = ask_int(f"정답 번호 (1-{Quiz.CHOICE_COUNT}): ", 1, Quiz.CHOICE_COUNT)

        self.quizzes.append(Quiz(question, choices, answer))
        print(f"\n✅ 퀴즈가 추가되었습니다! (총 {len(self.quizzes)}개)")

    def list_quizzes(self) -> None:
        """등록된 퀴즈의 문제 목록을 보여 준다."""
        if not self.quizzes:
            print("\n⚠️ 등록된 퀴즈가 없습니다. '퀴즈 추가'로 퀴즈를 등록해 주세요.")
            return

        print(f"\n📋 등록된 퀴즈 목록 (총 {len(self.quizzes)}개)\n")
        print(THIN_LINE)
        for number, quiz in enumerate(self.quizzes, start=1):
            print(f"[{number}] {quiz.question}")
        print(THIN_LINE)
