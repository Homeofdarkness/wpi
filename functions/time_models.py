"""One source of truth for simulation time and reference-rate scaling."""

from __future__ import annotations

from dataclasses import dataclass


MONTHS_PER_YEAR = 12
REFERENCE_TURN_MONTHS = 6
REFERENCE_TURN_YEARS = REFERENCE_TURN_MONTHS / MONTHS_PER_YEAR

# Change this one value to select the default duration of a simulation turn.
TURN_MONTHS = 3


def month_word(months: int) -> str:
    """Return the grammatically correct Russian word for a month count."""
    remainder_100 = months % 100
    remainder_10 = months % 10
    if 11 <= remainder_100 <= 14:
        return "месяцев"
    if remainder_10 == 1:
        return "месяц"
    if 2 <= remainder_10 <= 4:
        return "месяца"
    return "месяцев"


def format_months(months: int, *, uppercase: bool = False) -> str:
    text = f"{months} {month_word(months)}"
    return text.upper() if uppercase else text


@dataclass(frozen=True, slots=True)
class TurnCalendar:
    """Validated duration and conversions for one simulation turn.

    Existing balance values are calibrated to the historical six-month turn.
    ``reference_scale`` converts those rates to any requested duration.
    """

    months: int

    def __post_init__(self) -> None:
        if isinstance(self.months, bool) or not isinstance(self.months, int):
            raise TypeError(
                "Длительность хода должна быть целым числом месяцев"
            )
        if self.months <= 0:
            raise ValueError("Длительность хода должна быть больше нуля")

    @property
    def years(self) -> float:
        return self.months / MONTHS_PER_YEAR

    @property
    def reference_scale(self) -> float:
        return self.months / REFERENCE_TURN_MONTHS

    @property
    def label(self) -> str:
        return format_months(self.months)

    @property
    def upper_label(self) -> str:
        return format_months(self.months, uppercase=True)

    def scale_flow(self, value: float) -> float:
        """Scale an amount calibrated for the six-month reference turn."""
        return float(value) * self.reference_scale

    def scale_progress(self, reference_fraction: float) -> float:
        """Compound bounded progress calibrated for one reference turn."""
        fraction = min(max(float(reference_fraction), 0.0), 1.0)
        return 1 - (1 - fraction) ** self.reference_scale

    def scale_retention(self, reference_percent: float) -> float:
        """Compound a six-month retention percentage for this duration."""
        retention = min(max(float(reference_percent) / 100, 0.0), 1.0)
        return retention**self.reference_scale * 100


def default_turn_calendar() -> TurnCalendar:
    return TurnCalendar(TURN_MONTHS)


DEFAULT_TURN_CALENDAR = default_turn_calendar()
TURN_YEARS = DEFAULT_TURN_CALENDAR.years
TURN_SCALE = DEFAULT_TURN_CALENDAR.reference_scale
MONTH_YEARS = 1 / MONTHS_PER_YEAR
