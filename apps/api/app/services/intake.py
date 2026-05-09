import re
from typing import Any

from pydantic import ValidationError

from realestate_schemas import (
    IntakeNormalizeRequest,
    NormalizedBuildSpecResponse,
    PropertyType,
    RiskTolerance,
    UserBuildSpec,
)


REQUIRED_FIELDS = ["projectName", "propertyType", "totalBudgetUsd", "units", "riskTolerance"]


def normalize_build_spec(request: IntakeNormalizeRequest) -> NormalizedBuildSpecResponse:
    values = _normalize_keys(request.structured)
    free_text = request.free_text.strip()
    assumptions: list[str] = []
    warnings: list[str] = []

    if free_text:
        extracted = _extract_from_text(free_text)
        for key, value in extracted.items():
            values.setdefault(key, value)

    values.setdefault("city", "Austin")
    values.setdefault("state", "TX")
    values.setdefault("projectName", "Austin feasibility project")
    values.setdefault("riskTolerance", RiskTolerance.MEDIUM.value)

    if "propertyType" not in values:
        values["propertyType"] = PropertyType.SINGLE_FAMILY.value
        assumptions.append("Assumed single-family residential because no property type was provided.")

    if "units" not in values:
        values["units"] = _default_units(values["propertyType"])
        assumptions.append("Assumed unit count from the selected property type.")

    missing_fields = [
        field for field in REQUIRED_FIELDS if field not in values or values[field] in ("", None)
    ]

    if "totalBudgetUsd" not in values or values.get("totalBudgetUsd") in ("", None):
        missing_fields.append("totalBudgetUsd")
    missing_fields = sorted(set(missing_fields))

    if missing_fields:
        return NormalizedBuildSpecResponse(
            spec=None,
            missing_fields=missing_fields,
            assumptions=assumptions,
            warnings=warnings,
        )

    if values["propertyType"] == PropertyType.COMMERCIAL.value:
        warnings.append("Commercial intake is captured, but MVP feasibility confidence is limited.")

    try:
        spec = UserBuildSpec(**values)
    except ValidationError as exc:
        return NormalizedBuildSpecResponse(
            spec=None,
            missing_fields=_validation_missing_fields(exc),
            assumptions=assumptions,
            warnings=warnings + ["Some intake values failed validation."],
        )

    return NormalizedBuildSpecResponse(
        spec=spec,
        missing_fields=[],
        assumptions=assumptions,
        warnings=warnings,
    )


def _normalize_keys(values: dict[str, Any]) -> dict[str, Any]:
    normalized: dict[str, Any] = {}
    for key, value in values.items():
        if value in ("", None):
            continue
        normalized[_to_camel(key)] = value
    return normalized


def _to_camel(value: str) -> str:
    parts = value.split("_")
    return parts[0] + "".join(part.capitalize() for part in parts[1:])


def _extract_from_text(text: str) -> dict[str, Any]:
    lowered = text.lower()
    extracted: dict[str, Any] = {}

    budget = _extract_money(lowered)
    if budget is not None:
        extracted["totalBudgetUsd"] = budget

    lot_sqft = _extract_number_before(lowered, ["lot sqft", "lot square feet", "sqft lot"])
    if lot_sqft is not None:
        extracted["targetLotSqft"] = lot_sqft

    building_sqft = _extract_number_before(
        lowered,
        ["house sqft", "building sqft", "home sqft", "square foot house", "sqft house"],
    )
    if building_sqft is not None:
        extracted["targetBuildingSqft"] = building_sqft

    bedrooms = _extract_number_before(lowered, ["bed", "beds", "bedroom", "bedrooms"])
    if bedrooms is not None:
        extracted["bedrooms"] = int(bedrooms)

    bathrooms = _extract_number_before(lowered, ["bath", "baths", "bathroom", "bathrooms"])
    if bathrooms is not None:
        extracted["bathrooms"] = bathrooms

    units = _extract_number_before(lowered, ["unit", "units"])
    if units is not None:
        extracted["units"] = int(units)

    if "commercial" in lowered or "retail" in lowered or "office" in lowered:
        extracted["propertyType"] = PropertyType.COMMERCIAL.value
    elif "triplex" in lowered or "duplex" in lowered:
        extracted["propertyType"] = PropertyType.DUPLEX_TRIPLEX.value
    elif "adu" in lowered or "accessory dwelling" in lowered:
        extracted["propertyType"] = PropertyType.ADU.value
    elif "single family" in lowered or "single-family" in lowered:
        extracted["propertyType"] = PropertyType.SINGLE_FAMILY.value

    if "low risk" in lowered or "conservative" in lowered:
        extracted["riskTolerance"] = RiskTolerance.LOW.value
    elif "high risk" in lowered or "aggressive" in lowered or "max yield" in lowered:
        extracted["riskTolerance"] = RiskTolerance.HIGH.value
    elif "medium risk" in lowered or "balanced" in lowered:
        extracted["riskTolerance"] = RiskTolerance.MEDIUM.value

    styles = [
        style
        for style in ["modern", "warm modern", "farmhouse", "traditional", "industrial"]
        if style in lowered
    ]
    if styles:
        extracted["stylePreferences"] = styles

    return extracted


def _extract_money(text: str) -> float | None:
    for match in re.finditer(r"\$?\s*(\d+(?:\.\d+)?)\s*(m|million|k|thousand)?", text):
        amount = float(match.group(1))
        suffix = match.group(2)
        if suffix in {"m", "million"}:
            return amount * 1_000_000
        if suffix in {"k", "thousand"}:
            return amount * 1_000
        if amount >= 10_000:
            return amount
    return None


def _extract_number_before(text: str, labels: list[str]) -> float | None:
    for label in labels:
        match = re.search(rf"(\d+(?:\.\d+)?)\s*{re.escape(label)}", text)
        if match:
            return float(match.group(1))
    return None


def _default_units(property_type: str) -> int:
    if property_type == PropertyType.ADU.value:
        return 2
    if property_type == PropertyType.DUPLEX_TRIPLEX.value:
        return 2
    return 1


def _validation_missing_fields(exc: ValidationError) -> list[str]:
    missing = []
    for error in exc.errors():
        location = error.get("loc", ())
        if location:
            missing.append(str(location[0]))
    return sorted(set(missing))
