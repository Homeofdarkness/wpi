from abc import abstractmethod
from typing import Optional, List, Any, Dict
import re

import pydantic

from utils.input_parsers import InputParser


class StatsBase(pydantic.BaseModel):

    @abstractmethod
    def debug(self):
        raise NotImplementedError()

    @abstractmethod
    def __str__(self):
        raise NotImplementedError()

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
    def _get_regex_patterns():
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

                    # Определяем тип поля
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
        if defaults is None:
            defaults = cls._get_default_values()

        result = defaults.copy()
        patterns = cls._get_regex_patterns()

        for field_name, pattern in patterns.items():
            if field_name not in cls.model_fields:
                continue

            field_info = cls.model_fields[field_name]
            field_type = field_info.annotation

            if isinstance(pattern, list):
                result[field_name] = cls._parse_array_field(data, pattern)
            elif isinstance(pattern, str):
                result[field_name] = cls._parse_single_field(data, pattern,
                                                             field_type)
            elif isinstance(pattern, dict):
                result[field_name] = cls._parse_complex_field(data, pattern,
                                                              field_type)

        return cls(**result)

    @classmethod
    def _parse_single_field(cls, text: str, pattern: str,
                            field_type: type) -> Any:
        match = re.search(pattern, text)
        if not match:
            return None

        value = match.group(1)

        # Приведение к нужному типу
        if field_type == int:
            return int(float(value))  # Сначала float для обработки "123.0"
        elif field_type == float:
            return float(value)
        elif field_type == str:
            return value

    @classmethod
    def _parse_array_field(cls, text: str, patterns: List[str]) -> List[float]:
        """Парсинг массива значений"""
        result = []

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                result.append(float(match.group(1)))
            else:
                result.append(0.0)

        return result

    @classmethod
    def _parse_complex_field(cls, text: str, pattern_config: Dict,
                             field_type: type) -> Any:
        """Парсинг сложных полей с особой логикой"""
        if pattern_config.get('type') == 'budget_calculation':
            # Специальная обработка для расчета бюджета
            budget_match = re.search(pattern_config['pattern'], text)
            if budget_match:
                if pattern_config['field'] == 'current_budget':
                    return float(budget_match.group(2))
                elif pattern_config['field'] == 'prev_budget':
                    current = float(budget_match.group(2))
                    change = float(budget_match.group(1))
                    return current - change

        # Обычный парсинг для остальных случаев
        return cls._parse_single_field(text, pattern_config['pattern'],
                                       field_type)
