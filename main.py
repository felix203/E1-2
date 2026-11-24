"""퀴즈 게임 실행 파일.  실행: python main.py"""

import sys

from quiz_game import QuizGame


def setup_console_encoding() -> None:
    """콘솔 입출력 인코딩을 UTF-8로 맞춘다.

    Windows의 Git Bash 같은 환경에서는 입출력 인코딩이 cp949로 잡혀서
    이모지를 출력하는 순간 UnicodeEncodeError로 프로그램이 멈추거나 한글 입력이 깨질 수 있다.
    """
    for stream in (sys.stdin, sys.stdout):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")


def main() -> None:
    setup_console_encoding()
    game = QuizGame()
    game.run()


if __name__ == "__main__":
    main()
