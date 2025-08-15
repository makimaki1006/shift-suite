from dataclasses import dataclass
from typing import List
import datetime as dt


@dataclass
class NeedCalculationConfig:
    """Need calculation settings."""

    include_zero_days: bool = True
    auto_holiday_detection: bool = False
    statistic_method: str = "中央値"
    remove_outliers: bool = True
    iqr_multiplier: float = 1.5
    adjustment_factor: float = 1.0
    explicit_holidays: List[dt.date] | None = None
    validation_enabled: bool = True
    tolerance_factor: float = 3.0

    def __post_init__(self) -> None:
        if self.explicit_holidays is None:
            self.explicit_holidays = []

    def get_holidays_set(self) -> set[dt.date]:
        return set(self.explicit_holidays)

    def validate(self) -> List[str]:
        errors: List[str] = []
        if self.statistic_method not in ["中央値", "平均値", "25パーセンタイル"]:
            errors.append("statistic_method must be one of 中央値, 平均値, 25パーセンタイル")
        if self.tolerance_factor <= 0:
            errors.append("tolerance_factor must be positive")
        if self.adjustment_factor <= 0:
            errors.append("adjustment_factor must be positive")
        return errors
