#!/usr/bin/env python3
"""
Fetch EU employment context data from Eurostat REST API.

Uses the Eurostat SDMX 2.1 REST API to get employment statistics
by country and occupation group (ISCO-08).

API documentation:
https://wikis.ec.europa.eu/display/EUROSTATHELP/API+-+Getting+started

Key datasets:
- lfsa_egan22d: Employment by ISCO-08 occupation group
- lfsa_egdn: Employment by country (total)

Output: ../site/eu_context.json

Usage:
    python fetch_eurostat.py
"""

import json
import os
import sys
import time

try:
    import httpx
except ImportError:
    print("Install httpx: pip install httpx")
    sys.exit(1)


EUROSTAT_API = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0"

# EU countries to include in comparison
EU_COUNTRIES = {
    "DE": {"de": "Deutschland", "en": "Germany"},
    "FR": {"de": "Frankreich", "en": "France"},
    "IT": {"de": "Italien", "en": "Italy"},
    "ES": {"de": "Spanien", "en": "Spain"},
    "PL": {"de": "Polen", "en": "Poland"},
    "NL": {"de": "Niederlande", "en": "Netherlands"},
    "SE": {"de": "Schweden", "en": "Sweden"},
    "AT": {"de": "Österreich", "en": "Austria"},
    "BE": {"de": "Belgien", "en": "Belgium"},
    "CZ": {"de": "Tschechien", "en": "Czechia"},
    "RO": {"de": "Rumänien", "en": "Romania"},
    "PT": {"de": "Portugal", "en": "Portugal"},
    "DK": {"de": "Dänemark", "en": "Denmark"},
    "IE": {"de": "Irland", "en": "Ireland"},
    "FI": {"de": "Finnland", "en": "Finland"},
}

# ISCO-08 major groups (for AI exposure estimation)
ISCO_GROUPS = {
    "OC1": {"name": "Managers", "ai_exposure_est": 5.5},
    "OC2": {"name": "Professionals", "ai_exposure_est": 6.0},
    "OC3": {"name": "Technicians and associate professionals", "ai_exposure_est": 5.0},
    "OC4": {"name": "Clerical support workers", "ai_exposure_est": 7.5},
    "OC5": {"name": "Service and sales workers", "ai_exposure_est": 3.0},
    "OC6": {"name": "Skilled agricultural workers", "ai_exposure_est": 2.0},
    "OC7": {"name": "Craft and related trades workers", "ai_exposure_est": 2.0},
    "OC8": {"name": "Plant and machine operators", "ai_exposure_est": 3.0},
    "OC9": {"name": "Elementary occupations", "ai_exposure_est": 1.5},
}


def fetch_eurostat_data(dataset, filters):
    """Fetch data from Eurostat API with given filters."""
    client = httpx.Client(timeout=60)

    params = {
        "format": "JSON",
        "lang": "en",
    }
    params.update(filters)

    url = f"{EUROSTAT_API}/data/{dataset}"
    print(f"  Fetching {dataset}...")

    try:
        resp = client.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()
        client.close()
        return data
    except Exception as e:
        print(f"  Error: {e}")
        client.close()
        return None


def parse_eurostat_employment(data):
    """Parse Eurostat JSON-stat format employment data."""
    if not data:
        return {}

    values = data.get("value", {})
    dimensions = data.get("dimension", {})

    # Get country dimension
    geo_dim = dimensions.get("geo", {}).get("category", {}).get("index", {})
    time_dim = dimensions.get("time", {}).get("category", {}).get("index", {})

    # Get the dimension sizes for index calculation
    size = data.get("size", [])

    employment = {}
    for country_code, country_idx in geo_dim.items():
        if country_code in EU_COUNTRIES:
            # Find the value for the latest year
            for time_key, time_idx in time_dim.items():
                idx = str(country_idx * len(time_dim) + time_idx)
                if idx in values:
                    val = values[idx]
                    if val and val > 0:
                        # Convert from thousands if needed
                        employment[country_code] = int(val * 1000) if val < 100000 else int(val)

    return employment


def estimate_country_ai_exposure(country_code, isco_shares=None):
    """
    Estimate country-level AI exposure based on ISCO occupation mix.

    Countries with higher shares of knowledge workers (ISCO 1-4) will have
    higher average AI exposure than those with more manual workers (ISCO 5-9).
    """
    # Default occupation mix estimates (% of total employment by ISCO group)
    # Based on Eurostat lfsa_egan22d data
    COUNTRY_ISCO_SHARES = {
        "DE": {"OC1": 5, "OC2": 22, "OC3": 20, "OC4": 10, "OC5": 16, "OC6": 1, "OC7": 12, "OC8": 7, "OC9": 7},
        "FR": {"OC1": 6, "OC2": 22, "OC3": 18, "OC4": 11, "OC5": 16, "OC6": 2, "OC7": 10, "OC8": 7, "OC9": 8},
        "NL": {"OC1": 7, "OC2": 28, "OC3": 18, "OC4": 9, "OC5": 17, "OC6": 1, "OC7": 7, "OC8": 4, "OC9": 9},
        "SE": {"OC1": 6, "OC2": 28, "OC3": 20, "OC4": 6, "OC5": 18, "OC6": 1, "OC7": 8, "OC8": 5, "OC9": 8},
        "PL": {"OC1": 5, "OC2": 18, "OC3": 14, "OC4": 8, "OC5": 15, "OC6": 6, "OC7": 14, "OC8": 10, "OC9": 10},
        "IT": {"OC1": 3, "OC2": 17, "OC3": 18, "OC4": 10, "OC5": 18, "OC6": 3, "OC7": 12, "OC8": 8, "OC9": 11},
        "ES": {"OC1": 4, "OC2": 19, "OC3": 14, "OC4": 9, "OC5": 21, "OC6": 3, "OC7": 10, "OC8": 8, "OC9": 12},
        "AT": {"OC1": 5, "OC2": 20, "OC3": 20, "OC4": 10, "OC5": 17, "OC6": 3, "OC7": 11, "OC8": 6, "OC9": 8},
    }

    shares = isco_shares or COUNTRY_ISCO_SHARES.get(country_code, COUNTRY_ISCO_SHARES["DE"])

    total_share = sum(shares.values())
    weighted_exposure = 0
    for isco, share in shares.items():
        exposure = ISCO_GROUPS.get(isco, {}).get("ai_exposure_est", 3.0)
        weighted_exposure += exposure * (share / total_share)

    return round(weighted_exposure, 1)


def build_eu_context():
    """Build the complete EU context dataset."""
    print("Building EU context data...")

    # Try to fetch from Eurostat
    employment_data = {}

    # Attempt API fetch
    try:
        data = fetch_eurostat_data("lfsa_egan2", {
            "geo": ",".join(EU_COUNTRIES.keys()),
            "time": "2023",
            "isco08": "TOTAL",
            "sex": "T",
            "age": "Y15-64",
            "unit": "THS_PER",
        })
        employment_data = parse_eurostat_employment(data) if data else {}
    except Exception as e:
        print(f"  API fetch failed: {e}")

    # Fallback: use known estimates if API fails
    FALLBACK_EMPLOYMENT = {
        "DE": 45900000, "FR": 30100000, "IT": 25600000, "ES": 21200000,
        "PL": 17300000, "NL": 9700000, "SE": 5300000, "AT": 4500000,
        "BE": 5100000, "CZ": 5400000, "RO": 8300000, "PT": 5100000,
        "DK": 3000000, "IE": 2600000, "FI": 2700000,
    }

    for code in EU_COUNTRIES:
        if code not in employment_data:
            employment_data[code] = FALLBACK_EMPLOYMENT.get(code, 0)

    # Calculate EU total
    total_eu = sum(employment_data.values())

    # Build comparison data
    countries = []
    for code, names in sorted(EU_COUNTRIES.items(), key=lambda x: -employment_data.get(x[0], 0)):
        emp = employment_data.get(code, 0)
        if emp > 0:
            countries.append({
                "code": code,
                "name_de": names["de"],
                "name_en": names["en"],
                "employment": emp,
                "ai_exposure_est": estimate_country_ai_exposure(code),
            })

    de_employment = employment_data.get("DE", 45900000)

    # Calculate weighted EU average AI exposure
    total_weighted = sum(c["ai_exposure_est"] * c["employment"] for c in countries)
    total_emp = sum(c["employment"] for c in countries)
    avg_eu_exposure = round(total_weighted / total_emp, 1) if total_emp > 0 else 3.9

    context = {
        "total_eu_employment": total_eu,
        "de_share_of_eu": round(de_employment / total_eu, 3) if total_eu > 0 else 0.215,
        "avg_ai_exposure_eu_est": avg_eu_exposure,
        "countries_comparison": countries[:8],  # Top 8 for UI
        "data_year": 2023,
        "source": "Eurostat, own estimates based on ISCO-08 occupation mix",
    }

    return context


def main():
    context = build_eu_context()

    os.makedirs("../site", exist_ok=True)
    with open("../site/eu_context.json", "w", encoding="utf-8") as f:
        json.dump(context, f, ensure_ascii=False, indent=2)

    print(f"\nSaved EU context to ../site/eu_context.json")
    print(f"Countries: {len(context['countries_comparison'])}")
    print(f"Total EU employment: {context['total_eu_employment']:,}")
    print(f"DE share: {context['de_share_of_eu']*100:.1f}%")
    print(f"Avg EU AI exposure: {context['avg_ai_exposure_eu_est']}")


if __name__ == "__main__":
    main()
