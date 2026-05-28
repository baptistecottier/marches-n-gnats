"""Unary Even Odd"""

import random
from typing import Iterator


def input_generator() -> Iterator[tuple[str, str]]:
    """
    Generates input for the quest.
    """
    for _ in range(100):
        a = random.randint(1, 100)
        tape = "|" * a
        output = "E" if a % 2 == 0 else "O"
        yield (tape, output)
