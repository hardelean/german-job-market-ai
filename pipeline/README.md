# Data Pipeline — KI-Exposition des deutschen Arbeitsmarktes

## Quick Start (Demo with seed data)

```bash
cd pipeline
python generate_seed_data.py
# Open ../site/index.html in a browser
```

## Full Pipeline (Real data)

### Prerequisites

```bash
pip install httpx openpyxl python-dotenv
```

### Step 1: Fetch KldB 2010 occupation classification

```bash
# Option A: From Bundesagentur API (requires API key)
export BA_API_KEY=your_key_here
python fetch_kldb.py

# Option B: From downloaded classification file
python fetch_kldb.py --from-file /path/to/kldb2010.xlsx
```

Get API key: https://web.arbeitsagentur.de/portal/metasuche/suche/information/BERUFENET

### Step 2: Fetch employment data

```bash
# Option A: From Destatis GENESIS API
export GENESIS_USER=your_username
export GENESIS_PASS=your_password
python fetch_employment.py

# Option B: From downloaded BA Statistik file
python fetch_employment.py --from-file beschaeftigte_kldb.csv
```

Register: https://www-genesis.destatis.de/genesis/online

### Step 3: Fetch wage data

```bash
# Option A: From Entgeltatlas API
export BA_API_KEY=your_key_here
python fetch_wages.py

# Option B: From downloaded export
python fetch_wages.py --from-file entgeltatlas.csv

# Option C: Use aggregate estimates (no API needed)
python fetch_wages.py --use-estimates
```

### Step 4: Fetch Engpassanalyse (outlook)

```bash
# Download from: https://statistik.arbeitsagentur.de/
python fetch_outlook.py --from-file engpassanalyse_2024.xlsx
```

### Step 5: Fetch EU context data

```bash
python fetch_eurostat.py
```

### Step 6: Score AI exposure with LLM

```bash
export OPENAI_API_KEY=your_key_here
python score_de.py
python score_de.py --model gpt-4o  # higher quality
```

### Step 7: Build site data

```bash
python build_site_data_de.py
```

### Step 8: Serve

```bash
cd ../site
python -m http.server 8000
# Open http://localhost:8000
```

## Data Sources

| Source | Data | License |
|--------|------|---------|
| Bundesagentur für Arbeit | KldB 2010, Entgeltatlas, Engpassanalyse | DL-DE/BY-2.0 |
| Destatis (GENESIS) | Employment by occupation | DL-DE/BY-2.0 |
| Eurostat | EU employment statistics | Eurostat Copyright |
| OpenAI GPT-4o-mini | AI exposure scores | — |
