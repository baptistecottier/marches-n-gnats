"""
Logic Mill implementation.

This module provides a simple implementation of a Turing machine.

LICENSE: MIT
"""

import argparse
import importlib.util
import sys
from pathlib import Path

RIGHT = "R"
LEFT = "L"
BLANK = "_"
COMMENT_PREFIX = "//"


TransitionType = tuple[str, str, str, str, str]


def parse_transition_rules(transition_rules_str: str) -> list[TransitionType]:
    """
    Parse a string into a list of transition rules.

    Args:
        transition_rules_str: A string containing transition rules, with each rule on a new line.
            Each rule should be space-separated values in the format:
            currentState currentSymbol newState newSymbol moveDirection

    Returns:
        A list of transition tuples, where each tuple contains:
        (currentState, currentSymbol, newState, newSymbol, moveDirection)

    """
    transitions_list: list[TransitionType] = []
    for raw_line in transition_rules_str.split("\n"):
        line = raw_line.strip()
        if not line:
            continue

        # Skip whole-line comment
        if line.startswith(COMMENT_PREFIX):
            continue

        # Skip comment after the transition rule
        line = line.split(COMMENT_PREFIX, 1)[0].strip()

        values: list[str] = []
        for raw_val in line.split(" "):
            val = raw_val.strip()
            if not val:
                continue
            values.append(val)

        transitions_list.append(tuple(values))  # ty: ignore[invalid-argument-type]
    return transitions_list


def _format_tape_comparison(result: str, expected: str, context: int = 20) -> tuple[str, str, str]:
    """Return aligned result/expected segments and a diff marker line."""
    max_length = max(len(result), len(expected))
    min_length = min(len(result), len(expected))
    first_diff = next((i for i in range(min_length) if result[i] != expected[i]), min_length)
    if first_diff < min_length:
        diff_index = first_diff
    else:
        diff_index = min_length

    start = max(0, diff_index - context)
    end = min(max_length, diff_index + context)

    def segment(value: str) -> str:
        segment_text = value[start:end]
        if start > 0:
            segment_text = "..." + segment_text
        if end < len(value):
            segment_text = segment_text + "..."
        return segment_text

    result_segment = segment(result)
    expected_segment = segment(expected)

    marker_offset = len("...") if start > 0 else 0
    marker = " " * (marker_offset + diff_index - start) + "^"

    return result_segment, expected_segment, marker


class InvalidTransitionError(Exception):
    """Exception raised when a transition is invalid (parsing)."""


class MissingTransitionError(Exception):
    """Exception raised when a transition is missing (parsing)."""


class InvalidSymbolError(Exception):
    """Exception raised when a symbol is invalid (parsing)."""


class LogicMill:
    """Logic Mill implementation."""

    def __init__(
        self,
        transitions_list: list[TransitionType],
        initial_state: str = "INIT",
        halt_state: str = "HALT",
        blank_symbol: str = BLANK,
        max_states: int = 2**10,  # 1024
    ) -> None:
        """Initialize the Logic Mill."""
        self.initial_state = initial_state
        self.halt_state = halt_state
        self.blank_symbol = blank_symbol
        self.max_states = max_states
        self.transitions = self._parse_transitions_list(
            transitions_list,
            initial_state,
            halt_state,
        )

        self._set_tape("")

    def _validate_transition(self, transition: TransitionType) -> TransitionType:
        if len(transition) != 5:  # noqa: PLR2004
            msg = (
                f"Invalid transition: {transition}. Must be in the format (currentState, currentSymbol, newState, newSymbol, moveDirection)"
            )
            raise InvalidTransitionError(
                msg,
            )

        current_state, current_symbol, new_state, new_symbol, move_direction = transition

        if move_direction not in [LEFT, RIGHT]:
            msg = f"Invalid moveDirection: {move_direction}. Must be L or R"
            raise InvalidTransitionError(
                msg,
            )

        if len(current_symbol) != 1:
            msg = f"Invalid current symbol {current_symbol}. Must be a single character."
            raise InvalidSymbolError(
                msg,
            )

        if len(new_symbol) != 1:
            msg = f"Invalid new symbol {new_symbol}. Must be a single character."
            raise InvalidSymbolError(
                msg,
            )

        return current_state, current_symbol, new_state, new_symbol, move_direction

    def _parse_transitions_list(
        self,
        transitions_list: list[TransitionType],
        initial_state: str,
        halt_state: str,
    ) -> dict[str, dict[str, tuple[str, str, str]]]:
        transitions: dict[str, dict[str, tuple[str, str, str]]] = {}
        has_halt_state = False
        for transition in transitions_list:
            current_state, current_symbol, new_state, new_symbol, move_direction = self._validate_transition(transition)

            if current_state not in transitions:
                transitions[current_state] = {}

            if current_symbol in transitions[current_state]:
                msg = f"Duplicate transition for state {current_state} and symbol {current_symbol}"
                raise InvalidTransitionError(
                    msg,
                )

            transitions[current_state][current_symbol] = (
                new_state,
                new_symbol,
                move_direction,
            )

            if new_state == halt_state:
                has_halt_state = True

        if initial_state not in transitions:
            msg = f"Initial state {initial_state} not found in the transitions"
            raise InvalidTransitionError(
                msg,
            )

        if not has_halt_state:
            msg = f"Halt state {halt_state} not found in the transitions"
            raise InvalidTransitionError(
                msg,
            )

        if len(transitions) > self.max_states:
            msg = f"Too many states: {len(transitions)}. Maximum is {self.max_states}."
            raise InvalidTransitionError(
                msg,
            )

        return transitions

    def _set_tape(self, input_tape: str) -> None:
        if " " in input_tape:
            msg = "Input tape must not contain spaces"
            raise InvalidSymbolError(
                msg,
            )

        self.tape: dict[int, str] = {i: symbol for i, symbol in enumerate(input_tape) if symbol != self.blank_symbol}
        self.head_position = 0
        self.current_state = self.initial_state

    def _render_tape(self, *, strip_blank: bool = True) -> str:
        min_pos, max_pos = self._get_min_max_pos()
        tape_str = ""
        for i in range(min_pos, max_pos + 1):
            tape_str += self.tape.get(i, self.blank_symbol)

        if strip_blank:
            tape_str = tape_str.strip(self.blank_symbol)

        return tape_str

    def _get_min_max_pos(self, window: int = 10) -> tuple[int, int]:
        """Get the minimum and maximum positions of the tape."""
        min_pos = min(self.tape.keys()) if self.tape else self.head_position - window
        max_pos = max(self.tape.keys()) if self.tape else self.head_position + window

        min_pos = min(min_pos, self.head_position - window)
        max_pos = max(max_pos, self.head_position + window)

        return min_pos, max_pos

    def _print_tape(self) -> None:
        """Print the current state of the tape."""
        min_pos, _ = self._get_min_max_pos()

        head_pos_in_window = self.head_position - min_pos

        print(self._render_tape(strip_blank=False))
        print(" " * head_pos_in_window + "^")
        print(self.current_state)
        print()

    def run(  # noqa: C901
        self,
        input_tape: str,
        max_steps: int = 1_000_000,
        *,
        verbose: bool = False,
    ) -> tuple[str, int]:
        """
        Run the Logic Mill with the given input string.

        Returns a tuple containing the final tape content and the number of steps taken.
        """
        self._set_tape(input_tape)

        if verbose:
            self._print_tape()

        steps_count = 0
        while steps_count < max_steps:
            if self.current_state == self.halt_state:
                if verbose:
                    print(f"HALTED after {steps_count} steps")
                return (self._render_tape(), steps_count)

            current_symbol = self.tape.get(self.head_position, self.blank_symbol)

            transition = self.transitions.get(self.current_state, {}).get(current_symbol)
            if not transition:
                msg = (
                    f"No transition for symbol {current_symbol or self.blank_symbol} "
                    f"in state {self.current_state} with input tape {input_tape}"
                )
                raise MissingTransitionError(
                    msg,
                )

            new_state, new_symbol, move_direction = transition

            if new_symbol == self.blank_symbol:
                if self.head_position in self.tape:
                    del self.tape[self.head_position]
            else:
                self.tape[self.head_position] = new_symbol

            self.current_state = new_state

            if move_direction == LEFT:
                self.head_position -= 1
            elif move_direction == RIGHT:
                self.head_position += 1

            steps_count += 1

            if verbose:
                self._print_tape()

        msg = f"Max steps reached ({max_steps}) with input tape {input_tape}"
        raise RuntimeError(msg)


if __name__ == "__main__":
    def normalize_quest_value(quest_value: str) -> str:
        if quest_value.isdigit():
            return quest_value.zfill(2)
        raise ValueError("Quest identifier must be numeric.")

    def resolve_quest_paths(quest_value: str) -> Path:
        quest_dir = Path(__file__).resolve().parent / "quests"
        if not quest_dir.exists():
            raise FileNotFoundError(f"Quests directory not found: {quest_dir}")

        quest_value = normalize_quest_value(quest_value)
        quest_path = quest_dir / f"quest_{quest_value}"

        if not quest_path.exists() or not quest_path.is_dir():
            raise FileNotFoundError(
                f"Quest directory not found for quest {quest_value} in {quest_dir}"
            )

        rules_path = quest_path / f"quest_{quest_value}.rules"

        if not rules_path.exists():
            raise FileNotFoundError(
                f"No rules file found for quest {quest_value} in {quest_path}"
            )

        return rules_path

    def load_quest_input_generator(quest_value: str):
        quest_dir = Path(__file__).resolve().parent / "quests"
        if not quest_dir.exists():
            raise FileNotFoundError(f"Quests directory not found: {quest_dir}")

        quest_value = normalize_quest_value(quest_value)
        quest_path = quest_dir / f"quest_{quest_value}"
        if not quest_path.exists() or not quest_path.is_dir():
            return None, None

        named_module = quest_path / f"quest_{quest_value}.py"
        generic_module = quest_path / "quest.py"

        if named_module.exists():
            module_path = named_module
        elif generic_module.exists():
            module_path = generic_module
        else:
            return None, None

        spec = importlib.util.spec_from_file_location(
            f"quest_{quest_value}.{module_path.stem}",
            module_path,
        )
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot import quest module from {module_path}")

        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)

        input_generator = getattr(module, "input_generator", None)
        if input_generator is None or not callable(input_generator):
            return None, None

        return module_path, input_generator

    parser = argparse.ArgumentParser(
        description="Run the Logic Mill with a numbered quest rules file."
    )
    parser.add_argument(
        "quest",
        help="Quest number to run (e.g. 1 for quests/01_*.rules).",
    )
    parser.add_argument(
        "--tape",
        "-t",
        default=None,
        help=(
            "Optional input tape string to run through the Logic Mill. "
            "If omitted, generated quest cases are used when available."
        ),
    )
    parser.add_argument(
        "--max-steps",
        "-m",
        type=int,
        default=1_000_000,
        help="Maximum number of execution steps before aborting.",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show tape state after each step.",
    )
    args = parser.parse_args()

    try:
        rules_path = resolve_quest_paths(args.quest)
        transition_rules = parse_transition_rules(rules_path.read_text())
        quest_module_path, input_generator = load_quest_input_generator(args.quest)
        if args.tape is None and input_generator is None:
            parser.error(
                f"No generated input cases found for quest {args.quest}. "
                "Provide --tape or add quest_{id}.py with input_generator()."
            )
        input_tape = args.tape
    except (FileNotFoundError, ValueError, ImportError) as exc:
        parser.error(str(exc))

    mill = LogicMill(transition_rules)

    if args.tape is None and input_generator is not None:
        total_cases = 0
        for input_tape, expected_value in input_generator():
            total_cases += 1
            try:
                result, steps = mill.run(
                    input_tape,
                    max_steps=args.max_steps,
                    verbose=args.verbose,
                )
            except Exception as exc:
                print("Status: FAIL")
                print(f"Error: {exc}")
                print(f"Rules file: {rules_path.name}")
                print(f"Quest module: {quest_module_path.name}")
                print(f"Input: {input_tape}")
                sys.exit(1)

            if result != expected_value:
                result_segment, expected_segment, marker = _format_tape_comparison(
                    result,
                    expected_value,
                )
                print("Status: FAIL")
                print(f"Rules file: {rules_path.name}")
                print(f"Quest module: {quest_module_path.name}")
                print(f"Input: {input_tape}")
                print(f"Result:   {result_segment}")
                print(f"Expected: {expected_segment}")
                print(f"          {marker}")
                print(f"Steps: {steps}")
                sys.exit(1)

        print("Status: PASS")
        print(f"Validated {total_cases} generated cases from {quest_module_path.name}.")
        sys.exit(0)

    try:
        result, steps = mill.run(
            input_tape,
            max_steps=args.max_steps,
            verbose=args.verbose,
        )
    except Exception as exc:
        print("Status: FAIL")
        print(f"Error: {exc}")
        print(f"Rules file: {rules_path.name}")
        print(f"Input: {input_tape}")
        sys.exit(1)

    print("Status: PASS")
    print(f"Result: {result}")
    print(f"Steps: {steps}")