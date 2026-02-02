"""CSV parsing for manual activity uploads."""
import csv
import io

from pydantic import ValidationError

from app.schemas.integrations import CsvRowSchema

# Column name aliases (user may use different headers)
COLUMN_ALIASES = {
    "scope": ["scope"],
    "activity_type": ["activity_type", "activity type", "type"],
    "quantity": ["quantity", "amount", "value"],
    "unit": ["unit", "units"],
    "period_start": ["period_start", "period start", "start_date", "start date"],
    "period_end": ["period_end", "period end", "end_date", "end date"],
    "scope_3_category": ["scope_3_category", "scope_3_category", "scope 3 category", "category"],
    "data_quality": ["data_quality", "data quality", "quality"],
    "assumptions": ["assumptions"],
    "confidence_score": ["confidence_score", "confidence score", "confidence"],
}


def _normalize_key(key: str) -> str:
    return key.strip().lower().replace(" ", "_").replace("-", "_")


def _get_value(row: dict, canonical: str) -> str | None:
    aliases = COLUMN_ALIASES.get(canonical, [canonical])
    for alias in aliases:
        for k, v in row.items():
            if _normalize_key(k) == _normalize_key(alias) and v is not None:
                s = str(v).strip()
                return s if s else None
    return None


def parse_csv_activities(content: bytes | str) -> tuple[list[dict], list[dict]]:
    """
    Parse CSV content into validated activity rows.
    Returns (valid_rows, errors) where errors is [{row: int, error: str}, ...].
    """
    if isinstance(content, bytes):
        content = content.decode("utf-8", errors="replace")

    reader = csv.DictReader(io.StringIO(content))
    if not reader.fieldnames:
        return [], [{"row": 0, "error": "Empty or invalid CSV"}]

    valid_rows: list[dict] = []
    errors: list[dict] = []

    for i, row in enumerate(reader, start=2):
        activity_type = _get_value(row, "activity_type")
        unit = _get_value(row, "unit")
        period_start = _get_value(row, "period_start")
        period_end = _get_value(row, "period_end")

        if not activity_type:
            errors.append({"row": i, "error": "activity_type is required"})
            continue
        if not unit:
            errors.append({"row": i, "error": "unit is required"})
            continue
        if not period_start:
            errors.append({"row": i, "error": "period_start is required"})
            continue
        if not period_end:
            errors.append({"row": i, "error": "period_end is required"})
            continue

        scope_str = _get_value(row, "scope") or "3"
        try:
            scope = int(scope_str)
            if scope not in (1, 2, 3):
                raise ValueError("must be 1, 2, or 3")
        except (ValueError, TypeError):
            errors.append({"row": i, "error": "scope must be 1, 2, or 3"})
            continue

        quantity_str = _get_value(row, "quantity") or "0"
        try:
            quantity = float(quantity_str)
        except (ValueError, TypeError):
            errors.append({"row": i, "error": "quantity must be a number"})
            continue

        conf_str = _get_value(row, "confidence_score")
        confidence_score = None
        if conf_str:
            try:
                confidence_score = float(conf_str)
            except (ValueError, TypeError):
                pass

        try:
            validated = CsvRowSchema(
                scope=scope,
                activity_type=activity_type,
                quantity=quantity,
                unit=unit,
                period_start=period_start,
                period_end=period_end,
                scope_3_category=_get_value(row, "scope_3_category") or None,
                data_quality=_get_value(row, "data_quality") or "manual",
                assumptions=_get_value(row, "assumptions") or None,
                confidence_score=confidence_score,
            )
            valid_rows.append(validated.model_dump())
        except ValidationError as e:
            err_msg = e.errors()[0].get("msg", str(e)) if e.errors() else str(e)
            errors.append({"row": i, "error": str(err_msg)})

    return valid_rows, errors
