#!/usr/bin/env python3
"""
Fetch Engpassanalyse (bottleneck analysis) data from Bundesagentur für Arbeit.

The Engpassanalyse identifies occupations with labor shortages or surpluses
in Germany, updated quarterly by the Federal Employment Agency.

Source: https://statistik.arbeitsagentur.de/DE/Navigation/Statistiken/
        Fachstatistiken/Gemeldete-Arbeitsstellen/Engpassanalyse.html

The Engpassanalyse uses an indicator system based on:
- Vacancy duration (Vakanzzeit)
- Vacancy-to-unemployment ratio (Arbeitslosen-Stellen-Relation)
- Professional migration potential
- Wage development

Output: ../data/outlook_de.json

Usage:
    python fetch_outlook.py --from-file engpassanalyse_2024.xlsx

    # The BA publishes Engpassanalyse as downloadable Excel files
    # Download from: https://statistik.arbeitsagentur.de/
"""

import argparse
import csv
import json
import os
import sys

try:
    import httpx
except ImportError:
    print("Install httpx: pip install httpx")
    sys.exit(1)


# Engpass indicator mapping
ENGPASS_CATEGORIES = {
    "Engpassberuf": {
        "de": "Starker Fachkräftemangel",
        "en": "Severe Shortage",
        "outlook_pct": 12,
    },
    "Engpass angedeutet": {
        "de": "Fachkräftemangel",
        "en": "Shortage",
        "outlook_pct": 6,
    },
    "kein Engpass": {
        "de": "Ausgeglichen",
        "en": "Balanced",
        "outlook_pct": 2,
    },
    "Überhang angedeutet": {
        "de": "Leichter Überhang",
        "en": "Moderate Surplus",
        "outlook_pct": -4,
    },
    "Überhang": {
        "de": "Starker Überhang",
        "en": "Strong Surplus",
        "outlook_pct": -8,
    },
}


def parse_from_file(filepath):
    """Parse Engpassanalyse from downloaded Excel/CSV file."""
    outlook = {}

    if filepath.endswith(".xlsx"):
        try:
            import openpyxl
        except ImportError:
            print("Install openpyxl: pip install openpyxl")
            sys.exit(1)

        wb = openpyxl.load_workbook(filepath, read_only=True)

        # The Engpassanalyse typically has multiple sheets
        for ws in wb.worksheets:
            rows = list(ws.iter_rows(values_only=True))
            if not rows:
                continue

            # Find header row
            header_idx = None
            code_col = None
            engpass_col = None
            vakanz_col = None

            for i, row in enumerate(rows):
                if not row:
                    continue
                for j, cell in enumerate(row):
                    if cell and isinstance(cell, str):
                        cell_lower = cell.lower()
                        if "kldb" in cell_lower or "beruf" in cell_lower and "code" in cell_lower:
                            header_idx = i
                            code_col = j
                        if "engpass" in cell_lower or "bewertung" in cell_lower:
                            engpass_col = j
                        if "vakanz" in cell_lower:
                            vakanz_col = j

                if header_idx is not None:
                    break

            if header_idx is None or code_col is None:
                continue

            for row in rows[header_idx + 1:]:
                if not row or not row[code_col]:
                    continue
                code = str(row[code_col]).strip()

                # Determine engpass status
                engpass_raw = ""
                if engpass_col is not None and len(row) > engpass_col:
                    engpass_raw = str(row[engpass_col] or "").strip()

                # Try to map to our categories
                category = None
                for key, cat in ENGPASS_CATEGORIES.items():
                    if key.lower() in engpass_raw.lower():
                        category = cat
                        break

                if category is None:
                    # Infer from Vakanzzeit if available
                    if vakanz_col is not None and len(row) > vakanz_col:
                        try:
                            vakanz = float(str(row[vakanz_col]).replace(",", "."))
                            if vakanz > 180:
                                category = ENGPASS_CATEGORIES["Engpassberuf"]
                            elif vakanz > 120:
                                category = ENGPASS_CATEGORIES["Engpass angedeutet"]
                            elif vakanz > 60:
                                category = ENGPASS_CATEGORIES["kein Engpass"]
                            else:
                                category = ENGPASS_CATEGORIES["Überhang angedeutet"]
                        except ValueError:
                            category = ENGPASS_CATEGORIES["kein Engpass"]
                    else:
                        category = ENGPASS_CATEGORIES["kein Engpass"]

                outlook[code] = {
                    "outlook_desc_de": category["de"],
                    "outlook_desc_en": category["en"],
                    "outlook_pct": category["outlook_pct"],
                    "engpass_raw": engpass_raw,
                }

        wb.close()

    elif filepath.endswith(".csv"):
        with open(filepath, encoding="utf-8") as f:
            sample = f.read(2000)
            f.seek(0)
            delimiter = ";" if ";" in sample else ","

            reader = csv.reader(f, delimiter=delimiter)
            header = next(reader, None)

            code_col = 0
            engpass_col = -1
            if header:
                for i, h in enumerate(header):
                    h_lower = h.lower()
                    if "kldb" in h_lower or "code" in h_lower:
                        code_col = i
                    if "engpass" in h_lower or "bewertung" in h_lower:
                        engpass_col = i

            for row in reader:
                if len(row) <= code_col:
                    continue
                code = row[code_col].strip()
                engpass_raw = row[engpass_col].strip() if engpass_col >= 0 and len(row) > engpass_col else ""

                category = ENGPASS_CATEGORIES.get("kein Engpass")
                for key, cat in ENGPASS_CATEGORIES.items():
                    if key.lower() in engpass_raw.lower():
                        category = cat
                        break

                outlook[code] = {
                    "outlook_desc_de": category["de"],
                    "outlook_desc_en": category["en"],
                    "outlook_pct": category["outlook_pct"],
                }

    print(f"  Parsed {len(outlook)} outlook entries from {filepath}")
    return outlook


def main():
    parser = argparse.ArgumentParser(description="Fetch German Engpassanalyse data")
    parser.add_argument("--from-file", required=True,
                       help="Parse from downloaded Engpassanalyse Excel/CSV file")
    args = parser.parse_args()

    outlook = parse_from_file(args.from_file)

    # Save
    os.makedirs("../data", exist_ok=True)
    with open("../data/outlook_de.json", "w", encoding="utf-8") as f:
        json.dump(outlook, f, ensure_ascii=False, indent=2)

    # Stats
    by_status = {}
    for v in outlook.values():
        desc = v["outlook_desc_de"]
        by_status[desc] = by_status.get(desc, 0) + 1

    print(f"\nSaved {len(outlook)} entries to ../data/outlook_de.json")
    print("\nOutlook distribution:")
    for status, count in sorted(by_status.items(), key=lambda x: -x[1]):
        print(f"  {status}: {count}")


if __name__ == "__main__":
    main()
