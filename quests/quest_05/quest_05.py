"""Find Element in Unary Array"""

import random
from typing import Iterator


def input_generator() -> Iterator[tuple[str, str]]:
    """
    Generates input for the quest.
    """
    for _ in range(100):
        size = random.randint(1, 10)
        index = random.randint(1, size)
        output = ""
        tape = "|" * index + ":"
        for idx in range(1, size + 1):
            value = random.randint(1, 10)
            tape += "|" * value + ","
            if idx == index:
                output = "|" * value
        yield (tape[:-1], output)
