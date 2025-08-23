from functions.base import BaseInMoveFunctions


class AtteriumStatsFunctions(BaseInMoveFunctions):

    @staticmethod
    def calculate_trade_income(technology_percent: float,
                               resources_percent: float,
                               trade_potential: float,
                               trade_usage: int, trade_efficiency: float,
                               trade_wastes: float) -> float:
        pure_income = min(technology_percent, 100) * 5 + min(
            resources_percent, 750)
        efficiency_factor = (
                trade_efficiency / 100) if trade_usage <= trade_potential else (
                trade_efficiency / 200)
        base_income = (
            trade_usage / 48 if trade_usage <= trade_potential else trade_usage / 78)

        return base_income + pure_income * efficiency_factor - trade_wastes

    @staticmethod
    def calculate_society_decline(
            contentment: int,
            government_trust: float,
            many_children_traditions: int,
            sexual_asceticism: float,
            egocentrism_development: float,
            capitalism_decay: float,
            education_level: int,
            erudition_will: int,
            cultural_level: int,
            violence_tendency: float,
            unemployment_rate: float,
            grace_of_the_highest: int,
            commitment_to_cause: int,
            departure_from_truths: int,
            equality: float
    ) -> float:
        """Считает упадок общества"""
        positive_factors = (
                contentment * 0.04 +
                government_trust * 0.19 +
                many_children_traditions * 0.04 +
                sexual_asceticism * 0.3 +
                education_level * 0.04 +
                erudition_will * 0.074 +
                cultural_level * 0.04 +
                grace_of_the_highest * 0.8 +
                commitment_to_cause * 0.14 +
                equality * 0.16
        )

        negative_factors = (
                violence_tendency * 0.3 +  # + 2
                egocentrism_development * 0.15 +
                capitalism_decay * 0.2 +
                unemployment_rate * 0.15 +
                departure_from_truths * 0.9
        )

        societal_decline = max(0.0, negative_factors - positive_factors)
        societal_decline = min(societal_decline, 100)

        return round(societal_decline, 2)
