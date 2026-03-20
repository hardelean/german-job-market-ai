#!/usr/bin/env python3
"""
Fetch employment data for German occupations from Destatis GENESIS API.

Uses Destatis Table 12211-0010: "Erwerbstätige nach Beruf (KldB 2010)"
(Employed persons by occupation, KldB 2010 classification)

The GENESIS API requires registration at:
https://www-genesis.destatis.de/genesis/online

Alternative sources:
- Statistik der Bundesagentur für Arbeit: Sozialversicherungspflichtig Beschäftigte
  https://statistik.arbeitsagentur.de/
- IAB Forschungsdatenzentrum

Output: ../data/employment_de.json

Usage:
    export GENESIS_USER=your_username
    export GENESIS_PASS=your_password
    python fetch_employment.py

    # Or from downloaded CSV:
    python fetch_employment.py --from-file beschaeftigte_kldb.csv
"""

import argparse
import csv
import json
import os
import sys
import time

try:
    import httpx
except ImportError:
    print("Install httpx: pip install httpx")
    sys.exit(1)


GENESIS_API = "https://www-genesis.destatis.de/genesisWS/rest/2020"

# Destatis table for employment by KldB
TABLE_ID = "12211-0010"

# Statistik der Bundesagentur table (alternative, more detailed)
BA_TABLE = "SozBe_Berufe_KldB2010"


def fetch_from_genesis(username, password):
    """Fetch employment data from Destatis GENESIS REST API."""
    client = httpx.Client(timeout=60)

    print(f"Fetching table {TABLE_ID} from Destatis GENESIS...")

    # Login to get token
    login_resp = client.get(
        f"{GENESIS_API}/helloworld/logincheck",
        params={"kennung": username, "passwort": password},
    )
    login_resp.raise_for_status()
    login_data = login_resp.json()
    if login_data.get("Status", {}).get("Code") != 0:
        print(f"Login failed: {login_data}")
        sys.exit(1)

    print("  Login successful")

    # Fetch table data as flat CSV
    resp = client.get(
        f"{GENESIS_API}/data/tablefile",
        params={
            "kennung": username,
            "passwort": password,
            "name": TABLE_ID,
            "area": "all",
            "compress": "false",
            "format": "ffcsv",  # Flat file CSV
            "language": "de",
            "startyear": "2023",
            "endyear": "2023",
        },
    )
    resp.raise_for_status()

    # Parse the CSV response
    lines = resp.text.strip().split("\n")
    reader = csv.DictReader(lines, delimiter=";")

    employment = {}
    for row in reader:
        # GENESIS CSV format has columns like:
        # KLDB10_5;KLDB10_5-label;BEV003;BEV003-label;...;value
        kldb_code = row.get("KLDB10_5", row.get("1_Auspraegung_Code", ""))
        value_str = row.get("BEV003__Erwerbstaetige__Anzahl",
                           row.get("1_Merkmal_Auspraegung", ""))

        if kldb_code and len(kldb_code) == 5:
            try:
                value = int(value_str.replace(" ", "").replace(",", ""))
                employment[kldb_code] = value
            except (ValueError, AttributeError):
                pass

    client.close()
    return employment


def fetch_from_ba_api():
    """
    Alternative: Fetch from Bundesagentur für Arbeit Statistik.

    The BA publishes monthly employment statistics by KldB at:
    https://statistik.arbeitsagentur.de/SiteGlobals/Forms/Suche/Einzelheftsuche_Formular.html

    This function attempts to use the BA's Statistik-API.
    """
    print("Fetching from Bundesagentur Statistik API...")

    # The BA Statistik data is available through their data portal
    # https://statistik.arbeitsagentur.de/DE/Navigation/Statistiken/Interaktive-Statistiken/

    # This would require scraping or using their XLSX exports
    # For now, return empty and use --from-file instead
    print("  BA API integration requires XLSX download.")
    print("  Download from: https://statistik.arbeitsagentur.de/")
    print("  Table: Sozialversicherungspflichtig Beschäftigte nach der KldB 2010")
    return {}


def parse_from_file(filepath):
    """Parse employment data from downloaded file (CSV or XLSX)."""
    employment = {}

    if filepath.endswith(".xlsx"):
        try:
            import openpyxl
        except ImportError:
            print("Install openpyxl: pip install openpyxl")
            sys.exit(1)

        wb = openpyxl.load_workbook(filepath, read_only=True)
        ws = wb.active
        rows = list(ws.iter_rows(values_only=True))

        # Find header row
        header_idx = 0
        for i, row in enumerate(rows):
            if row and any("KldB" in str(c) or "Beruf" in str(c) for c in row if c):
                header_idx = i
                break

        for row in rows[header_idx + 1:]:
            if not row or not row[0]:
                continue
            code = str(row[0]).strip()
            # Try to find the employment count column
            for cell in row[1:]:
                if cell and isinstance(cell, (int, float)):
                    employment[code] = int(cell)
                    break

        wb.close()

    elif filepath.endswith(".csv"):
        with open(filepath, encoding="utf-8") as f:
            # Try different delimiters
            sample = f.read(2000)
            f.seek(0)
            delimiter = ";" if ";" in sample else ","

            reader = csv.reader(f, delimiter=delimiter)
            header = next(reader, None)

            # Find code and count columns
            code_col = 0
            count_col = -1
            if header:
                for i, h in enumerate(header):
                    h_lower = h.lower()
                    if "kldb" in h_lower or "code" in h_lower or "beruf" in h_lower:
                        code_col = i
                    if "beschäftigte" in h_lower or "anzahl" in h_lower or "employed" in h_lower or "count" in h_lower:
                        count_col = i

                if count_col == -1:
                    # Default: assume last numeric column
                    count_col = len(header) - 1

            for row in reader:
                if len(row) > max(code_col, count_col):
                    code = row[code_col].strip()
                    if len(code) >= 3:  # Accept 3-5 digit codes
                        try:
                            count = int(row[count_col].strip().replace(" ", "").replace(",", "").replace(".", ""))
                            employment[code] = count
                        except ValueError:
                            pass

    print(f"  Parsed {len(employment)} occupation entries from {filepath}")
    return employment


def main():
    parser = argparse.ArgumentParser(description="Fetch German employment data")
    parser.add_argument("--from-file", help="Parse from downloaded CSV/XLSX")
    parser.add_argument("--source", choices=["genesis", "ba"], default="genesis",
                       help="API source (default: genesis)")
    args = parser.parse_args()

    if args.from_file:
        employment = parse_from_file(args.from_file)
    elif args.source == "genesis":
        username = os.environ.get("GENESIS_USER")
        password = os.environ.get("GENESIS_PASS")
        if not username or not password:
            print("Error: Set GENESIS_USER and GENESIS_PASS environment variables")
            print("Register at: https://www-genesis.destatis.de/genesis/online")
            sys.exit(1)
        employment = fetch_from_genesis(username, password)
    else:
        employment = fetch_from_ba_api()

    # Save
    os.makedirs("../data", exist_ok=True)
    with open("../data/employment_de.json", "w", encoding="utf-8") as f:
        json.dump(employment, f, ensure_ascii=False, indent=2)

    total = sum(employment.values())
    print(f"\nSaved {len(employment)} entries to ../data/employment_de.json")
    print(f"Total employment represented: {total:,}")


if __name__ == "__main__":
    main()
