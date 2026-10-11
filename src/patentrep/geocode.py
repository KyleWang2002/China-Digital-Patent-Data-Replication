"""Optional licensed address geocoding with explicit Amap key and disk cache."""
from __future__ import annotations
import json,os,time
from pathlib import Path
import pandas as pd
import requests
from .coords import gcj02_to_wgs84

GEOCODE_URL='https://restapi.amap.com/v3/geocode/geo'

def geocode_amap(records:pd.DataFrame,cache_path:str, key:str|None=None,delay:float=0.6)->pd.DataFrame:
    """Geocode applicant_address only after explicit opt-in; Amap responds in GCJ-02.

    Never infer unknown addresses or silently substitute city centroids.
    """
    token=key or os.environ.get('AMAP_KEY')
    if not token:raise ValueError('Set AMAP_KEY in your environment; never commit API keys')
    if delay<0.5:raise ValueError('Delay should be >= 0.5 seconds')
    p=Path(cache_path);p.parent.mkdir(parents=True,exist_ok=True)
    cache=json.loads(p.read_text(encoding='utf-8')) if p.exists() else {}
    out=records.copy()
    for idx,r in out.iterrows():
        if pd.notna(r.get('latitude')) and pd.notna(r.get('longitude')):continue
        address=str(r.get('applicant_address') or '').strip()
        if not address:continue
        if address not in cache:
            res=requests.get(GEOCODE_URL,params={'key':token,'address':address},timeout=20)
            res.raise_for_status();payload=res.json()
            if str(payload.get('status'))!='1':raise RuntimeError('Geocode request rejected: '+str(payload.get('info','unknown error')))
            items=payload.get('geocodes',[])
            location=items[0].get('location','') if len(items)==1 else ''
            cache[address]={'location':location,'count':len(items)}
            p.write_text(json.dumps(cache,ensure_ascii=False,indent=2),encoding='utf-8')
            time.sleep(delay)
        location=cache[address].get('location','')
        if location:
            lon,lat=map(float,location.split(','))
            # Output WGS84 because station coordinates must be in a common CRS.
            lon,lat=gcj02_to_wgs84(lon,lat)
            out.at[idx,'longitude']=lon;out.at[idx,'latitude']=lat
            out.at[idx,'coordinate_system']='wgs84'
            out.at[idx,'geocode_status']='amap_geocoded'
        else:out.at[idx,'geocode_status']='unresolved'
    return out
