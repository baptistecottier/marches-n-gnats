"""Binary Increment"""

import random
from typing import Iterator


def input_generator() -> Iterator[tuple[str, str]]:
    """
    Generates input for the quest.
    """
    for _ in range(100):
        a = random.randint(1, 100)
        tape = bin(a)[2:]
        output = bin(a + 1)[2:]
        yield (tape, output)
