"""Letter Mark"""

import random
from typing import Iterator


def input_generator() -> Iterator[tuple[str, str]]:
    """
    Generates input for the quest.
    """
    alphabet = "abcdefghijklmnopqrstuvwxyzäöõü"
    for _ in range(100):
        tape = ""
        n_words = random.randint(1, 6)
        for _ in range(n_words):
            word_len = random.randint(1, 12)
            for _ in range(word_len):
                c = random.choice(alphabet)
                tape += c
            tape += "-"
        tape = tape[:-1]
        output = tape.replace("w", "[w]").replace("ch", "[ch]")
        yield (tape, output)
