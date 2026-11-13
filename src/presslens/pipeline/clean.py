"""Explicit row contracts; invalid records are quarantined rather than imputed."""

from collections import Counter
from datetime import date
import re

from .generate import CHANNELS, DEVICES, SESSION_FIELDS


class RowValidationError(ValueError):
    pass


def clean_sessions(rows: list[dict], article_ids: set[str]) -> tuple[list[dict], list[dict], dict]:
    accepted, rejected = [], []
    seen: set[str] = set()
    reasons: Counter = Counter()
    normalized_rows = 0
    channel_map = {value.lower(): value for value in CHANNELS}
    device_map = {value.lower(): value for value in DEVICES}
    for line, source in enumerate(rows, 2):
        try:
            missing = [field for field in SESSION_FIELDS if field not in source]
            if missing:
                raise RowValidationError("missing_field")
            row = {key: str(source[key]).strip() for key in SESSION_FIELDS}
            if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", row["session_id"]):
                raise RowValidationError("invalid_session_id")
            try:
                parsed_date = date.fromisoformat(row["date"])
                if parsed_date.isoformat() != row["date"]:
                    raise ValueError
            except ValueError as error:
                raise RowValidationError("invalid_date") from error
            if row["article_id"] not in article_ids:
                raise RowValidationError("unknown_article")
            if row["channel"].lower() not in channel_map or row["device"].lower() not in device_map:
                raise RowValidationError("invalid_dimension")
            row["channel"] = channel_map[row["channel"].lower()]
            row["device"] = device_map[row["device"].lower()]
            for name, maximum in (("engaged_seconds", 3600), ("scroll_depth", 100), ("engaged", 1), ("newsletter_signup", 1), ("subscribed", 1)):
                try:
                    row[name] = int(row[name])
                except ValueError as error:
                    raise RowValidationError("invalid_numeric_value") from error
                if row[name] < 0 or row[name] > maximum:
                    raise RowValidationError("out_of_bounds")
            expected_engaged = int(row["engaged_seconds"] >= 30 and row["scroll_depth"] >= 50)
            if row["engaged"] != expected_engaged or (row["subscribed"] or row["newsletter_signup"]) and not row["engaged"]:
                raise RowValidationError("invalid_funnel")
            if row["session_id"] in seen:
                raise RowValidationError("duplicate_session_id")
            seen.add(row["session_id"])
            normalized_rows += int(any(str(row[key]) != str(source[key]) for key in SESSION_FIELDS))
            accepted.append(row)
        except RowValidationError as error:
            reason = str(error)
            reasons[reason] += 1
            rejected.append({**source, "source_line": line, "rejection_reason": reason})
    return accepted, rejected, {
        "raw_rows": len(rows), "accepted_rows": len(accepted), "rejected_rows": len(rejected),
        "normalized_rows": normalized_rows, "rejection_reasons": dict(sorted(reasons.items())),
        "reconciled": len(rows) == len(accepted) + len(rejected),
        "acceptance_rate": len(accepted) / len(rows) if rows else 0.0,
        "policy": "Keep first valid session ID. Quarantine invalid rows; do not impute metrics.",
    }
