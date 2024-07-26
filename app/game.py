from collections import deque
from dataclasses import dataclass, field
from enum import StrEnum, auto
from functools import cache
from random import shuffle

import yaml

from app.config import settings


@cache
def load_words() -> list[str]:
    folder = settings.STATIC_DIR / "words"
    words = set()
    for eachPath in folder.glob("*.yaml"):
        with open(eachPath) as yamlFile:
            words |= {i.lower() for i in yaml.safe_load(yamlFile)}
    words = list(words)
    words.sort()
    return words


class Difficulty(StrEnum):
    EASY = auto()
    MEDIUM = auto()
    HARD = auto()


@dataclass
class Game:
    difficulty: Difficulty

    _disturbance_factor: float = 0
    _task_duration: int = 0  # seconds

    _fonts: deque[str] = field(default_factory=deque)
    _words: deque[str] = field(default_factory=deque)

    def select_words(self, min_len: int, max_len: int, amount: int) -> deque[str]:
        all_words = list(load_words())
        all_words = deque(all_words)
        shuffle(all_words)
        selected = deque()
        while len(selected) < amount:
            word = all_words.popleft()
            if min_len <= len(word) <= max_len:
                selected.append(word)
        return selected

    def __post_init__(self):
        match self.difficulty:
            case Difficulty.EASY:
                self._disturbance_factor = 0.5
                self._task_duration = 60
                self._words = self.select_words(min_len=3, max_len=6, amount=6)
            case Difficulty.MEDIUM:
                self._disturbance_factor = 0.75
                self._task_duration = 40
                self._words = self.select_words(min_len=5, max_len=8, amount=10)
            case Difficulty.HARD:
                self._disturbance_factor = 1
                self._task_duration = 20
                self._words = self.select_words(min_len=7, max_len=12, amount=14)

    def guess(self, answer: str) -> int:
        return 10

    def next_task(self) -> str:
        return ""


think = lambda x: x

if __name__ == "__main__":
    game = Game(difficulty=Difficulty.EASY)

    question = game.next_task()
    answer = think(question)
    score = game.guess(answer)
    print(score)
