"""프로그램이 기본으로 제공하는 퀴즈 데이터.

주제: Python & Git 기초 (이번 미션에서 배우는 내용)
"""

# 타입 힌트(list[str], int | None 등)를 실행 시점에 계산하지 않게 해서 Python 3.8·3.9에서도 시작 오류가 나지 않게 한다.
from __future__ import annotations

from quiz import Quiz


def get_default_quizzes() -> list[Quiz]:
    """기본 퀴즈 목록을 매번 새 Quiz 객체로 만들어 돌려준다."""
    return [
        Quiz(
            "Python에서 리스트(list)를 만들 때 사용하는 괄호는?",
            ["( )", "[ ]", "{ }", "< >"],
            2,
        ),
        Quiz(
            "다음 중 Python의 bool(참/거짓) 값으로 올바른 것은?",
            ["true", "TRUE", "True", '"True"'],
            3,
        ),
        Quiz(
            "클래스의 메서드에서 객체 자기 자신을 가리키는 첫 번째 매개변수의 관례적인 이름은?",
            ["this", "me", "self", "obj"],
            3,
        ),
        Quiz(
            "반복 횟수가 정해져 있지 않고, 조건이 참인 동안 계속 반복할 때 주로 쓰는 문법은?",
            ["for", "while", "if", "def"],
            2,
        ),
        Quiz(
            "open()으로 열려는 파일이 존재하지 않을 때 발생하는 예외는?",
            ["ValueError", "KeyError", "FileNotFoundError", "ZeroDivisionError"],
            3,
        ),
        Quiz(
            "JSON 파일의 내용을 읽어 Python 객체(dict, list 등)로 바꿔 주는 함수는?",
            ["json.dump()", "json.load()", "json.dumps()", "json.open()"],
            2,
        ),
        Quiz(
            "Git에서 변경한 파일을 커밋하기 전에 스테이징 영역에 올리는 명령어는?",
            ["git commit", "git add", "git push", "git init"],
            2,
        ),
        Quiz(
            "새 브랜치를 만들면서 동시에 그 브랜치로 이동하는 명령어는?",
            ["git branch feature", "git checkout -b feature", "git merge feature", "git log feature"],
            2,
        ),
        Quiz(
            "원격 저장소의 변경 사항을 가져와 현재 브랜치에 합치는 명령어는?",
            ["git clone", "git push", "git pull", "git status"],
            3,
        ),
    ]
