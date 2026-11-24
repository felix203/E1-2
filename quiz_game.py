"""게임 전체(메뉴, 퀴즈 풀기/추가/목록/삭제, 점수, 저장)를 관리하는 QuizGame 클래스."""

# 타입 힌트(list[str], int | None 등)를 실행 시점에 계산하지 않게 해서 Python 3.8·3.9에서도 시작 오류가 나지 않게 한다.
from __future__ import annotations

import json
import os
import random
from datetime import datetime
from pathlib import Path

from default_quizzes import get_default_quizzes
from input_utils import ask_int, ask_text, ask_yes_no, parse_int, read_line
from quiz import Quiz

# 실행 위치와 상관없이 항상 프로젝트 루트(이 파일이 있는 폴더)의 state.json을 사용한다.
STATE_PATH = Path(__file__).resolve().parent / "state.json"

LINE = "=" * 40
THIN_LINE = "-" * 40
HINT_CREDIT = 0.5          # 힌트를 보고 맞히면 1문제의 절반만 인정
RECENT_HISTORY_COUNT = 5   # 점수 확인에서 보여 줄 최근 기록 수


class QuizGame:
    """퀴즈 목록, 최고 점수, 게임 기록을 가지고 게임 전체를 진행한다."""

    MENU_ITEMS = ("퀴즈 풀기", "퀴즈 추가", "퀴즈 목록", "점수 확인", "퀴즈 삭제", "종료")
    EXIT_CHOICE = len(MENU_ITEMS)

    def __init__(self, state_path: Path = STATE_PATH):
        self.state_path = Path(state_path)
        self.quizzes: list[Quiz] = []
        self.best_score: int | None = None     # 아직 풀지 않았으면 None
        self.best_detail: dict | None = None   # 최고 점수를 받은 판의 정답 수/문제 수/힌트 수
        self.history: list[dict] = []          # 모든 게임 기록
        self.load_message = self.load_state()  # 시작할 때 저장된 데이터를 불러온다

    # ------------------------------------------------------------------
    # 실행 / 메뉴
    # ------------------------------------------------------------------
    def run(self) -> None:
        """프로그램의 메인 루프. 종료를 고를 때까지 메뉴를 반복한다."""
        self.print_header()
        try:
            while True:
                self.show_menu()
                choice = self.select_menu()
                if choice == self.EXIT_CHOICE:
                    self.exit_game()
                    break
                self.handle_choice(choice)
        except (KeyboardInterrupt, EOFError) as error:
            # 어디서 입력을 받던 중이든 Ctrl+C / 입력 종료는 여기서 처리한다.
            if isinstance(error, KeyboardInterrupt):
                reason = "Ctrl+C 입력이 감지되어"
            else:
                reason = "입력이 종료되어"
            print(f"\n\n⚠️ {reason} 프로그램을 안전하게 종료합니다.")
            if self.save_state():
                print("💾 현재까지의 데이터를 저장했습니다.")

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
        elif choice == 5:
            self.delete_quiz()
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
        if any(quiz.has_hint() for quiz in selected):
            print("💡 힌트가 있는 문제는 h를 입력해 힌트를 볼 수 있어요. (힌트 사용 후 정답이면 0.5문제로 인정)")

        correct = 0
        hints_used = 0
        points = 0.0
        for number, quiz in enumerate(selected, start=1):
            print()
            print(THIN_LINE)
            quiz.display(number)
            answer, used_hint = self.ask_answer(quiz)
            if used_hint:
                hints_used += 1

            if quiz.is_correct(answer):
                correct += 1
                points += HINT_CREDIT if used_hint else 1
                print("✅ 정답입니다!" + (" (힌트 사용으로 0.5문제 인정)" if used_hint else ""))
            else:
                print(f"❌ 오답입니다. 정답은 {quiz.answer}번 '{quiz.correct_choice_text()}'입니다.")

        score = self.calculate_score(points, total)
        self.add_history(score, correct, total, hints_used)
        is_new_best = self.update_best_score(score, correct, total, hints_used)
        self.show_result(score, correct, total, hints_used, is_new_best)
        self.save_state()

    def ask_question_count(self) -> int:
        """풀 문제 수를 고른다. 퀴즈가 1개뿐이면 묻지 않는다."""
        total = len(self.quizzes)
        if total == 1:
            return 1
        print()
        return ask_int(f"몇 문제를 풀까요? (1-{total}): ", 1, total)

    def ask_answer(self, quiz: Quiz) -> tuple[int, bool]:
        """정답 번호를 입력받는다. h를 입력하면 힌트를 보여 준다.

        반환값: (입력한 번호, 힌트 사용 여부)
        """
        used_hint = False
        max_choice = Quiz.CHOICE_COUNT
        if quiz.has_hint():
            prompt = f"정답 입력 (1-{max_choice}, 힌트 h): "
        else:
            prompt = f"정답 입력 (1-{max_choice}): "

        while True:
            text = read_line(prompt)
            if text.lower() == "h":
                if not quiz.has_hint():
                    print("💡 이 문제에는 힌트가 없습니다.")
                elif used_hint:
                    print(f"💡 (다시 보기) 힌트: {quiz.hint}")
                else:
                    used_hint = True
                    print(f"💡 힌트: {quiz.hint}")
                continue

            number = parse_int(text, 1, max_choice)
            if number is not None:
                return number, used_hint

    @staticmethod
    def calculate_score(points: float, total: int) -> int:
        """100점 만점으로 환산한다. (반올림)"""
        return int(points / total * 100 + 0.5)

    def show_result(self, score: int, correct: int, total: int, hints_used: int, is_new_best: bool) -> None:
        print()
        print(LINE)
        print(f"🏆 결과: {total}문제 중 {correct}문제 정답! ({score}점)")
        if hints_used:
            print(f"💡 힌트 사용: {hints_used}회")
        if is_new_best:
            print("🎉 새로운 최고 점수입니다!")
        else:
            print(f"현재 최고 점수: {self.best_score}점")
        print(LINE)

    # ------------------------------------------------------------------
    # 점수 / 기록
    # ------------------------------------------------------------------
    def update_best_score(self, score: int, correct: int, total: int, hints_used: int) -> bool:
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
            self.best_detail = {"correct": correct, "total": total, "hints_used": hints_used}
        return is_better

    def add_history(self, score: int, correct: int, total: int, hints_used: int) -> None:
        """한 판의 결과를 날짜/시간과 함께 기록한다."""
        self.history.append({
            "played_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total": total,
            "correct": correct,
            "hints_used": hints_used,
            "score": score,
        })

    def show_score(self) -> None:
        """최고 점수와 최근 게임 기록을 보여 준다."""
        if self.best_score is None:
            print("\n📭 아직 퀴즈를 푼 기록이 없습니다. '퀴즈 풀기'로 도전해 보세요!")
            return

        if self.best_detail:
            detail = self.best_detail
            hints = detail.get("hints_used", 0)
            hint_text = f", 힌트 {hints}회" if hints else ""
            print(f"\n🏆 최고 점수: {self.best_score}점 "
                  f"({detail['total']}문제 중 {detail['correct']}문제 정답{hint_text})")
        else:
            print(f"\n🏆 최고 점수: {self.best_score}점")

        if self.history:
            recent = self.history[-RECENT_HISTORY_COUNT:]
            print(f"\n📜 최근 기록 (최근 {len(recent)}회 / 전체 {len(self.history)}회)")
            print(THIN_LINE)
            for record in reversed(recent):  # 최신 기록이 위로 오도록
                print(f"{record['played_at']} | {record['total']}문제 중 {record['correct']}개 정답"
                      f" | 힌트 {record['hints_used']}회 | {record['score']}점")
            print(THIN_LINE)

    # ------------------------------------------------------------------
    # 퀴즈 추가 / 목록 / 삭제
    # ------------------------------------------------------------------
    def add_quiz(self) -> None:
        """문제, 선택지 4개, 정답 번호, 힌트(선택)를 입력받아 새 퀴즈를 등록한다."""
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
        hint = ask_text("힌트 (없으면 그냥 Enter): ", allow_empty=True)

        self.quizzes.append(Quiz(question, choices, answer, hint))
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

    def delete_quiz(self) -> None:
        """번호로 퀴즈를 골라 확인을 받은 뒤 삭제하고 파일에 반영한다."""
        if not self.quizzes:
            print("\n⚠️ 삭제할 퀴즈가 없습니다.")
            return

        self.list_quizzes()
        total = len(self.quizzes)
        number = ask_int(f"삭제할 퀴즈 번호 (1-{total}, 취소 0): ", 0, total)
        if number == 0:
            print("↩️ 삭제를 취소했습니다.")
            return

        target = self.quizzes[number - 1]
        if not ask_yes_no(f"'{target.question}' 퀴즈를 삭제할까요? (y/n): "):
            print("↩️ 삭제를 취소했습니다.")
            return

        self.quizzes.pop(number - 1)
        if self.save_state():
            print(f"🗑️ 퀴즈를 삭제했습니다. (남은 퀴즈 {len(self.quizzes)}개)")
        else:
            print("⚠️ 퀴즈는 삭제했지만 파일에 저장하지 못했습니다.")

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

        raw_history = data.get("history", [])
        if not isinstance(raw_history, list):
            raw_history = []
        history = [record for record in raw_history if self.is_valid_history_record(record)]

        # 검사를 모두 통과한 뒤에 한꺼번에 반영한다.
        self.quizzes = quizzes
        self.best_score = best_score
        self.best_detail = best_detail
        self.history = history
        return skipped

    @staticmethod
    def is_non_negative_int(value) -> bool:
        """0 이상의 정수인지 확인한다. (bool은 제외)"""
        return isinstance(value, int) and not isinstance(value, bool) and value >= 0

    @classmethod
    def is_valid_record(cls, record, keys: tuple[str, ...]) -> bool:
        """record가 딕셔너리이고 keys의 값이 모두 0 이상의 정수인지 확인한다."""
        return isinstance(record, dict) and all(cls.is_non_negative_int(record.get(key)) for key in keys)

    @classmethod
    def is_valid_history_record(cls, record) -> bool:
        """게임 기록 한 줄의 형식이 올바른지 확인한다."""
        return (cls.is_valid_record(record, ("total", "correct", "hints_used", "score"))
                and isinstance(record.get("played_at"), str))

    def reset_to_default(self) -> None:
        """기본 퀴즈 데이터로 초기화한다."""
        self.quizzes = get_default_quizzes()
        self.best_score = None
        self.best_detail = None
        self.history = []

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
            "history": self.history,
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
