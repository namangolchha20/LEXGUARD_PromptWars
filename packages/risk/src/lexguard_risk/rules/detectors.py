import re
from re import Pattern

from lexguard_shared.schemas.clause import ClauseType, ExtractedClause
from lexguard_shared.schemas.risk import RiskCategory, RiskFlag

from lexguard_risk.rules.base import RiskRule, RuleHit

_PATTERN = tuple[tuple[str, str, float, RiskCategory], ...]


class PatternRule(RiskRule):
    """Regex-based rule detector with category mapping."""

    def __init__(
        self,
        flag: RiskFlag,
        patterns: _PATTERN,
        default_categories: tuple[RiskCategory, ...],
    ) -> None:
        self.flag = flag
        self._patterns = patterns
        self._default_categories = default_categories
        self._compiled: list[tuple[Pattern[str], str, str, float, RiskCategory]] = [
            (re.compile(pat, re.IGNORECASE), rule_id, desc, weight, cat)
            for pat, rule_id, desc, weight, cat in patterns
        ]

    def evaluate(self, clause: ExtractedClause) -> list[RuleHit]:
        text = clause.text
        hits: list[RuleHit] = []
        seen: set[str] = set()

        for regex, rule_id, desc, weight, category in self._compiled:
            for match in regex.finditer(text):
                matched = match.group(0).strip()
                key = f"{rule_id}:{matched[:50]}"
                if key in seen:
                    continue
                seen.add(key)
                hits.append(
                    RuleHit(
                        rule_id=rule_id,
                        rule_name=desc,
                        matched_text=matched,
                        pattern=regex.pattern,
                        weight=weight,
                        flag=self.flag,
                        categories=(category, *self._extra_categories(clause, category)),
                    )
                )
        return hits

    def _extra_categories(
        self,
        clause: ExtractedClause,
        primary: RiskCategory,
    ) -> tuple[RiskCategory, ...]:
        extras: list[RiskCategory] = []
        mapping = _CLAUSE_TYPE_CATEGORIES.get(clause.clause_type, ())
        for cat in mapping:
            if cat != primary and cat not in extras:
                extras.append(cat)
        return tuple(extras)


class OneSidedObligationRule(RiskRule):
    """Detects imbalanced obligation distribution between parties."""

    flag = RiskFlag.ONE_SIDED_OBLIGATION

    _PARTY_A = re.compile(
        r"\b(?:employee|licensee|contractor|recipient|subscriber|user|tenant|"
        r"vendor|consultant|party\s+[ab]|the\s+company)\s+shall\b",
        re.IGNORECASE,
    )
    _PARTY_B = re.compile(
        r"\b(?:employer|licensor|company|provider|discloser|landlord|"
        r"platform|owner|party\s+[ab])\s+shall\b",
        re.IGNORECASE,
    )
    _YOU_SHALL = re.compile(r"\b(?:you|your)\s+shall\b", re.IGNORECASE)
    _WE_SHALL = re.compile(r"\b(?:we|our)\s+shall\b", re.IGNORECASE)

    def evaluate(self, clause: ExtractedClause) -> list[RuleHit]:
        text = clause.text
        party_a = len(self._PARTY_A.findall(text)) + len(self._YOU_SHALL.findall(text))
        party_b = len(self._PARTY_B.findall(text)) + len(self._WE_SHALL.findall(text))
        total = party_a + party_b

        if total < 2:
            return []

        ratio = max(party_a, party_b) / total
        if ratio < 0.75:
            return []

        return [
            RuleHit(
                rule_id="ONE_SIDED_001",
                rule_name="Imbalanced obligation distribution",
                matched_text=f"{max(party_a, party_b)}/{total} obligations favor one party",
                pattern=f"obligation_ratio={ratio:.2f}",
                weight=min(0.5 + ratio * 0.4, 0.95),
                flag=self.flag,
                categories=_categories_for_clause(clause, RiskCategory.COMPLIANCE_RISK),
            )
        ]


_EXPLOITATIVE_PATTERNS: _PATTERN = (
    (
        r"\bsole\s+(?:and\s+absolute\s+)?discretion\b",
        "EXP_001",
        "Sole discretion clause",
        0.85,
        RiskCategory.COMPLIANCE_RISK,
    ),
    (
        r"\birrevocabl(?:y|e)\b",
        "EXP_002",
        "Irrevocable commitment",
        0.8,
        RiskCategory.COMPLIANCE_RISK,
    ),
    (
        r"\bwaive(?:s|d)?\s+(?:all\s+)?(?:rights|claims|remedies)\b",
        "EXP_003",
        "Broad waiver of rights",
        0.9,
        RiskCategory.COMPLIANCE_RISK,
    ),
    (
        r"\bwithout\s+(?:any\s+)?limitation\b",
        "EXP_004",
        "Unlimited scope language",
        0.75,
        RiskCategory.FINANCIAL_RISK,
    ),
    (
        r"\bat\s+(?:its|their)\s+sole\s+option\b",
        "EXP_005",
        "Unilateral option language",
        0.8,
        RiskCategory.COMPLIANCE_RISK,
    ),
    (
        r"\bunlimited\s+liability\b",
        "EXP_006",
        "Unlimited liability",
        0.95,
        RiskCategory.FINANCIAL_RISK,
    ),
    (
        r"\bforfeit(?:ure|s)?\s+(?:all|any)\b",
        "EXP_007",
        "Forfeiture language",
        0.85,
        RiskCategory.EMPLOYMENT_RISK,
    ),
)

_VAGUE_PATTERNS: _PATTERN = (
    (
        r"\breasonable(?:ly)?\b(?!\s+(?:efforts|time))",
        "VAG_001",
        "Undefined 'reasonable' standard",
        0.6,
        RiskCategory.COMPLIANCE_RISK,
    ),
    (
        r"\bappropriate\b",
        "VAG_002",
        "Undefined 'appropriate' standard",
        0.55,
        RiskCategory.COMPLIANCE_RISK,
    ),
    (
        r"\bas\s+(?:needed|required|necessary)\b",
        "VAG_003",
        "Open-ended requirement",
        0.65,
        RiskCategory.COMPLIANCE_RISK,
    ),
    (
        r"\bfrom\s+time\s+to\s+time\b",
        "VAG_004",
        "Indefinite timing",
        0.5,
        RiskCategory.COMPLIANCE_RISK,
    ),
    (
        r"\bsubstantial(?:ly)?\b(?!\s+(?:part|portion))",
        "VAG_005",
        "Undefined 'substantial'",
        0.6,
        RiskCategory.COMPLIANCE_RISK,
    ),
    (
        r"\bmaterial(?:ly)?\b(?!\s+breach)",
        "VAG_006",
        "Undefined 'material'",
        0.6,
        RiskCategory.COMPLIANCE_RISK,
    ),
    (
        r"\bincluding\s+but\s+not\s+limited\s+to\b",
        "VAG_007",
        "Non-exhaustive open list",
        0.55,
        RiskCategory.COMPLIANCE_RISK,
    ),
    (
        r"\band\s+other\s+(?:similar|related)\b",
        "VAG_008",
        "Catch-all undefined scope",
        0.65,
        RiskCategory.COMPLIANCE_RISK,
    ),
)

_HIDDEN_LIABILITY_PATTERNS: _PATTERN = (
    (
        r"\bindemnif(?:y|ies|ication)\b",
        "HID_001",
        "Indemnification obligation",
        0.8,
        RiskCategory.FINANCIAL_RISK,
    ),
    (r"\bhold\s+harmless\b", "HID_002", "Hold harmless clause", 0.85, RiskCategory.FINANCIAL_RISK),
    (
        r"\bconsequential\s+damages?\b",
        "HID_003",
        "Consequential damages exposure",
        0.75,
        RiskCategory.FINANCIAL_RISK,
    ),
    (
        r"\battorney(?:s')?\s+fees?\b",
        "HID_004",
        "Attorneys' fees shifting",
        0.65,
        RiskCategory.FINANCIAL_RISK,
    ),
    (
        r"\bliquidated\s+damages?\b",
        "HID_005",
        "Liquidated damages clause",
        0.7,
        RiskCategory.FINANCIAL_RISK,
    ),
    (
        r"\b(?:unlimited|uncapped)\s+(?:damages|liability)\b",
        "HID_006",
        "Uncapped damages",
        0.95,
        RiskCategory.FINANCIAL_RISK,
    ),
    (
        r"\bsuccessor(?:s)?\s+(?:and|&)\s+assigns?\b",
        "HID_007",
        "Binding successors language",
        0.5,
        RiskCategory.COMPLIANCE_RISK,
    ),
)

_EXCESSIVE_RESTRICTION_PATTERNS: _PATTERN = (
    (r"\bworldwide\b", "RES_001", "Worldwide geographic scope", 0.75, RiskCategory.EMPLOYMENT_RISK),
    (r"\bperpetual(?:ly)?\b", "RES_002", "Perpetual duration", 0.9, RiskCategory.EMPLOYMENT_RISK),
    (
        r"\bany\s+(?:and\s+all\s+)?business(?:es)?\b",
        "RES_003",
        "Unlimited business scope",
        0.85,
        RiskCategory.EMPLOYMENT_RISK,
    ),
    (
        r"\bnon[\s-]?compete\b",
        "RES_004",
        "Non-compete restriction",
        0.7,
        RiskCategory.EMPLOYMENT_RISK,
    ),
    (
        r"\bnon[\s-]?solicit(?:ation)?\b",
        "RES_005",
        "Non-solicitation restriction",
        0.65,
        RiskCategory.EMPLOYMENT_RISK,
    ),
    (
        r"\bclass\s+action\s+waiver\b",
        "RES_006",
        "Class action waiver",
        0.85,
        RiskCategory.ARBITRATION_RISK,
    ),
    (
        r"\bbinding\s+arbitration\b",
        "RES_007",
        "Mandatory arbitration",
        0.7,
        RiskCategory.ARBITRATION_RISK,
    ),
    (
        r"\bassign(?:able|ment)\s+(?:of\s+)?(?:all\s+)?(?:ip|intellectual\s+property)\b",
        "RES_008",
        "IP assignment",
        0.8,
        RiskCategory.IP_RISK,
    ),
)

_CLAUSE_TYPE_CATEGORIES: dict[ClauseType, tuple[RiskCategory, ...]] = {
    ClauseType.NON_COMPETE: (RiskCategory.EMPLOYMENT_RISK,),
    ClauseType.ARBITRATION: (RiskCategory.ARBITRATION_RISK,),
    ClauseType.TERMINATION: (RiskCategory.EMPLOYMENT_RISK, RiskCategory.COMPLIANCE_RISK),
    ClauseType.CONFIDENTIALITY: (RiskCategory.COMPLIANCE_RISK,),
    ClauseType.INTELLECTUAL_PROPERTY: (RiskCategory.IP_RISK,),
    ClauseType.PAYMENT: (RiskCategory.FINANCIAL_RISK,),
    ClauseType.LIABILITY: (RiskCategory.FINANCIAL_RISK,),
    ClauseType.PRIVACY: (RiskCategory.PRIVACY_RISK,),
    ClauseType.INDEMNIFICATION: (RiskCategory.FINANCIAL_RISK,),
}


def _categories_for_clause(
    clause: ExtractedClause,
    primary: RiskCategory,
) -> tuple[RiskCategory, ...]:
    mapped = _CLAUSE_TYPE_CATEGORIES.get(clause.clause_type, ())
    cats = [primary]
    for cat in mapped:
        if cat not in cats:
            cats.append(cat)
    return tuple(cats)


EXPLOITATIVE_RULE = PatternRule(
    RiskFlag.EXPLOITATIVE_LANGUAGE,
    _EXPLOITATIVE_PATTERNS,
    (RiskCategory.COMPLIANCE_RISK,),
)
VAGUE_RULE = PatternRule(RiskFlag.VAGUE_LANGUAGE, _VAGUE_PATTERNS, (RiskCategory.COMPLIANCE_RISK,))
HIDDEN_LIABILITY_RULE = PatternRule(
    RiskFlag.HIDDEN_LIABILITY,
    _HIDDEN_LIABILITY_PATTERNS,
    (RiskCategory.FINANCIAL_RISK,),
)
EXCESSIVE_RESTRICTION_RULE = PatternRule(
    RiskFlag.EXCESSIVE_RESTRICTION,
    _EXCESSIVE_RESTRICTION_PATTERNS,
    (RiskCategory.EMPLOYMENT_RISK,),
)
ONE_SIDED_RULE = OneSidedObligationRule()

ALL_RULES: list[RiskRule] = [
    EXPLOITATIVE_RULE,
    VAGUE_RULE,
    HIDDEN_LIABILITY_RULE,
    ONE_SIDED_RULE,
    EXCESSIVE_RESTRICTION_RULE,
]
