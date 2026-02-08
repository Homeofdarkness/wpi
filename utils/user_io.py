"""User I/O abstraction.

The original project mixed business logic with `input()` / `print()`.
That makes unit testing painful.

This module defines a small interface so the core engine can be tested
in isolation:

- Production uses :class:`ConsoleIO` (real stdin/stdout).
- Tests can use :class:`TestIO` (pre-programmed answers).

Keep this intentionally small; add methods only when the engine needs them.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Deque, Optional, Protocol
from collections import deque


class UserIO(Protocol):
    """Minimal I/O surface used by the core engine."""

    def print(self, message: str) -> None:
        ...

    def ask_bool(self, prompt: str, default: Optional[bool] = None) -> bool:
        ...

    def ask_float(self, prompt: str, default: Optional[float] = None) -> float:
        ...

    def request_credit(self, deficit: float) -> Optional[float]:
        """Ask the player whether they want a credit.

        Returns:
            - desired final budget (float) if credit is taken
            - None if refused or cancelled
        """
        ...


@dataclass
class ConsoleIO:
    """Console implementation (stdin/stdout)."""

    def print(self, message: str) -> None:
        print(message)

    def ask_bool(self, prompt: str, default: Optional[bool] = None) -> bool:
        while True:
            raw = input(prompt).strip().lower()
            if not raw and default is not None:
                return default
            if raw in {"1", "y", "yes", "да", "д", "true", "t"}:
                return True
            if raw in {"0", "n", "no", "нет", "н", "false", "f"}:
                return False
            self.print("Введите 1/0 (да/нет)")

    def ask_float(self, prompt: str, default: Optional[float] = None) -> float:
        while True:
            raw = input(prompt).strip()
            if not raw and default is not None:
                return float(default)
            try:
                return float(raw.replace(",", "."))
            except ValueError:
                self.print("Введите число")

    def request_credit(self, deficit: float) -> Optional[float]:
        self.print(f"У меня нет денег - не хватает {deficit}")
        try:
            take_credit = self.ask_bool("Взять кредит? 1, если да, 0 - если нет\n", default=False)
        except (KeyboardInterrupt, EOFError):
            return None

        if not take_credit:
            return None

        try:
            return self.ask_float("Введите сумму, которая в итоге будет в казне - ")
        except (KeyboardInterrupt, EOFError):
            return None


@dataclass
class TestIO:
    """Deterministic I/O for tests.

    Provide `inputs` as a list of values that will be consumed in order.
    Values may be bool/float/str.
    """

    __test__ = False  # prevent pytest from collecting as a test class

    inputs: Deque[object] = field(default_factory=deque)
    printed: list[str] = field(default_factory=list)

    def __post_init__(self):
        # Allow passing a plain list for convenience
        if not isinstance(self.inputs, deque):
            self.inputs = deque(self.inputs)

    def print(self, message: str) -> None:
        self.printed.append(str(message))

    def _pop(self) -> object:
        if not self.inputs:
            raise RuntimeError("TestIO: no more scripted inputs")
        return self.inputs.popleft()

    def ask_bool(self, prompt: str, default: Optional[bool] = None) -> bool:
        v = self._pop()
        if isinstance(v, bool):
            return v
        if isinstance(v, (int, float)):
            return bool(int(v))
        s = str(v).strip().lower()
        if not s and default is not None:
            return default
        return s in {"1", "y", "yes", "да", "true", "t"}

    def ask_float(self, prompt: str, default: Optional[float] = None) -> float:
        v = self._pop()
        if isinstance(v, (int, float)):
            return float(v)
        s = str(v).strip()
        if not s and default is not None:
            return float(default)
        return float(s.replace(",", "."))

    def request_credit(self, deficit: float) -> Optional[float]:
        # Expect: bool (take credit?) then final budget
        take = self.ask_bool("", default=False)
        if not take:
            return None
        return self.ask_float("")
