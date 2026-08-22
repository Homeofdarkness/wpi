# Промышленность: YAML, ресурсы и эффекты

Один ход равен шести месяцам. За ход движок добывает ресурсы, выполняет
производственные правила, покрывает расход и только после этого применяет
ресурсные эффекты к остальным статам.

## Основные правила интерфейса

- группы фиксированы движком и всегда выводятся, даже если в группе нет
  ресурсов;
- alias ресурса не ограничен встроенным каталогом: допустим любой идентификатор
  вида `a_z0_9` с первой строчной буквой;
- у ресурса нет скрытого типа; добывается или производится он только потому,
  что на него ссылается соответствующее правило;
- содержимое склада является состоянием и находится в основной стате;
- вместимость склада, доступность, качество и расход являются настройками YAML;
- работников вручную распределять не нужно.

## Минимальная конфигурация

```yaml
НАСТРОЙКА ПРОМЫШЛЕННОСТИ YAML
schema_version: 2
resources:
  iron:
    name: Железо
    group: ferrous
    availability: 80
    quality: 70
    consumption: 25
    storage_capacity: 2000
extraction:
  ferrous:
    intensity: 80
    priority: 2
production: []
effects: []
КОНЕЦ НАСТРОЙКИ ПРОМЫШЛЕННОСТИ
```

Маркеры нужны консольному вводу, чтобы понять границы YAML. Внутри находится
обычный YAML, который читается через `yaml.safe_load` и проверяется Pydantic.
Неизвестное поле является ошибкой, поэтому опечатка не будет молча потеряна.

## Произвольный новый ресурс

Глобально добавлять enum или менять Python-код не нужно:

```yaml
resources:
  reinforced_glass:
    name: Армированное стекло
    group: construction
    availability: 72
    quality: 81
    consumption: 20
    storage_capacity: 300
```

Тот же ресурс сразу можно использовать в производстве:

```yaml
production:
  - id: reinforced_glass_production
    name: Производство армированного стекла
    active: true
    batches: 20
    turns: 4
    inputs:
      basic_building_materials: 2
      silicon: 0.5
    outputs:
      reinforced_glass: 1
    byproducts:
      slag: 0.1
```

`turns: null` означает бессрочное правило. Число фактически выполненных партий
ограничивается сырьём и свободной вместимостью выходных складов. После попытки
выполнения срок уменьшается на один ход.

## Добыча

Ключ после `extraction` — alias фиксированной группы или зарегистрированного
ресурса. Группа имеет приоритет при совпадении имён.

```yaml
extraction:
  ferrous:
    intensity: 80
    priority: 1
  iron:
    intensity: 100
    priority: 2
```

`intensity` — загрузка направления от 0 до 100. `priority` — относительная
доля общего бюджета ресурсодобычи. Общая мощность равна
`расходы на ресурсодобычу × 300`; движок сам делит работников и мощность между
правилами. Индивидуальное правило исключает свой ресурс из группового, поэтому
двойной добычи нет.

## Состояние ресурсов и групп

Основная промышленная стата выводит рассчитанные данные отдельно от YAML:

```text
СОСТОЯНИЕ ГРУПП
Группа                              | Ресурсов | Добыто | Дефицит
Лесное хозяйство [forestry]         | 0        | 0       | 0
Строительные материалы [construction] | 1      | 0       | 20

СОСТОЯНИЕ РЕСУРСОВ
Ресурс                                  | Склад   | Добыто | Дефицит
Армированное стекло [reinforced_glass] | 25 / 300 | 0      | 0
```

Все ресурсные числа здесь округляются до одного знака. `Склад` — текущее
количество и вместимость. `Дефицит` — неудовлетворённая часть настроенного
расхода текущего хода.

## Настраиваемые эффекты

Эффект содержит только `id`, список зависимостей, список целевых стат и одну
формулу. Одна формула применяется отдельно к каждой цели; `target` означает
текущее значение этой цели, а результат формулы — прибавку к нему.

```yaml
effects:
  - id: freshwater_population_growth
    dependencies:
      - resource: fresh_water
    targets:
      - population_growth
    formula: -target * resources.fresh_water.deficit

  - id: construction_infrastructure_expenses
    dependencies:
      - group: construction
    targets:
      - infrastructure_expenses
    formula: >-
      target * (0.4 * groups.construction.deficit -
      min(0.25 * groups.construction.surplus, 0.2))

  - id: hydrocarbons_transport
    dependencies:
      - group: hydrocarbons
    targets:
      - logistic
      - trade_efficiency
    formula: -target * groups.hydrocarbons.deficit * 0.08

  - id: glass_safety
    dependencies:
      - resource: reinforced_glass
      - group: construction
    targets:
      - industrial_accident_chance
      - population_epidemic_chance
    formula: >-
      target * (0.12 * groups.construction.deficit -
      min(0.05 * resources.reinforced_glass.surplus, 0.2))
```

Каждая объявленная зависимость предоставляет только два нормированных числа:

```text
resources.<alias>.deficit
resources.<alias>.surplus
groups.<alias>.deficit
groups.<alias>.surplus
```

Для ресурса со спросом `D`:

```text
deficit = неудовлетворённый_расход / D
surplus = остаток_на_складе / D
```

При нулевом спросе обе величины равны нулю: у движка нет масштаба, относительно
которого можно назвать склад дефицитом или профицитом. Для группы числители и
спрос суммируются по её ресурсам со спросом.

Разрешены числа, `target`, `+`, `-`, `*`, `/`, `**`, а также `min`, `max` и
`abs`. Выражение разбирается через AST без Python `eval`; доступ к файлам,
импортам, методам и необъявленным зависимостям запрещён.

Целью может быть любая существующая числовая стата из разделов `economy`,
`industry`, `agriculture`, `inner_politics` и `probabilities`. Для уникального
имени раздел не нужен:

```yaml
targets:
  - trade_efficiency
  - logistic
  - food_diversity
  - contentment
  - research_success_chance
  - industrial_accident_chance
```

Если одно имя есть в нескольких разделах, программа попросит уточнить раздел:

```yaml
targets:
  - industry.expected_wastes
  - agriculture.expected_wastes
```

Отдельно сохраняются два удобных специальных alias:

- `population_growth` — рассчитанный прирост до остальных демографических
  множителей;
- `infrastructure_expenses` — эффективные расходы на инфраструктуру.

Вторая цель не переписывает исходную стату расходов. Её результат входит в
отдельную строку `Поправка расходов от ресурсов` бюджетного отчёта и затем в
общие расходы.

Целочисленные статы округляются до целого. Ограничения конкретного поля
соблюдаются автоматически: вероятность или показатель с диапазоном `0..100`
не выйдет за этот диапазон, а казна без нижнего ограничения может остаться
отрицательной. Списки, словари, вложенные объекты и несуществующие показатели
указывать нельзя. Производные показатели изменяются после собственного
пересчёта: этап выбирается движком автоматически и не задаётся в YAML.

Если в модель страны добавить новую числовую стату, её имя сразу станет
доступно в `targets`; отдельный enum или реестр пополнять не требуется.

## Проверка загрузки и применения эффектов

`create_basic_country.py` без дополнительных аргументов создаёт страну, но не
рассчитывает ход. Поэтому основной выходной файл честно показывает, что
настроенные эффекты ещё не применялись:

```text
ЭФФЕКТЫ ПРОМЫШЛЕННОСТИ
freshwater_society:
  contentment                : ожидает расчёта хода
  food_diversity             : ожидает расчёта хода
  population_epidemic_chance : ожидает расчёта хода
```

Чтобы одновременно создать страну, рассчитать ход и увидеть результат:

```bash
uv run python create_basic_country.py --turns 1 --seed 1
```

В основной стате появится отдельный читаемый отчёт без YAML:

```text
ЭФФЕКТЫ ПРОМЫШЛЕННОСТИ
freshwater_society:
  contentment                : 89.0 -> 89.0 (+0.0)
  food_diversity             : 96.7 -> 96.7 (+0.0)
  population_epidemic_chance :  1.5 ->  1.5 (+0.0)
```

Нулевая поправка означает не потерю эффекта, а отсутствие дефицита или
профицита, на которые ссылается формула. Редактируемая формула, зависимости и
полный список целей остаются в отдельном `*_industry_settings.txt`.

## Python API

```python
from stats.industry_components import (
    ExtractionGroup,
    ResourceRegistration,
    ResourceType,
)

glass = ResourceType("reinforced_glass")
industry.register_resource(
    ResourceRegistration(
        resource=glass,
        name="Армированное стекло",
        group=ExtractionGroup.CONSTRUCTION,
        stockpile=25,
        storage_capacity=300,
        consumption_per_turn=20,
    )
)
```

Встроенные `ResourceType.IRON` и подобные константы оставлены как удобные
совместимые alias, но не образуют закрытый перечень.
