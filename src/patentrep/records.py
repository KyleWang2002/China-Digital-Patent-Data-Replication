"""Normalize multilingual IncoPat patent metadata without inventing missing values."""
from __future__ import annotations
import pandas as pd

FIELDS = {
    "申请号": "application_no", "专利申请号": "application_no", "申请日": "application_date",
    "标题": "title", "专利名称": "title", "摘要": "abstract", "权利要求": "claims",
    "标准申请人": "standardized_applicant", "申请人(原始)": "applicant",
    "申请人（原始）": "applicant", "申请人地址": "applicant_address",
    "公开(公告)号": "publication_no", "公开（公告）号": "publication_no",
    "公开(公告)日": "publication_date", "公开（公告）日": "publication_date",
    "合享价值度": "value_score", "价值度": "value_score",
    "技术分类": "tech_category", "经度": "longitude", "纬度": "latitude",
    "坐标系": "coordinate_system",
}
DATE_COLS = ("application_date", "publication_date")
TEXT_COLS = ("application_no", "title", "abstract", "claims", "applicant", "standardized_applicant",
             "applicant_address", "publication_no", "tech_category", "coordinate_system")

def normalize_records(frame: pd.DataFrame) -> pd.DataFrame:
    """Return canonical columns, keeping empty identifiers empty rather than 'nan'."""
    df = frame.rename(columns=lambda c: FIELDS.get(str(c).strip(), str(c).strip())).copy()
    if df.columns.duplicated().any():
        raise ValueError("Duplicate columns after normalizing headers")
    for c in TEXT_COLS:
        if c not in df.columns: df[c] = ""
        df[c] = df[c].fillna("").astype(str).str.strip()
    for c in DATE_COLS:
        if c not in df.columns: df[c] = pd.NaT
        # Distinguish YYYYMMDD floats from usable strings.
        raw = df[c].astype('string').str.replace(r'\.0$', '', regex=True).str.strip()
        raw = raw.replace({'': pd.NA, 'nan': pd.NA, 'NaT':pd.NA, '<NA>':pd.NA})
        df[c] = pd.to_datetime(raw, format='mixed', errors='coerce')
    for c in ('latitude','longitude','value_score'):
        if c not in df.columns: df[c] = float('nan')
        df[c] = pd.to_numeric(df[c], errors='coerce')
    if (df['value_score'].dropna()<0).any(): raise ValueError("value_score must be nonnegative")
    if ((df['latitude'].dropna().abs()>90).any() or (df['longitude'].dropna().abs()>180).any()):
        raise ValueError("Invalid latitude / longitude")
    # Known patent application IDs should be unique. Empty IDs require explicit review.
    df['record_key'] = df['application_no'].where(df['application_no'].ne(''), df['publication_no'])
    if df['record_key'].eq('').any(): raise ValueError("Missing application_no and publication_no for one or more rows")
    return df.drop_duplicates('record_key',keep='first').reset_index(drop=True)

def load_patents(path: str) -> pd.DataFrame:
    return normalize_records(pd.read_csv(path, dtype=str, encoding='utf-8-sig'))
