#!/usr/bin/env python3
import re
from typing import Optional, Tuple, List

MONTH_NAME_ALTS = (
    r"Jan(?:uary)?",
    r"Feb(?:ruary)?",
    r"Mar(?:ch)?",
    r"Apr(?:il)?",
    r"May",
    r"Jun(?:e)?",
    r"Jul(?:y)?",
    r"Aug(?:ust)?",
    r"Sep(?:t|tember)?",
    r"Oct(?:ober)?",
    r"Nov(?:ember)?",
    r"Dec(?:ember)?",
)
MONTH_NAME_REGEX = r"(?:" + r"|".join(MONTH_NAME_ALTS) + r")\.?"

# Precompile regex patterns (ordered by specificity)
PATTERNS: List[Tuple[re.Pattern, str]] = [
    # MM/DD/YYYY or M/D/YY
    (re.compile(r"\b(?P<m>\d{1,2})/(?P<d>\d{1,2})/(?P<y>\d{2,4})\b"), "slash_mdy"),
    # YYYY-MM-DD
    (re.compile(r"\b(?P<y>\d{4})-(?P<m>\d{1,2})-(?P<d>\d{1,2})\b"), "dash_ymd"),
    # DD-MM-YYYY (assume dash-delimited is day-first if not YYYY-...)
    (re.compile(r"\b(?P<d>\d{1,2})-(?P<m>\d{1,2})-(?P<y>\d{2,4})\b"), "dash_dmy"),
    # MonthName DD, YYYY or MonthName DD YYYY
    (re.compile(r"\b(?P<month_name>" + MONTH_NAME_REGEX + r")\s+(?P<d>\d{1,2})(?:st|nd|rd|th)?(?:,)?\s+(?P<y>\d{2,4})\b", re.IGNORECASE), "mname_d_y"),
    # DD MonthName YYYY
    (re.compile(r"\b(?P<d>\d{1,2})(?:st|nd|rd|th)?\s+(?P<month_name>" + MONTH_NAME_REGEX + r")\s+(?P<y>\d{2,4})\b", re.IGNORECASE), "d_mname_y"),
    # MonthName YYYY (day defaults to 1)
    (re.compile(r"\b(?P<month_name>" + MONTH_NAME_REGEX + r")\s+(?P<y>\d{4})\b", re.IGNORECASE), "mname_y"),
    # MM/YY or M/YY (month/year, day defaults to 1)
    (re.compile(r"\b(?P<m>\d{1,2})/(?P<y>\d{2,4})\b"), "slash_my"),
    # YYYY only (defaults to Jan 1)
    (re.compile(r"\b(?P<y>\d{4})\b"), "y_only"),
]

MONTH_LOOKUP = {
    "jan": 1, "january": 1,
    "feb": 2, "february": 2,
    "mar": 3, "march": 3,
    "apr": 4, "april": 4,
    "may": 5,
    "jun": 6, "june": 6,
    "jul": 7, "july": 7,
    "aug": 8, "august": 8,
    "sep": 9, "sept": 9, "september": 9,
    "oct": 10, "october": 10,
    "nov": 11, "november": 11,
    "dec": 12, "december": 12,
}

def normalize_year(year_text: str) -> int:
    year_int = int(year_text)
    if len(year_text) == 2:
        return 1900 + year_int
    return year_int


def parse_month_name(text: str) -> Optional[int]:
    clean = text.strip().lower().rstrip('.')
    return MONTH_LOOKUP.get(clean)


def format_date(y: int, m: int, d: int) -> str:
    return f"{y:04d}-{m:02d}-{d:02d}"


def choose_first_match(text: str) -> Optional[Tuple[int, int, int]]:
    candidates: List[Tuple[int, int, int, int]] = []  # (start_idx, order, y, m, d)

    for order, (pattern, kind) in enumerate(PATTERNS):
        for m in pattern.finditer(text):
            y: Optional[int] = None
            month: Optional[int] = None
            day: Optional[int] = None

            if kind in ("slash_mdy", "dash_ymd", "dash_dmy", "slash_my", "y_only"):
                if 'y' in m.groupdict() and m.group('y') is not None:
                    y = normalize_year(m.group('y'))

            if kind == "slash_mdy":
                month = int(m.group('m'))
                day = int(m.group('d'))
            elif kind == "dash_ymd":
                month = int(m.group('m'))
                day = int(m.group('d'))
            elif kind == "dash_dmy":
                day = int(m.group('d'))
                month = int(m.group('m'))
            elif kind == "mname_d_y":
                y = normalize_year(m.group('y'))
                month_name = m.group('month_name')
                month = parse_month_name(month_name)
                day = int(m.group('d'))
            elif kind == "d_mname_y":
                y = normalize_year(m.group('y'))
                month_name = m.group('month_name')
                month = parse_month_name(month_name)
                day = int(m.group('d'))
            elif kind == "mname_y":
                y = int(m.group('y'))
                month_name = m.group('month_name')
                month = parse_month_name(month_name)
                day = 1
            elif kind == "slash_my":
                month = int(m.group('m'))
                day = 1
            elif kind == "y_only":
                month = 1
                day = 1

            if y is None or month is None or day is None:
                continue

            # Basic range validation
            if not (1 <= month <= 12):
                continue
            if not (1 <= day <= 31):
                continue

            candidates.append((m.start(), order, y, month, day))

    if not candidates:
        return None

    candidates.sort(key=lambda t: (t[0], t[1]))
    _, _, y, month, day = candidates[0]
    return y, month, day


def extract_first_normalized_date(text: str) -> Optional[str]:
    parsed = choose_first_match(text)
    if parsed is None:
        return None
    y, m, d = parsed
    return format_date(y, m, d)


def process_file(input_path: str, output_path: str) -> None:
    with open(input_path, 'r', encoding='utf-8') as fin, open(output_path, 'w', encoding='utf-8') as fout:
        for raw_line in fin:
            stripped = raw_line.rstrip('\n')
            if not stripped:
                continue
            if '\t' not in stripped:
                continue
            idx_text, content = stripped.split('\t', 1)
            normalized = extract_first_normalized_date(content)
            if normalized is None:
                continue
            fout.write(f"{idx_text}\t{normalized}\n")


if __name__ == "__main__":
    INPUT_FILE = "/workspace/dates.txt"
    OUTPUT_FILE = "/workspace/assignment_your_surname.txt"
    process_file(INPUT_FILE, OUTPUT_FILE)
    print(f"Wrote normalized dates to {OUTPUT_FILE}")