from abc import ABC, abstractmethod
from dataclasses import dataclass

from lexguard_shared.schemas.clause import ExtractedClause
from lexguard_shared.schemas.risk import RiskCategory, RiskFlag


@dataclass(frozen=True)
class RuleHit:
    rule_id: str
    rule_name: str
    matched_text: str
    pattern: str
    weight: float
    flag: RiskFlag
    categories: tuple[RiskCategory, ...]


class RiskRule(ABC):
    """Base class for deterministic risk detectors."""

    flag: RiskFlag

    @abstractmethod
    def evaluate(self, clause: ExtractedClause) -> list[RuleHit]:
        """Return all rule hits for a clause."""
