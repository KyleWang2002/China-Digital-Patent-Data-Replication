# Methods and input fields / 数据处理说明

This repository has two independent entry points: the offline patent-to-station workflow and optional interactive metadata collection for users with permitted IncoPat access.

## Inputs

**Patent CSV**: `application_no`, `application_date`, `title`, `abstract` (optional), `claims` (optional), `applicant` (optional), `applicant_address` (optional), `longitude`, `latitude`, `coordinate_system`, and `value_score` (optional). The parser also recognizes selected Chinese headers including `申请号`, `申请日`, `专利名称`, `申请人地址`, and `合享价值度`. An identifier is required; coordinates may remain missing until geocoding. `coordinate_system` must be `wgs84` or `gcj02` for rows with geographic coordinates.

**Station CSV**: `station_id`, `station_name`, `longitude`, `latitude`, `coordinate_system`.

**Keyword CSV**: `category`, `keyword`. The provided dictionary is an editable **screening vocabulary**, not a validated reproduction of the article's complete patent classification. Ambiguous multi-category candidates are flagged for review and omitted from automated category stocks unless a category has been supplied.

## Workflow and conventions

1. Normalize application IDs, dates and available text; deduplicate by application number.
2. Match available patent text against keywords for AI, big data, cloud computing, blockchain and 5G. A source's formal patent classification may require additional manual verification.
3. Geocode applicant addresses only when authorized, and convert Amap's GCJ-02 coordinates into approximate WGS84 before comparison with station coordinates. Low-confidence addresses need manual attention, especially at a 1 km radius.
4. Match each patent to stations by great-circle distance (default 5 km). One patent can appear in multiple station-specific neighborhoods without being duplicated in the original patent file.
5. For each station and date, count matched patent applications up to that date. Value-weighted stocks are generated only when relevant patent value scores are provided; missing values remain missing rather than being imputed.

The paper's patent value scores, historical sample and empirical regressions cannot be reconstructed from the included demonstration records alone. No proprietary IncoPat value score is estimated by these scripts.

## Commands

```bash
python -m pip install -e .
python scripts/run_demo.py
python -m unittest discover -s tests -v

# Process your own geocoded patent export and station file:
python -m patentrep.pipeline --patents PATH/TO/patents.csv --stations PATH/TO/stations.csv --start 2014-05-13 --end 2019-12-31 --out outputs/custom --radius-km 5

# Optional IncoPat capture with authorized manual login:
python -m pip install -e '.[browser]'
python scripts/collect_incopat.py --output data/raw/incopat_export.csv --max-records 5

# Optional geocoding, after setting AMAP_KEY in your local environment:
python scripts/geocode_patents.py --input data/raw/incopat_export.csv --output data/raw/geocoded.csv
```

The offline demo uses intentionally fictional patent identifiers, coordinates, dates and value scores; the five-row observed sample in `examples/` comes from the supplied exploratory Notebook and is not a screened digital-patent sample.
