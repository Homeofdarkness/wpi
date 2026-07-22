"""Interactive parsing helpers."""

from __future__ import annotations

from collections.abc import Callable


def _field_bound(field_info, name: str):
    for constraint in field_info.metadata:
        value = getattr(constraint, name, None)
        if value is not None:
            return value
    return None


class InputParser:
    @staticmethod
    def _input_number(
        prompt: str,
        field_info,
        converter: Callable[[str], int | float],
        error_message: str,
    ) -> int | float:
        minimum = _field_bound(field_info, "ge")
        strict_minimum = _field_bound(field_info, "gt")
        maximum = _field_bound(field_info, "le")
        strict_maximum = _field_bound(field_info, "lt")
        while True:
            try:
                value = converter(input(f"{prompt}: "))
            except ValueError:
                print(error_message)
                continue
            if minimum is not None and value < minimum:
                print(f"Значение должно быть не меньше {minimum}")
                continue
            if strict_minimum is not None and value <= strict_minimum:
                print(f"Значение должно быть больше {strict_minimum}")
                continue
            if maximum is not None and value > maximum:
                print(f"Значение должно быть не больше {maximum}")
                continue
            if strict_maximum is not None and value >= strict_maximum:
                print(f"Значение должно быть меньше {strict_maximum}")
                continue
            return value

    @classmethod
    def input_int(cls, prompt: str, field_info) -> int:
        return int(
            cls._input_number(
                prompt,
                field_info,
                int,
                "Некорректный ввод. Введите целое число.",
            )
        )

    @classmethod
    def input_float(cls, prompt: str, field_info) -> float:
        return float(
            cls._input_number(
                prompt,
                field_info,
                lambda raw: float(raw.replace(",", ".")),
                "Некорректный ввод. Введите число.",
            )
        )

    @staticmethod
    def input_float_list(prompt: str) -> list[float]:
        while True:
            try:
                values = input(f"{prompt} (через пробел): ").split()
                return [float(value.replace(",", ".")) for value in values]
            except ValueError:
                print("Некорректный ввод. Введите числа через пробел.")

    @staticmethod
    def parse_data_from_str() -> str:
        lines = []
        while line := input():
            lines.append(line)
        return "\n".join(lines)
