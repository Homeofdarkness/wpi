from abc import ABC, abstractmethod
from typing import Any, get_origin

import pydantic

from stats.pretty import PrettyLayoutSpec, parse_pretty_text, render_pretty
from utils.input_parsers import InputParser


class StatsBase(pydantic.BaseModel, ABC):
    def model_post_init(self, __context) -> None:
        self.recalculate_derived_fields()

    def recalculate_derived_fields(self) -> None:
        """Пересчитывает производные поля модели после инициализации."""
        return None

    def render_pretty(self, *, debug: bool = False) -> str:
        return render_pretty(self, self._get_pretty_layout(), debug=debug)

    def debug(self):
        return self.render_pretty(debug=True)

    def __str__(self):
        return self.render_pretty(debug=False)

    @staticmethod
    @abstractmethod
    def _get_pretty_layout() -> PrettyLayoutSpec:
        raise NotImplementedError()

    @staticmethod
    def _get_default_values() -> dict:
        return {}

    @classmethod
    def from_user_input(cls, greeting_text: str | None = None) -> "StatsBase":
        if greeting_text:
            print(greeting_text)

        fields = cls.model_fields
        data = {}
        labels: dict[str, list[str]] = {}
        for spec in cls._get_pretty_layout().fields.values():
            if spec.field_name is not None and not spec.read_only:
                labels.setdefault(spec.field_name, []).append(spec.label)

        for field_name, field_info in fields.items():
            if not field_info.is_required():
                continue
            prompt = " / ".join(dict.fromkeys(labels.get(field_name, [])))
            prompt = prompt or field_name
            if field_info.annotation is int:
                data[field_name] = InputParser.input_int(prompt, field_info)
            elif field_info.annotation is float:
                data[field_name] = InputParser.input_float(prompt, field_info)
            elif get_origin(field_info.annotation) is list or (
                field_info.annotation is list
            ):
                data[field_name] = InputParser.input_float_list(prompt)
            else:
                data[field_name] = input(f"{prompt}: ")

        return cls(**data)

    @classmethod
    def from_stats_text(
        cls, data: str, defaults: dict[str, Any] = None
    ) -> "StatsBase":
        merged_defaults = cls._get_default_values().copy()
        if defaults:
            merged_defaults.update(defaults)

        parsed = parse_pretty_text(
            data,
            cls._get_pretty_layout(),
            cls.model_fields,
            defaults=merged_defaults,
        )
        return cls(**parsed)
