from __future__ import annotations

import re
from typing import Tuple


def parse_money(value: str) -> float:
    cleaned = value.strip()
    cleaned = cleaned.replace("MX$", "").replace("$", "").replace(" ", "")
    if "," in cleaned and "." not in cleaned:
        cleaned = cleaned.replace(",", ".")
    else:
        cleaned = cleaned.replace(",", "")
    return round(float(cleaned), 2)


def parse_eta_range(value: str) -> Tuple[int, int]:
    matches = [int(part) for part in re.findall(r"\d+", value)]
    if not matches:
        raise ValueError(f"Could not parse ETA: {value}")
    if len(matches) == 1:
        return matches[0], matches[0]
    return matches[0], matches[1]
