"""Unary Subtraction"""

import random
from typing import Iterator


def input_generator() -> Iterator[tuple[str, str]]:
    """
    Generates input for the quest.
    """
    for _ in range(100):
        a = random.randint(1, 20)
        b = random.randint(1, a)
        tape = "|" * a + "-" + "|" * b
        output = "|" * (a - b)
        yield (tape, output)
