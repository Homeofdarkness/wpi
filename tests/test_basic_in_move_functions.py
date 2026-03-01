import random

from tests.factories import make_basic_bundle


def test_calculate_workers_count():
    random.seed(10)
    b = make_basic_bundle(budget=1000.0)
    population_count = b.economy.population_count

    from functions.basic_in_move_functions import BasicInMoveFunctions
    print(BasicInMoveFunctions.calculate_workers_count(
        population_count,

    )
    )
