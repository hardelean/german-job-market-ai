# 🇩🇪 KI-Exposition des deutschen Arbeitsmarktes
## AI Exposure of the German Job Market

An interactive visualization mapping **133 German occupations** by their exposure to artificial intelligence, adapted for the German and European labor market context.

**[Live Demo →](#)** *(deploy to GitHub Pages after cloning)*

![Treemap View](docs/screenshot-treemap.png)

---

## Attribution & Lineage

### Original Project

This project is a **German adaptation** of [**Andrej Karpathy's**](https://karpathy.ai/) original work:

> **[karpathy/jobs](https://github.com/karpathy/jobs)** — *AI Exposure of the Canadian Job Market*
> 516 Canadian occupations (NOC 2021) scored on a 0–10 AI exposure scale,
> visualized as an interactive treemap and scatter plot.
> Data from Canada's Job Bank, Statistics Canada (StatCan), and COPS.
> Scoring by GPT-4o-mini.

Karpathy's original tool was published at [krunal16-c.github.io/jobs](https://krunal16-c.github.io/jobs/index.html),
with the Canadian adaptation contributed by [Krunal Chavda (krunal16-c)](https://github.com/krunal16-c).

### German Adaptation

This German version was **researched, designed, and built by Claude Opus 4.6** (Anthropic's AI assistant, operating in Cowork mode) at the request of [Horia Ardelean](https://github.com/horiaardelean).

The adaptation involved:
- Complete redesign of the data schema for the German labor classification system (KldB 2010)
- New data pipeline targeting German federal data sources (Bundesagentur für Arbeit, Destatis, Eurostat)
- Bilingual interface (German/English) with full i18n support
- EU comparison context layer with cross-country employment data
- German-specific AI exposure scoring prompt accounting for the dual vocational system, works councils, and EU AI Act
- Rewritten education, salary, and labor outlook categorizations for Germany

---

## What This Tool Does

Each rectangle in the treemap represents a German occupation. **Size** encodes employment count; **color** encodes AI exposure (green = low, red = high). The tool answers: *How vulnerable is each German occupation to AI automation?*

### Key Features

| Feature | Description |
|---------|-------------|
| **Treemap view** | Occupations grouped by KldB Berufsbereich, sized by employment |
| **Scatter view** | AI exposure score vs. labor market outlook (Engpassanalyse) |
| **Bilingual toggle** | Full DE ↔ EN switching for all labels, filters, tooltips |
| **Dark/light theme** | Toggle between dark and light color schemes |
| **10 smart filters** | Fachkräftemangel, Überhang, salary bands, sectors, AI tiers |
| **EU context panel** | Employment comparison across 8 EU countries |
| **Rich tooltips** | German + English titles, KldB code, salary, education, outlook, AI rationale |
| **Zero dependencies** | Pure HTML/CSS/JS, no frameworks, no build step |

### German-Specific Adaptations

This is not a simple translation — the German labor market has fundamentally different structures:

- **KldB 2010** (Klassifikation der Berufe) replaces Canada's NOC 2021 as the occupation taxonomy
- **Anforderungsniveaus** (Helfer → Fachkraft → Spezialist → Experte) replace TEER-based education levels
- **Engpassanalyse** (bottleneck analysis) from the Bundesagentur replaces COPS surplus/shortage outlook
- **EUR salary bands** calibrated to German wage structure (Entgeltatlas medians)
- **Betriebsräte and Mitbestimmung** factor into AI exposure scoring (stronger worker protections slow adoption)
- **EU AI Act** regulatory context included in scoring rationale
- **Dual vocational system** (Duales Ausbildungssystem) recognized as a structural difference affecting automation risk

---

## Research & Methodology

### Data Sources

| Source | Data Provided | License | URL |
|--------|---------------|---------|-----|
| **Bundesagentur für Arbeit** | KldB 2010 classification, Entgeltatlas wages, Engpassanalyse | DL-DE/BY-2.0 | [arbeitsagentur.de](https://www.arbeitsagentur.de) |
| **Destatis (GENESIS)** | Employment by occupation (Table 12211-0010) | DL-DE/BY-2.0 | [destatis.de](https://www.destatis.de) |
| **Eurostat** | EU-wide employment by ISCO-08, cross-country comparison | Eurostat Copyright | [ec.europa.eu/eurostat](https://ec.europa.eu/eurostat) |
| **OpenAI GPT-4o-mini** | AI exposure scores (0–10) with written rationale | — | [openai.com](https://openai.com) |

### AI Exposure Scoring Rubric

Each occupation is scored on a 0–10 scale by an LLM. The scoring prompt was adapted from Karpathy's original rubric with German-specific anchors:

| Score | Level | German Examples |
|-------|-------|-----------------|
| **0–1** | Minimal | Dachdecker, Feuerwehr, Landwirt |
| **2–3** | Low | Elektriker, Krankenpfleger, Klempner |
| **4–5** | Moderate | Arzt, Polizist, Lehrer |
| **6–7** | High | Steuerberater, Unternehmensberater, Personalmanager |
| **8–9** | Very high | Softwareentwickler, Grafikdesigner, Übersetzer |
| **10** | Maximum | Dateneingabe, Telemarketing |

Key principle: If the job's work product is fundamentally digital (can be done entirely from a home office on a computer), AI exposure is inherently high (7+). Jobs requiring physical presence have a natural barrier.

### German-Specific Scoring Factors

The scoring prompt includes these Germany-specific considerations not present in the Canadian version:

1. **Duales Ausbildungssystem** — Germany's dual vocational training produces workers with deep practical skills that are harder to automate than purely academic training
2. **Betriebsräte & Mitbestimmung** — Works councils and co-determination laws slow the pace of AI-driven workforce restructuring
3. **EU AI Act** — European regulation restricts certain high-risk AI applications in employment, healthcare, and public administration
4. **Mittelstand** — Germany's SME-heavy economy may adopt AI more slowly than large tech-oriented economies
5. **Manufacturing focus** — Germany's strong industrial sector means physical automation (robotics) is a separate consideration from AI exposure

### EU Context Methodology

Country-level AI exposure estimates are derived from ISCO-08 occupation mix data (Eurostat). Countries with higher shares of knowledge workers (ISCO groups 1–4: managers, professionals, technicians, clerical) receive higher estimated AI exposure scores than those with more manual workers (ISCO groups 5–9). This is a structural estimate, not an individual occupation analysis.

### KldB 2010 Classification Structure

The German classification system differs from Canada's NOC:

| KldB Area | German Name | English Name | Seed Occupations |
|-----------|-------------|--------------|------------------|
| 1 | Land-, Forst- und Tierwirtschaft | Agriculture, Forestry | 5 |
| 2 | Rohstoffgewinnung, Produktion | Production, Manufacturing | 16 |
| 3 | Bau, Architektur, Gebäudetechnik | Construction, Architecture | 12 |
| 4 | Naturwissenschaft, Informatik | Natural Sciences, IT | 16 |
| 5 | Verkehr, Logistik, Sicherheit | Transport, Logistics, Security | 11 |
| 6 | Kaufm. Dienstleistungen, Handel | Commercial Services, Trade | 17 |
| 7 | Unternehmensorg., Recht, Verwaltung | Corporate, Law, Administration | 20 |
| 8 | Gesundheit, Soziales, Lehre | Health, Social Work, Education | 23 |
| 9 | Geisteswiss., Medien, Kunst | Humanities, Media, Arts | 12 |
| 0 | Militär | Military | 1 |

### Seed Data Statistics

The current prototype includes 133 representative German occupations covering ~29.1M of Germany's ~45.9M total workforce:

- **Weighted average AI exposure:** 4.4 / 10
- **Most exposed category:** Corporate Organisation, Accounting, Law and Administration (avg ~6.8)
- **Least exposed category:** Construction, Architecture, Building Technology (avg ~2.1)
- **EUR payroll at risk (exposure 7+):** ~€189 billion annually

---

## Project Structure

```
german-job-market-ai/
├── site/                          # Frontend (ready to deploy)
│   ├── index.html                 # Main interactive visualization (self-contained)
│   ├── about.html                 # Methodology page (bilingual)
│   ├── data.json                  # Occupation data (also embedded in index.html)
│   └── eu_context.json            # EU comparison data
├── pipeline/                      # Data pipeline scripts
│   ├── README.md                  # Pipeline setup & usage guide
│   ├── generate_seed_data.py      # Generate demo dataset (no API needed)
│   ├── fetch_kldb.py              # Fetch KldB 2010 classification
│   ├── fetch_employment.py        # Fetch employment data from Destatis
│   ├── fetch_wages.py             # Fetch wage data from Entgeltatlas
│   ├── fetch_outlook.py           # Fetch Engpassanalyse data
│   ├── fetch_eurostat.py          # Fetch EU comparison data
│   ├── score_de.py                # LLM-based AI exposure scoring
│   └── build_site_data_de.py      # Merge all sources for frontend
├── data/                          # Generated data files
│   └── occupations_de.csv         # Full occupation dataset (CSV)
└── README.md                      # This file
```

---

## Quick Start

### Option 1: Just view it

Open `site/index.html` in any web browser. The data is embedded — no server needed.

### Option 2: Run the data pipeline

```bash
# Install dependencies
pip install httpx openpyxl python-dotenv

# Generate demo data (no API keys needed)
cd pipeline
python generate_seed_data.py

# Or run the full pipeline with real data:
# See pipeline/README.md for detailed instructions
```

### Option 3: Deploy to GitHub Pages

```bash
# In your repo settings:
# Settings → Pages → Source: Deploy from branch → Branch: main, /site
```

---

## Technology

- **Frontend:** Pure HTML5 Canvas + vanilla JavaScript (zero dependencies, ~145KB self-contained)
- **Visualization:** Custom squarified treemap algorithm (ported from Karpathy's original)
- **Pipeline:** Python 3.10+ with httpx, openpyxl
- **Scoring:** OpenAI GPT-4o-mini via REST API
- **Data format:** JSON (site), CSV (pipeline)

---

## Differences from the Canadian Original

| Aspect | Canadian (karpathy/jobs) | German (this repo) |
|--------|--------------------------|---------------------|
| Occupations | 516 (NOC 2021) | 133 seed, ~1,300 possible (KldB 2010 5-digit) |
| Classification | NOC 2021 | KldB 2010 |
| Employment | ~20.1M | ~29.1M (seed) / 45.9M (full) |
| Currency | CAD | EUR |
| Education system | TEER levels | Anforderungsniveaus (Helfer→Experte) |
| Outlook | COPS surplus/shortage | Engpassanalyse |
| Language | English only | Bilingual DE/EN toggle |
| EU context | None | 8-country comparison panel |
| Data sources | Job Bank, StatCan | Bundesagentur, Destatis, Eurostat |
| Regulatory context | None | EU AI Act, Betriebsräte, Mitbestimmung |

---

## License

This project is released under the **MIT License**, consistent with the original karpathy/jobs project.

German government data (Bundesagentur, Destatis) is used under the [Datenlizenz Deutschland – Namensnennung – Version 2.0](https://www.govdata.de/dl-de/by-2-0) (DL-DE/BY-2.0).

---

## Credits

- **Original concept & implementation:** [Andrej Karpathy](https://karpathy.ai/) — [karpathy/jobs](https://github.com/karpathy/jobs)
- **Canadian data adaptation:** [Krunal Chavda (krunal16-c)](https://github.com/krunal16-c) — [krunal16-c/jobs](https://github.com/krunal16-c/jobs)
- **German adaptation, research & development:** [Claude Opus 4.6](https://claude.ai/) (Anthropic) operating in Cowork mode, at the request of [Horia Ardelean](https://github.com/horiaardelean)
  - Studied and reverse-engineered the original Canadian tool's complete source code (1,293 lines of HTML/CSS/JS)
  - Researched German labor market data sources (KldB 2010, Entgeltatlas, Engpassanalyse, GENESIS API, Eurostat)
  - Designed bilingual data schema with German-specific education levels, salary bands, and outlook categories
  - Wrote 8 data pipeline scripts targeting German federal APIs and data exports
  - Adapted the AI exposure scoring rubric for German labor market specificities
  - Built the EU comparison layer with ISCO-08-based cross-country exposure estimates
  - Implemented full German/English i18n with dynamic switching
