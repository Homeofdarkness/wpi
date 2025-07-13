from typing import Optional, List


class InputParser:

    @staticmethod
    def input_int(prompt: str, field_info) -> Optional[int]:
        while True:
            try:
                value = int(input(f'{prompt}: '))
                if hasattr(field_info,
                           'ge') and field_info.ge is not None and value < field_info.ge:
                    print(f"Значение должно быть не меньше {field_info.ge}")
                    continue
                if hasattr(field_info,
                           'le') and field_info.le is not None and value > field_info.le:
                    print(f"Значение должно быть не больше {field_info.le}")
                    continue
                return value
            except ValueError:
                print("Некорректный ввод. Введите целое число.")

    @staticmethod
    def input_float(prompt: str, field_info) -> Optional[float]:
        """Безопасный ввод числа с плавающей точкой"""
        while True:
            try:
                value = float(input(f'{prompt}: '))
                # Проверяем ограничения из Field
                if hasattr(field_info,
                           'ge') and field_info.ge is not None and value < field_info.ge:
                    print(f"Значение должно быть не меньше {field_info.ge}")
                    continue
                if hasattr(field_info,
                           'le') and field_info.le is not None and value > field_info.le:
                    print(f"Значение должно быть не больше {field_info.le}")
                    continue
                return value
            except ValueError:
                print("Некорректный ввод. Введите число.")

    @staticmethod
    def input_float_list(prompt: str) -> List[float]:
        """Ввод списка чисел через пробел"""
        while True:
            try:
                values = input(f'{prompt} (через пробел): ').split()
                return [float(v) for v in values]
            except ValueError:
                print("Некорректный ввод. Введите числа через пробел.")

    @staticmethod
    def parse_data_from_str() -> str:
        lines = []
        while True:
            line = input()
            if not line:
                break
            lines.append(line)

        text = '\n'.join(lines)
        return text
