"""Transparent, exploratory dictionary screening (not the paper's full lexicon)."""
import re
from pathlib import Path
import pandas as pd

CATEGORIES = ("artificial_intelligence","big_data","cloud_computing","blockchain","5g_communication")

def load_keywords(path: str | Path) -> dict[str,list[str]]:
    frame = pd.read_csv(path).fillna('')
    if not {'category','keyword'}.issubset(frame): raise ValueError('Lexicon needs category and keyword')
    res = {x: [] for x in CATEGORIES}
    for row in frame.itertuples(index=False):
        if row.category not in res: raise ValueError(f'Unknown category: {row.category}')
        if str(row.keyword).strip(): res[row.category].append(str(row.keyword).strip())
    return res

def contains_term(text: str, term: str) -> bool:
    # Avoid interpreting embedded 'ai' in unrelated English words as artificial intelligence.
    if re.fullmatch(r'[a-zA-Z0-9]+',term) and len(term)<=3:
        return bool(re.search(r'(?<![a-zA-Z0-9])'+re.escape(term)+r'(?![a-zA-Z0-9])',text,re.I))
    return term.casefold() in text.casefold()

def classify_patents(frame:pd.DataFrame, lexicon:dict[str,list[str]]) -> pd.DataFrame:
    df=frame.copy()
    matches=[];terms=[]
    for r in df.itertuples(index=False):
        text=' '.join(str(getattr(r,c,'')) for c in ('title','abstract','claims'))
        hits={cat:[kw for kw in lexicon.get(cat,[]) if contains_term(text,kw)] for cat in CATEGORIES}
        present=[cat for cat in CATEGORIES if hits[cat]]
        matches.append(';'.join(present))
        terms.append(';'.join(dict.fromkeys(kw for cat in present for kw in hits[cat])))
    df['matched_categories']=matches
    df['matched_keywords']=terms
    df['candidate_digital']=df['matched_categories'].ne('')
    # Existing reviewed labels take priority. Otherwise single-category candidates only.
    old=df['tech_category'].fillna('').astype(str).str.strip()
    auto=df['matched_categories'].map(lambda x:x if ';' not in x else '')
    df['tech_category']=old.where(old.ne(''),auto)
    df['needs_review']=(df['matched_categories'].str.contains(';',regex=False) & old.eq(''))
    return df
