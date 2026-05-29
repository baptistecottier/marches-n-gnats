"""Decimal Increment"""

import random
from typing import Iterator


def input_generator() -> Iterator[tuple[str, str]]:
    """
    Generates input for the quest.
    """
    for _ in range(100):
        a = random.randint(1, 100)
        tape = str(a)
        output = str(a + 1)
        yield (tape, output)
