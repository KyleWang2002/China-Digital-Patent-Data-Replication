# Digital Technology Patents in China: Data Collection and Spatial Matching

[中文 README](README_zh.md) · [Methods](docs/METHODS.md)

This project grew out of my attempt to reproduce the patent-data construction in Chen et al. (2024), published in *Economic Research Journal* (《经济研究》). I experimented with collecting patent metadata from the dynamic **IncoPat** interface using Selenium, then organized the workflow around patent parsing, digital-technology screening, and geographic matching.

## What I worked on

- **Data collection:** navigating patent-detail pages and extracting application numbers, dates, applicants and other metadata; an example of the recorded fields is available [here](examples/incopat_ui_excerpt.csv).
- **Patent processing:** normalizing fields, deduplicating application records, and screening titles and available text into five digital-technology categories: AI, big data, cloud computing, blockchain and 5G.
- **Spatial analysis:** optional address geocoding, coordinate conversion and 1–10 km patent–monitoring-station matching, with 5 km as the baseline.
- **Panel construction:** daily counts and value-weighted patent stocks around individual monitoring stations, when patent value scores are available.

The original study uses approximately **410,000 Chinese digital-technology patents (1985–2021)** and **2,016 air-quality monitoring stations**. The data here consist of a small excerpt from my earlier interface exploration and **synthetic inputs** to demonstrate the processing workflow; they are not the study's full patent panel. The repository focuses on data construction rather than reproducing the paper's regression tables.

## Workflow

```text
IncoPat metadata / permitted export
        ↓
Parse and deduplicate patent records
        ↓
Digital-technology keyword screening
        ↓
Geocode addresses and standardize coordinates
        ↓
Match patents to monitoring stations
        ↓
Compute station-day patent stocks
```

## Run

Use Python 3.10+:

```bash
python -m pip install -e .
python scripts/run_demo.py
python -m unittest discover -s tests -v
```

The demo generates CSV outputs under `outputs/demo/` and does not require a website account or API key. See [methods](docs/METHODS.md) for processing your own authorized data exports. The optional browser code requires manually authenticated IncoPat access, and its selectors may need updates.

## Files

```text
src/patentrep/   Parsing, classification, geocoding and spatial matching
scripts/         Demo and optional data collection/geocoding tools
notebooks/       Selenium exploration notebook
examples/        Small real metadata excerpt from the original experiment
data/            Synthetic inputs and exploratory keyword dictionary
tests/           Offline tests
docs/METHODS.md  Technical notes and field conventions
```

## Reference

Chen, X., Zhang, J., Wang, Y., & Yang, Q. (2024). Digital empowerment, technological innovation and air pollution control: Evidence from patent text mining. *Economic Research Journal* (《经济研究》), 2024(12), 21–39.

**Yuankui Wang** · Hunan University
