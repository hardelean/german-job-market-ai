#!/usr/bin/env python3
"""
Build the final site/data.json for the German AI Job Market Exposure tool.

Merges data from all pipeline sources:
- KldB occupation classification (kldb_occupations.json)
- Employment statistics (employment_de.json)
- Wage data (wages_de.json)
- Engpassanalyse outlook (outlook_de.json)
- AI exposure scores (scores_de.json)

Output: ../site/data.json

Usage:
    python build_site_data_de.py
"""

import json
import os
import re
import sys


def slugify(text):
    text = text.lower()
    text = re.sub(r'[äÄ]', 'ae', text)
    text = re.sub(r'[öÖ]', 'oe', text)
    text = re.sub(r'[üÜ]', 'ue', text)
    text = re.sub(r'[ß]', 'ss', text)
    text = re.sub(r'[^a-z0-9]+', '-', text)
    return text.strip('-')


def load_json(path, default=None):
    """Load JSON file, return default if not found."""
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    print(f"  Warning: {path} not found, using defaults")
    return default if default is not None else {}


def main():
    data_dir = "../data"

    print("Loading pipeline data...")

    # 1. Load KldB occupations (required)
    occupations = load_json(f"{data_dir}/kldb_occupations.json", [])
    if not occupations:
        print("Error: No occupation data found. Run fetch_kldb.py first.")
        print("Or run generate_seed_data.py to create a demo dataset.")
        sys.exit(1)

    # 2. Load employment data
    employment = load_json(f"{data_dir}/employment_de.json", {})

    # 3. Load wage data
    wages = load_json(f"{data_dir}/wages_de.json", {})

    # 4. Load outlook data
    outlook = load_json(f"{data_dir}/outlook_de.json", {})

    # 5. Load AI exposure scores
    scores_list = load_json(f"{data_dir}/scores_de.json", [])
    scores = {s["slug"]: s for s in scores_list} if isinstance(scores_list, list) else {}

    print(f"  Occupations: {len(occupations)}")
    print(f"  Employment entries: {len(employment)}")
    print(f"  Wage entries: {len(wages)}")
    print(f"  Outlook entries: {len(outlook)}")
    print(f"  AI scores: {len(scores)}")

    # Merge everything
    data = []
    for occ in occupations:
        code = occ["kldb_code"]
        slug = occ.get("slug", slugify(occ.get("title_de", code)))

        # Employment
        jobs = employment.get(code)

        # Wages
        wage_info = wages.get(code, {})
        pay = wage_info.get("median_annual")

        # Outlook
        outlook_info = outlook.get(code, {})
        outlook_pct = outlook_info.get("outlook_pct")
        outlook_desc_de = outlook_info.get("outlook_desc_de", occ.get("outlook_desc_de", ""))
        outlook_desc_en = outlook_info.get("outlook_desc_en", occ.get("outlook_desc_en", ""))

        # AI exposure
        score_info = scores.get(slug, {})
        exposure = score_info.get("exposure")
        rationale = score_info.get("rationale", "")

        record = {
            "title_de": occ.get("title_de", ""),
            "title_en": occ.get("title_en", ""),
            "slug": slug,
            "kldb_code": code,
            "category_de": occ.get("category_de", ""),
            "category_en": occ.get("category_en", ""),
            "pay": pay,
            "jobs": jobs,
            "outlook": outlook_pct,
            "outlook_desc_de": outlook_desc_de,
            "outlook_desc_en": outlook_desc_en,
            "education_de": occ.get("education_de", ""),
            "education_en": occ.get("education_en", ""),
            "education_level": occ.get("education_level", 0),
            "exposure": exposure,
            "exposure_rationale": rationale,
            "url": f"https://berufenet.arbeitsagentur.de/berufenet/faces/index?path=null/suchergebnisse&such={code}",
        }
        data.append(record)

    # Filter out occupations with no meaningful data
    # Keep all if they have at least a title
    data = [d for d in data if d["title_de"]]

    # Sort by category then employment
    data.sort(key=lambda d: (d["category_de"], -(d["jobs"] or 0)))

    # Write
    os.makedirs("../site", exist_ok=True)
    with open("../site/data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)

    # Stats
    total_jobs = sum(d["jobs"] for d in data if d["jobs"])
    scored = sum(1 for d in data if d["exposure"] is not None)
    with_pay = sum(1 for d in data if d["pay"])
    with_outlook = sum(1 for d in data if d["outlook"] is not None)

    print(f"\n{'='*50}")
    print(f"Wrote {len(data)} occupations to ../site/data.json")
    print(f"  Total employment: {total_jobs:,}")
    print(f"  With AI scores: {scored}/{len(data)}")
    print(f"  With wage data: {with_pay}/{len(data)}")
    print(f"  With outlook: {with_outlook}/{len(data)}")

    if scored > 0:
        scored_data = [d for d in data if d["exposure"] is not None]
        if any(d["jobs"] for d in scored_data):
            ws = sum(d["exposure"] * (d["jobs"] or 0) for d in scored_data)
            wc = sum(d["jobs"] or 0 for d in scored_data)
            print(f"  Weighted avg exposure: {ws/wc:.1f}/10" if wc > 0 else "")


if __name__ == "__main__":
    main()
