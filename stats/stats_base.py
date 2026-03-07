from abc import ABC, abstractmethod
from typing import Optional, List, Any, Dict

import pydantic

from stats.pretty import parse_pretty_text, render_pretty, PrettyLayoutSpec
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
    def _get_field_groups():
        raise NotImplementedError()

    @staticmethod
    @abstractmethod
    def _get_field_names():
        raise NotImplementedError()

    @staticmethod
    @abstractmethod
    def _get_pretty_layout() -> PrettyLayoutSpec:
        raise NotImplementedError()

    @staticmethod
    def _get_default_values() -> Dict:
        return {}

    @classmethod
    def from_user_input(cls,
                        greeting_text: Optional[str] = None) -> 'StatsBase':
        if greeting_text:
            print(greeting_text)

        fields = cls.model_fields
        data = {}

        field_groups = cls._get_field_groups()
        field_names = cls._get_field_names()

        for group_name, field_list in field_groups.items():
            print(f"\n--- {group_name} ---")
            for field_name in field_list:
                if field_name in fields:
                    field_info = fields[field_name]
                    prompt = field_names.get(field_name, field_name)

                    if field_info.annotation == int:
                        data[field_name] = InputParser.input_int(prompt,
                                                                 field_info)
                    elif field_info.annotation == float:
                        data[field_name] = InputParser.input_float(prompt,
                                                                   field_info)
                    elif field_info.annotation == List[float]:
                        data[field_name] = InputParser.input_float_list(prompt)
                    else:
                        data[field_name] = input(f'{prompt}: ')

        return cls(**data)

    @classmethod
    def from_stats_text(cls, data: str,
                        defaults: Dict[str, Any] = None) -> 'StatsBase':
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
