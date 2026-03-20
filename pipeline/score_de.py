#!/usr/bin/env python3
"""
Score each German occupation's AI exposure using an LLM via OpenAI.

Adapted from karpathy/jobs for the German labor market context.
Reads occupation data, sends each to an LLM with a German-specific scoring
rubric, and collects structured scores. Results are cached incrementally.

The scoring prompt includes German-specific context:
- Dual vocational training system (Duales Ausbildungssystem)
- Works councils (Betriebsräte) and co-determination (Mitbestimmung)
- EU AI Act regulatory framework
- German industry structure (Mittelstand, manufacturing focus)

Usage:
    export OPENAI_API_KEY=your_key_here
    python score_de.py
    python score_de.py --model gpt-4o
    python score_de.py --start 0 --end 10
"""

import argparse
import json
import os
import sys
import time

try:
    import httpx
except ImportError:
    print("Install httpx: pip install httpx")
    sys.exit(1)

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


DEFAULT_MODEL = "gpt-4o-mini"
OUTPUT_FILE = "../data/scores_de.json"
API_URL = "https://api.openai.com/v1/chat/completions"

SYSTEM_PROMPT = """\
You are an expert analyst evaluating how exposed different occupations are to \
AI automation. You will be given a description of a German occupation from the \
KldB 2010 (Klassifikation der Berufe) classification system.

Rate the occupation's overall **AI Exposure** on a scale from 0 to 10.

AI Exposure measures: how much will AI reshape this occupation in Germany? \
Consider both direct effects (AI automating tasks currently done by humans) \
and indirect effects (AI making each worker so productive that fewer are needed).

**German-specific considerations:**
- Germany's dual vocational training system (Duales Ausbildungssystem) means \
many workers have deep practical skills that are harder to automate.
- Works councils (Betriebsräte) and co-determination laws \
(Mitbestimmungsgesetz) slow the pace of workforce restructuring.
- The EU AI Act restricts certain high-risk AI applications in employment, \
healthcare, and public administration.
- Germany's Mittelstand (SME-heavy economy) may adopt AI more slowly than \
large tech-oriented economies.
- Germany has a strong manufacturing sector where physical automation \
(robotics) is different from AI exposure.

A key signal is whether the job's work product is fundamentally digital. If \
the job can be done entirely from a home office on a computer — writing, \
coding, analyzing, communicating — then AI exposure is inherently high (7+). \
Conversely, jobs requiring physical presence, manual skill, or real-time \
human interaction in the physical world have a natural barrier.

Use these anchors to calibrate your score:

- **0–1: Minimal exposure.** Almost entirely physical, hands-on, or requires \
real-time human presence in unpredictable environments. \
Examples: Dachdecker (roofer), Landwirt (farmer), Feuerwehrmann (firefighter).

- **2–3: Low exposure.** Mostly physical or interpersonal work. AI might help \
with minor peripheral tasks but doesn't touch the core job. \
Examples: Elektriker (electrician), Klempner (plumber), Krankenpfleger (nurse).

- **4–5: Moderate exposure.** A mix of physical/interpersonal and knowledge \
work. AI can assist with information-processing parts. \
Examples: Arzt (physician), Polizist (police officer), Lehrer (teacher).

- **6–7: High exposure.** Predominantly knowledge work with some human \
judgment needs. Workers using AI may be substantially more productive. \
Examples: Steuerberater (tax advisor), Unternehmensberater (consultant), \
Personalmanager (HR manager).

- **8–9: Very high exposure.** Almost entirely computer-based work. All core \
tasks are in domains where AI is rapidly improving. Major restructuring likely. \
Examples: Softwareentwickler (developer), Grafikdesigner (graphic designer), \
Übersetzer (translator), Buchhalter (bookkeeper).

- **10: Maximum exposure.** Routine digital information processing. AI can \
already do most of it today. \
Examples: Dateneingabekraft (data entry), Telemarketing.

Respond with ONLY a JSON object in this exact format, no other text:
{
  "exposure": <0-10>,
  "rationale": "<2-3 sentences explaining the key factors, in English>"
}\
"""


def build_occupation_prompt(occ):
    """Build the user prompt describing one occupation."""
    parts = []
    parts.append(f"# {occ.get('title_de', 'Unknown')}")
    if occ.get("title_en"):
        parts.append(f"English: {occ['title_en']}")
    parts.append(f"KldB Code: {occ.get('kldb_code', '?')}")
    parts.append(f"Category: {occ.get('category_de', '?')} ({occ.get('category_en', '?')})")
    parts.append(f"Qualification level: {occ.get('education_de', '?')} ({occ.get('education_en', '?')})")

    if occ.get("pay"):
        parts.append(f"Median annual salary: €{occ['pay']:,}")
    if occ.get("jobs"):
        parts.append(f"Employment (2023): {occ['jobs']:,}")
    if occ.get("outlook_desc_de"):
        parts.append(f"Labor market outlook: {occ['outlook_desc_de']} ({occ.get('outlook_desc_en', '')})")

    return "\n".join(parts)


def score_occupation(client, text, model):
    """Send one occupation to the LLM and parse the structured response."""
    response = client.post(
        API_URL,
        headers={
            "Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}",
        },
        json={
            "model": model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": text},
            ],
            "temperature": 0.2,
        },
        timeout=60,
    )
    response.raise_for_status()
    content = response.json()["choices"][0]["message"]["content"]

    # Strip markdown code fences if present
    content = content.strip()
    if content.startswith("```"):
        content = content.split("\n", 1)[1]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()

    return json.loads(content)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--start", type=int, default=0)
    parser.add_argument("--end", type=int, default=None)
    parser.add_argument("--delay", type=float, default=0.5)
    parser.add_argument("--force", action="store_true", help="Re-score even if cached")
    parser.add_argument("--input", default="../data/kldb_occupations.json",
                       help="Input occupations file")
    args = parser.parse_args()

    if not os.environ.get("OPENAI_API_KEY"):
        print("Error: Set OPENAI_API_KEY environment variable")
        sys.exit(1)

    # Load occupations
    if not os.path.exists(args.input):
        print(f"Error: {args.input} not found. Run fetch_kldb.py first.")
        # Try seed data as fallback
        fallback = "../site/data.json"
        if os.path.exists(fallback):
            print(f"Using seed data from {fallback} instead")
            args.input = fallback
        else:
            sys.exit(1)

    with open(args.input, encoding="utf-8") as f:
        occupations = json.load(f)

    subset = occupations[args.start:args.end]

    # Load existing scores
    scores = {}
    if os.path.exists(OUTPUT_FILE) and not args.force:
        with open(OUTPUT_FILE, encoding="utf-8") as f:
            for entry in json.load(f):
                scores[entry["slug"]] = entry

    print(f"Scoring {len(subset)} occupations with {args.model}")
    print(f"Already cached: {len(scores)}")

    errors = []
    client = httpx.Client()

    for i, occ in enumerate(subset):
        slug = occ.get("slug", "")
        if not slug:
            continue

        if slug in scores:
            continue

        prompt = build_occupation_prompt(occ)
        title = occ.get("title_de", slug)

        print(f"  [{i+1}/{len(subset)}] {title}...", end=" ", flush=True)

        try:
            result = score_occupation(client, prompt, args.model)
            scores[slug] = {
                "slug": slug,
                "title_de": occ.get("title_de", ""),
                "title_en": occ.get("title_en", ""),
                "kldb_code": occ.get("kldb_code", ""),
                **result,
            }
            print(f"exposure={result['exposure']}")
        except Exception as e:
            print(f"ERROR: {e}")
            errors.append(slug)

        # Save incrementally
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(list(scores.values()), f, ensure_ascii=False, indent=2)

        if i < len(subset) - 1:
            time.sleep(args.delay)

    client.close()

    print(f"\nDone. Scored {len(scores)} occupations, {len(errors)} errors.")
    if errors:
        print(f"Errors: {errors}")

    # Summary
    vals = [s for s in scores.values() if "exposure" in s]
    if vals:
        avg = sum(s["exposure"] for s in vals) / len(vals)
        by_score = {}
        for s in vals:
            bucket = s["exposure"]
            by_score[bucket] = by_score.get(bucket, 0) + 1
        print(f"\nAverage exposure: {avg:.1f}")
        print("Distribution:")
        for k in sorted(by_score):
            print(f"  {k}: {'█' * by_score[k]} ({by_score[k]})")


if __name__ == "__main__":
    main()
