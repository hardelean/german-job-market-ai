#!/usr/bin/env python3
"""
Fetch median wage data for German occupations from the Entgeltatlas.

The Entgeltatlas is maintained by the Bundesagentur für Arbeit and provides
median gross monthly wages by KldB 2010 occupation codes.

Source: https://web.arbeitsagentur.de/entgeltatlas/
API: https://rest.arbeitsagentur.de/infosysbub/entgeltatlas/pc/v1/entgelte

Output: ../data/wages_de.json

Usage:
    export BA_API_KEY=your_key_here
    python fetch_wages.py

    # Or from downloaded CSV:
    python fetch_wages.py --from-file entgeltatlas_export.csv
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


BA_ENTGELT_API = "https://rest.arbeitsagentur.de/infosysbub/entgeltatlas/pc/v1"


def fetch_from_api(api_key, kldb_codes):
    """Fetch wage data from Entgeltatlas API for given KldB codes."""
    client = httpx.Client(timeout=30)
    headers = {
        "X-API-Key": api_key,
        "Accept": "application/json",
    }

    wages = {}
    total = len(kldb_codes)

    print(f"Fetching wages for {total} occupations from Entgeltatlas...")

    for i, code in enumerate(kldb_codes):
        try:
            resp = client.get(
                f"{BA_ENTGELT_API}/entgelte/{code}",
                headers=headers,
                params={
                    "region": "1",  # Germany total
                    "alter": "0",   # All ages
                    "geschlecht": "0",  # All genders
                },
            )

            if resp.status_code == 200:
                data = resp.json()
                # Extract median monthly gross wage
                median_monthly = data.get("median") or data.get("q50")
                if median_monthly:
                    wages[code] = {
                        "median_monthly": int(median_monthly),
                        "median_annual": int(median_monthly) * 12,
                        "q25_monthly": data.get("q25"),
                        "q75_monthly": data.get("q75"),
                    }

                if (i + 1) % 50 == 0:
                    print(f"  [{i+1}/{total}] Fetched {len(wages)} wages so far")

            elif resp.status_code == 404:
                pass  # No wage data for this code
            else:
                print(f"  Warning: HTTP {resp.status_code} for {code}")

        except Exception as e:
            print(f"  Error for {code}: {e}")

        # Rate limiting
        time.sleep(0.3)

    client.close()
    return wages


def parse_from_file(filepath):
    """Parse wage data from downloaded Entgeltatlas export."""
    wages = {}

    if filepath.endswith(".csv"):
        with open(filepath, encoding="utf-8") as f:
            sample = f.read(2000)
            f.seek(0)
            delimiter = ";" if ";" in sample else ","

            reader = csv.reader(f, delimiter=delimiter)
            header = next(reader, None)

            # Find relevant columns
            code_col = 0
            wage_col = -1
            if header:
                for i, h in enumerate(header):
                    h_lower = h.lower()
                    if "kldb" in h_lower or "code" in h_lower:
                        code_col = i
                    if "median" in h_lower or "entgelt" in h_lower or "gehalt" in h_lower:
                        wage_col = i

                if wage_col == -1:
                    for i, h in enumerate(header):
                        if "brutto" in h.lower() or "monat" in h.lower():
                            wage_col = i
                            break

            for row in reader:
                if len(row) > max(code_col, wage_col) and wage_col >= 0:
                    code = row[code_col].strip()
                    try:
                        wage_str = row[wage_col].strip().replace(" ", "").replace(",", ".").replace("€", "")
                        monthly = int(float(wage_str))
                        if 500 < monthly < 30000:  # Sanity check
                            wages[code] = {
                                "median_monthly": monthly,
                                "median_annual": monthly * 12,
                            }
                    except (ValueError, IndexError):
                        pass

    elif filepath.endswith(".xlsx"):
        try:
            import openpyxl
        except ImportError:
            print("Install openpyxl: pip install openpyxl")
            sys.exit(1)

        wb = openpyxl.load_workbook(filepath, read_only=True)
        ws = wb.active
        rows = list(ws.iter_rows(values_only=True))

        for row in rows[1:]:  # Skip header
            if row and row[0]:
                code = str(row[0]).strip()
                for cell in row[1:]:
                    if isinstance(cell, (int, float)) and 500 < cell < 30000:
                        wages[code] = {
                            "median_monthly": int(cell),
                            "median_annual": int(cell) * 12,
                        }
                        break
        wb.close()

    print(f"  Parsed {len(wages)} wage entries from {filepath}")
    return wages


# Fallback: estimated median wages by KldB Berufsbereich and Anforderungsniveau
# Based on Entgeltatlas 2023 aggregate data
WAGE_ESTIMATES = {
    # (berufsbereich, anforderungsniveau) → monthly gross median EUR
    ("1", "1"): 2200, ("1", "2"): 2600, ("1", "3"): 3200, ("1", "4"): 4200,
    ("2", "1"): 2400, ("2", "2"): 3100, ("2", "3"): 3800, ("2", "4"): 5200,
    ("3", "1"): 2500, ("3", "2"): 3200, ("3", "3"): 4000, ("3", "4"): 4800,
    ("4", "1"): 2600, ("4", "2"): 3500, ("4", "3"): 4400, ("4", "4"): 5500,
    ("5", "1"): 2300, ("5", "2"): 2900, ("5", "3"): 3800, ("5", "4"): 5000,
    ("6", "1"): 2100, ("6", "2"): 2800, ("6", "3"): 3500, ("6", "4"): 4800,
    ("7", "1"): 2400, ("7", "2"): 3000, ("7", "3"): 3900, ("7", "4"): 5600,
    ("8", "1"): 2300, ("8", "2"): 3000, ("8", "3"): 3400, ("8", "4"): 4600,
    ("9", "1"): 2100, ("9", "2"): 2700, ("9", "3"): 3400, ("9", "4"): 4200,
    ("0", "1"): 2500, ("0", "2"): 2900, ("0", "3"): 3500, ("0", "4"): 4500,
}


def estimate_wage(kldb_code):
    """Estimate median wage from KldB code using aggregate data."""
    if len(kldb_code) >= 5:
        area = kldb_code[0]
        level = kldb_code[4]
        key = (area, level)
        monthly = WAGE_ESTIMATES.get(key, 3000)
        return {"median_monthly": monthly, "median_annual": monthly * 12, "estimated": True}
    return None


def main():
    parser = argparse.ArgumentParser(description="Fetch German wage data")
    parser.add_argument("--from-file", help="Parse from downloaded CSV/XLSX")
    parser.add_argument("--kldb-file", default="../data/kldb_occupations.json",
                       help="KldB occupations file for code list")
    parser.add_argument("--use-estimates", action="store_true",
                       help="Use aggregate estimates instead of API")
    args = parser.parse_args()

    if args.from_file:
        wages = parse_from_file(args.from_file)
    elif args.use_estimates:
        # Load KldB codes and estimate
        if os.path.exists(args.kldb_file):
            with open(args.kldb_file) as f:
                kldb_data = json.load(f)
            wages = {}
            for occ in kldb_data:
                code = occ["kldb_code"]
                est = estimate_wage(code)
                if est:
                    wages[code] = est
            print(f"Generated estimates for {len(wages)} occupations")
        else:
            print(f"Error: {args.kldb_file} not found. Run fetch_kldb.py first.")
            sys.exit(1)
    else:
        api_key = os.environ.get("BA_API_KEY")
        if not api_key:
            print("Error: Set BA_API_KEY or use --from-file or --use-estimates")
            sys.exit(1)

        # Load KldB codes
        if os.path.exists(args.kldb_file):
            with open(args.kldb_file) as f:
                kldb_data = json.load(f)
            codes = [occ["kldb_code"] for occ in kldb_data]
        else:
            print(f"Warning: {args.kldb_file} not found, cannot determine codes to fetch")
            sys.exit(1)

        wages = fetch_from_api(api_key, codes)

    # Save
    os.makedirs("../data", exist_ok=True)
    with open("../data/wages_de.json", "w", encoding="utf-8") as f:
        json.dump(wages, f, ensure_ascii=False, indent=2)

    print(f"\nSaved {len(wages)} wage entries to ../data/wages_de.json")

    # Quick stats
    if wages:
        annual_vals = [v["median_annual"] for v in wages.values() if "median_annual" in v]
        if annual_vals:
            avg = sum(annual_vals) / len(annual_vals)
            print(f"Average median annual wage: €{avg:,.0f}")
            print(f"Range: €{min(annual_vals):,} – €{max(annual_vals):,}")


if __name__ == "__main__":
    main()
