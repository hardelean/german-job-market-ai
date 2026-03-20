#!/usr/bin/env python3
"""
Fetch the KldB 2010 (Klassifikation der Berufe) occupation classification.

The KldB 2010 is Germany's national occupation classification system,
maintained by the Bundesagentur für Arbeit (Federal Employment Agency).

Data source: Bundesagentur für Arbeit - KldB 2010
API: https://rest.arbeitsagentur.de/infosysbub/kldb/pc/v1/kldb

This script requires an API key from the Bundesagentur's developer portal:
https://web.arbeitsagentur.de/portal/metasuche/suche/information/BERUFENET

Alternatively, the KldB 2010 can be downloaded as a complete classification
from: https://statistik.arbeitsagentur.de/DE/Navigation/Grundlagen/Klassifikationen/Klassifikation-der-Berufe/Klassifikation-der-Berufe-Nav.html

Output: ../data/kldb_occupations.json

Usage:
    # With API key:
    export BA_API_KEY=your_key_here
    python fetch_kldb.py

    # Or parse from downloaded classification file:
    python fetch_kldb.py --from-file kldb2010_complete.xlsx
"""

import argparse
import json
import os
import re
import sys
import time

try:
    import httpx
except ImportError:
    print("Install httpx: pip install httpx")
    sys.exit(1)


# KldB 2010 Berufsbereiche (top-level areas, 1-digit)
BERUFSBEREICHE = {
    "0": {"de": "Militär", "en": "Military"},
    "1": {"de": "Land-, Forst- und Tierwirtschaft und Gartenbau", "en": "Agriculture, Forestry, Animal Husbandry and Horticulture"},
    "2": {"de": "Rohstoffgewinnung, Produktion und Fertigung", "en": "Raw Materials Extraction, Production and Manufacturing"},
    "3": {"de": "Bau, Architektur, Vermessung und Gebäudetechnik", "en": "Construction, Architecture, Surveying and Building Technology"},
    "4": {"de": "Naturwissenschaft, Geografie und Informatik", "en": "Natural Sciences, Geography and IT"},
    "5": {"de": "Verkehr, Logistik, Schutz und Sicherheit", "en": "Transport, Logistics, Security and Safety"},
    "6": {"de": "Kaufmännische Dienstleistungen, Warenhandel, Vertrieb, Hotel und Tourismus", "en": "Commercial Services, Trade, Sales, Hotel and Tourism"},
    "7": {"de": "Unternehmensorganisation, Buchhaltung, Recht und Verwaltung", "en": "Corporate Organisation, Accounting, Law and Administration"},
    "8": {"de": "Gesundheit, Soziales, Lehre und Erziehung", "en": "Health, Social Work, Teaching and Education"},
    "9": {"de": "Sprach-, Literatur-, Geistes-, Gesellschafts- und Wirtschaftswissenschaften, Medien, Kunst, Kultur und Gestaltung", "en": "Humanities, Media, Arts, Culture and Design"},
}

# KldB 2010 Anforderungsniveaus (qualification levels, 5th digit)
ANFORDERUNGSNIVEAUS = {
    "1": {"de": "Helfer (keine formale Ausbildung)", "en": "No formal qualification (Helfer)"},
    "2": {"de": "Fachkraft (Ausbildung)", "en": "Vocational training (Fachkraft)"},
    "3": {"de": "Spezialist (Meister/Techniker/Fachwirt)", "en": "Master craftsman / Technician (Spezialist)"},
    "4": {"de": "Experte (Hochschulabschluss)", "en": "University degree (Experte)"},
}

# Bundesagentur REST API base
BA_API_BASE = "https://rest.arbeitsagentur.de/infosysbub/kldb/pc/v1"


def fetch_from_api(api_key):
    """Fetch KldB occupations from Bundesagentur REST API."""
    client = httpx.Client(timeout=30)
    headers = {
        "X-API-Key": api_key,
        "Accept": "application/json",
    }

    occupations = []

    # Fetch all 5-digit KldB codes
    # The API supports hierarchical browsing: area → group → subgroup → occupation
    print("Fetching KldB 2010 classification from Bundesagentur API...")

    for area_code, area_names in BERUFSBEREICHE.items():
        print(f"  Area {area_code}: {area_names['de']}...")

        try:
            # Get all occupations in this area
            response = client.get(
                f"{BA_API_BASE}/kldb",
                headers=headers,
                params={"codenr": f"{area_code}*", "level": "5"},
            )
            response.raise_for_status()
            data = response.json()

            items = data.get("_embedded", {}).get("kldbList", [])
            for item in items:
                code = item.get("codenr", "")
                if len(code) == 5:
                    # Get qualification level from 5th digit
                    qual_level = code[-1]
                    anf = ANFORDERUNGSNIVEAUS.get(qual_level, {})

                    occupations.append({
                        "kldb_code": code,
                        "title_de": item.get("kurzBezeichnung", ""),
                        "title_en": "",  # Will need translation
                        "category_de": area_names["de"],
                        "category_en": area_names["en"],
                        "education_de": anf.get("de", ""),
                        "education_en": anf.get("en", ""),
                        "education_level": int(qual_level) if qual_level.isdigit() else 0,
                        "berufsbereich": area_code,
                    })

            time.sleep(0.5)  # Rate limiting

        except Exception as e:
            print(f"    Error fetching area {area_code}: {e}")

    client.close()
    return occupations


def fetch_from_file(filepath):
    """Parse KldB classification from a downloaded Excel/CSV file."""
    occupations = []

    if filepath.endswith(".xlsx"):
        try:
            import openpyxl
        except ImportError:
            print("Install openpyxl: pip install openpyxl")
            sys.exit(1)

        wb = openpyxl.load_workbook(filepath, read_only=True)
        ws = wb.active
        rows = list(ws.iter_rows(values_only=True))

        # Try to find the header row
        header_idx = 0
        for i, row in enumerate(rows):
            if row and any("KldB" in str(c) or "Code" in str(c) for c in row if c):
                header_idx = i
                break

        for row in rows[header_idx + 1:]:
            code = str(row[0]).strip() if row[0] else ""
            title = str(row[1]).strip() if len(row) > 1 and row[1] else ""

            if len(code) == 5 and code.isdigit() and title:
                area_code = code[0]
                qual_level = code[-1]
                area_names = BERUFSBEREICHE.get(area_code, {"de": "Sonstige", "en": "Other"})
                anf = ANFORDERUNGSNIVEAUS.get(qual_level, {})

                occupations.append({
                    "kldb_code": code,
                    "title_de": title,
                    "title_en": "",
                    "category_de": area_names["de"],
                    "category_en": area_names["en"],
                    "education_de": anf.get("de", ""),
                    "education_en": anf.get("en", ""),
                    "education_level": int(qual_level) if qual_level.isdigit() else 0,
                    "berufsbereich": area_code,
                })

        wb.close()

    elif filepath.endswith(".csv"):
        import csv
        with open(filepath, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                code = row.get("code", row.get("Code", row.get("KldB", "")))
                title = row.get("title", row.get("Bezeichnung", row.get("title_de", "")))
                if len(code) == 5 and code.isdigit() and title:
                    area_code = code[0]
                    qual_level = code[-1]
                    area_names = BERUFSBEREICHE.get(area_code, {"de": "Sonstige", "en": "Other"})
                    anf = ANFORDERUNGSNIVEAUS.get(qual_level, {})

                    occupations.append({
                        "kldb_code": code,
                        "title_de": title,
                        "title_en": "",
                        "category_de": area_names["de"],
                        "category_en": area_names["en"],
                        "education_de": anf.get("de", ""),
                        "education_en": anf.get("en", ""),
                        "education_level": int(qual_level) if qual_level.isdigit() else 0,
                        "berufsbereich": area_code,
                    })

    return occupations


def slugify(text):
    text = text.lower()
    text = re.sub(r'[äÄ]', 'ae', text)
    text = re.sub(r'[öÖ]', 'oe', text)
    text = re.sub(r'[üÜ]', 'ue', text)
    text = re.sub(r'[ß]', 'ss', text)
    text = re.sub(r'[^a-z0-9]+', '-', text)
    return text.strip('-')


def main():
    parser = argparse.ArgumentParser(description="Fetch KldB 2010 occupation classification")
    parser.add_argument("--from-file", help="Parse from downloaded Excel/CSV file instead of API")
    args = parser.parse_args()

    if args.from_file:
        occupations = fetch_from_file(args.from_file)
    else:
        api_key = os.environ.get("BA_API_KEY")
        if not api_key:
            print("Error: Set BA_API_KEY environment variable or use --from-file")
            print("Get an API key from: https://web.arbeitsagentur.de/portal/metasuche/suche/information/BERUFENET")
            sys.exit(1)
        occupations = fetch_from_api(api_key)

    # Add slugs
    for occ in occupations:
        occ["slug"] = slugify(occ["title_de"])

    # Save
    os.makedirs("../data", exist_ok=True)
    with open("../data/kldb_occupations.json", "w", encoding="utf-8") as f:
        json.dump(occupations, f, ensure_ascii=False, indent=2)

    print(f"\nSaved {len(occupations)} occupations to ../data/kldb_occupations.json")

    # Stats
    by_area = {}
    for occ in occupations:
        area = occ["berufsbereich"]
        by_area[area] = by_area.get(area, 0) + 1
    print("\nOccupations by area:")
    for area in sorted(by_area.keys()):
        name = BERUFSBEREICHE.get(area, {}).get("de", "?")
        print(f"  {area}: {by_area[area]:4d}  {name}")


if __name__ == "__main__":
    main()
