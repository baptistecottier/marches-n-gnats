"""Unary Addition"""

import random
from typing import Iterator


def input_generator() -> Iterator[tuple[str, str]]:
    """
    Generates input for the quest.
    """
    for _ in range(100):
        a = random.randint(1, 100)
        b = random.randint(1, 100)
        tape = "|" * a + "+" + "|" * b
        output = tape.replace("+", "")
        yield (tape, output)
