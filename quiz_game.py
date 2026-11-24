"""게임 전체(메뉴, 퀴즈 풀기/추가/목록, 점수, 저장)를 관리하는 QuizGame 클래스."""

# 타입 힌트(list[str], int | None 등)를 실행 시점에 계산하지 않게 해서 Python 3.8·3.9에서도 시작 오류가 나지 않게 한다.
from __future__ import annotations

import json
import os
import random
from pathlib import Path

from default_quizzes import get_default_quizzes
from input_utils import ask_int, ask_text
from quiz import Quiz

# 실행 위치와 상관없이 항상 프로젝트 루트(이 파일이 있는 폴더)의 state.json을 사용한다.
STATE_PATH = Path(__file__).resolve().parent / "state.json"

LINE = "=" * 40
THIN_LINE = "-" * 40


class QuizGame:
    """퀴즈 목록과 최고 점수를 가지고 게임 전체를 진행한다."""

    MENU_ITEMS = ("퀴즈 풀기", "퀴즈 추가", "퀴즈 목록", "점수 확인", "종료")
    EXIT_CHOICE = len(MENU_ITEMS)

    def __init__(self, state_path: Path = STATE_PATH):
        self.state_path = Path(state_path)
        self.quizzes: list[Quiz] = []
        self.best_score: int | None = None     # 아직 풀지 않았으면 None
        self.best_detail: dict | None = None   # 최고 점수를 받은 판의 정답 수/문제 수
        self.load_message = self.load_state()  # 시작할 때 저장된 데이터를 불러온다

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
        print(self.load_message)

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
        if self.save_state():
            print("💾 데이터를 저장했습니다.")
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
        self.save_state()

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
        if self.save_state():
            print(f"\n✅ 퀴즈가 추가되었습니다! (총 {len(self.quizzes)}개)")
        else:
            print("\n⚠️ 퀴즈는 추가했지만 파일에 저장하지 못해 이번 실행 동안만 유지됩니다.")

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

    # ------------------------------------------------------------------
    # 파일 저장 / 불러오기 (state.json)
    # ------------------------------------------------------------------
    def load_state(self) -> str:
        """state.json을 읽어 게임 상태를 채우고, 시작 시 보여 줄 안내 문구를 돌려준다."""
        if not self.state_path.exists():
            self.reset_to_default()
            self.save_state()
            return f"📂 저장된 데이터가 없어 기본 퀴즈 {len(self.quizzes)}개로 시작합니다."

        try:
            with open(self.state_path, "r", encoding="utf-8") as file:
                data = json.load(file)
            skipped = self.apply_state(data)
        except (json.JSONDecodeError, UnicodeDecodeError, ValueError) as error:
            # JSON 문법 오류, 인코딩 오류, 구조 오류 → 파일 손상으로 보고 기본 데이터로 복구
            backup_path = self.backup_broken_file()
            self.reset_to_default()
            self.save_state()
            message = f"⚠️ {self.state_path.name} 파일이 손상되어 기본 퀴즈 데이터로 복구했습니다. (원인: {error})"
            if backup_path:
                message += f"\n   손상된 파일은 {backup_path.name}(으)로 백업해 두었습니다."
            return message
        except OSError as error:
            # 권한 문제 등으로 파일을 읽을 수 없는 경우
            self.reset_to_default()
            return f"⚠️ {self.state_path.name} 파일을 읽을 수 없어 기본 퀴즈로 시작합니다. (원인: {error})"

        best_text = f"{self.best_score}점" if self.best_score is not None else "기록 없음"
        message = f"📂 저장된 데이터를 불러왔습니다. (퀴즈 {len(self.quizzes)}개, 최고점수 {best_text})"
        if skipped:
            message += f"\n⚠️ 형식이 잘못된 퀴즈 {skipped}개는 건너뛰었습니다."
        return message

    def apply_state(self, data) -> int:
        """JSON에서 읽은 데이터를 검사해서 속성에 반영한다.

        구조 자체가 잘못되었으면 ValueError를 일으키고,
        일부 퀴즈만 잘못되었으면 그 퀴즈만 건너뛴다. 반환값은 건너뛴 퀴즈 수.
        """
        if not isinstance(data, dict):
            raise ValueError("최상위 구조가 객체({ })가 아닙니다.")
        raw_quizzes = data.get("quizzes")
        if not isinstance(raw_quizzes, list):
            raise ValueError("'quizzes' 항목이 없거나 목록이 아닙니다.")

        quizzes = []
        skipped = 0
        for item in raw_quizzes:
            try:
                quizzes.append(Quiz.from_dict(item))
            except ValueError:
                skipped += 1
        if raw_quizzes and not quizzes:
            raise ValueError("올바른 형식의 퀴즈가 하나도 없습니다.")

        best_score = data.get("best_score")
        if not self.is_non_negative_int(best_score):
            best_score = None

        best_detail = data.get("best_detail")
        if best_score is None or not self.is_valid_record(best_detail, ("correct", "total")):
            best_detail = None

        # 검사를 모두 통과한 뒤에 한꺼번에 반영한다.
        self.quizzes = quizzes
        self.best_score = best_score
        self.best_detail = best_detail
        return skipped

    @staticmethod
    def is_non_negative_int(value) -> bool:
        """0 이상의 정수인지 확인한다. (bool은 제외)"""
        return isinstance(value, int) and not isinstance(value, bool) and value >= 0

    @classmethod
    def is_valid_record(cls, record, keys: tuple[str, ...]) -> bool:
        """record가 딕셔너리이고 keys의 값이 모두 0 이상의 정수인지 확인한다."""
        return isinstance(record, dict) and all(cls.is_non_negative_int(record.get(key)) for key in keys)

    def reset_to_default(self) -> None:
        """기본 퀴즈 데이터로 초기화한다."""
        self.quizzes = get_default_quizzes()
        self.best_score = None
        self.best_detail = None

    def backup_broken_file(self) -> Path | None:
        """손상된 state.json을 state.json.bak으로 옮겨 둔다. 실패하면 None."""
        backup_path = self.state_path.with_name(self.state_path.name + ".bak")
        try:
            os.replace(self.state_path, backup_path)
            return backup_path
        except OSError:
            return None

    def to_state_dict(self) -> dict:
        """현재 상태를 JSON으로 저장할 딕셔너리로 만든다."""
        return {
            "quizzes": [quiz.to_dict() for quiz in self.quizzes],
            "best_score": self.best_score,
            "best_detail": self.best_detail,
        }

    def save_state(self) -> bool:
        """state.json에 UTF-8로 저장한다. 성공하면 True.

        저장 도중 프로그램이 꺼져도 기존 파일이 깨지지 않도록
        임시 파일에 먼저 쓴 뒤 원래 파일과 바꿔치기한다.
        """
        temp_path = self.state_path.with_name(self.state_path.name + ".tmp")
        try:
            with open(temp_path, "w", encoding="utf-8") as file:
                json.dump(self.to_state_dict(), file, ensure_ascii=False, indent=4)
            os.replace(temp_path, self.state_path)
            return True
        except OSError as error:
            print(f"⚠️ 데이터를 저장하지 못했습니다. (원인: {error})")
            try:
                temp_path.unlink(missing_ok=True)
            except OSError:
                pass
            return False
