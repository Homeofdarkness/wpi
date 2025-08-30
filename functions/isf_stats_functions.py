from functions.base import BaseInMoveFunctions


class IsfStatsFunctions(BaseInMoveFunctions):

    @staticmethod
    def calculate_society_decline(
            contentment: int,
            government_trust: float,
            many_children_traditions: int,
            sexual_asceticism: float,
            egocentrism_development: float,
            education_level: int,
            erudition_will: int,
            cultural_level: int,
            violence_tendency: float,
            unemployment_rate: float,
            grace_of_the_silver: int,
            commitment_to_cause: int,
            departure_from_truths: int,
            imperial_court_power: float,
            separatism_of_the_highest: int
    ) -> float:
        """Считает упадок общества"""
        positive_factors = (
                contentment * 0.04 +
                government_trust * 0.19 +
                many_children_traditions * 0.04 +
                sexual_asceticism * 0.3 +
                education_level * 0.05 +
                erudition_will * 0.075 +
                cultural_level * 0.05 +
                grace_of_the_silver * 0.8 +
                commitment_to_cause * 0.15 +
                imperial_court_power * 0.15
        )

        negative_factors = (
            violence_tendency * 0.3 +  # + 2
            egocentrism_development * 0.15 +
            unemployment_rate * 0.15 +
            departure_from_truths * 0.9,
            separatism_of_the_highest * 0.7
        )

        societal_decline = max(0.0, negative_factors - positive_factors)
        societal_decline = min(societal_decline, 100)

        return round(societal_decline, 2)
