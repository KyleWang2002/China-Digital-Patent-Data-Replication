"""Reproducible offline pipeline from licensed patent exports to station-day measures."""
from __future__ import annotations
import argparse
from pathlib import Path
import pandas as pd
from .records import load_patents
from .classify import load_keywords,classify_patents
from .coords import standardize_wgs84
from .spatial import load_stations,match_stations,daily_station_stock

def run(patents_csv:str,stations_csv:str,lexicon_csv:str,output_dir:str,start:str,end:str,
        radius_km:float=5.0,category:str|None=None):
    out=Path(output_dir);out.mkdir(parents=True,exist_ok=True)
    patents=load_patents(patents_csv)
    patents=classify_patents(patents,load_keywords(lexicon_csv))
    patents=standardize_wgs84(patents)
    stations=standardize_wgs84(load_stations(stations_csv))
    patents.to_csv(out/'patents_normalized.csv',index=False,encoding='utf-8-sig')
    # Use records assigned a single screening category or provided with a reviewed label.
    # Ambiguous multi-category records stay in the screening output for manual review.
    eligible=patents[patents['tech_category'].ne('')].copy()
    matches=match_stations(eligible,stations,radius_km)
    matches.to_csv(out/'patent_station_matches.csv',index=False,encoding='utf-8-sig')
    daily=daily_station_stock(matches,stations,start,end,category)
    daily.to_csv(out/'station_daily_stock.csv',index=False,encoding='utf-8-sig')
    summary=pd.DataFrame([{'input_patents':len(patents),'keyword_candidates':int(patents['candidate_digital'].sum()),
        'patents_with_coordinates':int(patents['latitude'].notna().sum()),'stations':len(stations),
        'matched_patent_station_pairs':len(matches),'station_days':len(daily),
        'unscored_patents':int(eligible['value_score'].isna().sum()),
        'category':category or 'ALL','radius_km':radius_km}])
    summary.to_csv(out/'processing_summary.csv',index=False)
    return summary

def main(argv=None):
    p=argparse.ArgumentParser()
    p.add_argument('--patents',required=True);p.add_argument('--stations',required=True)
    p.add_argument('--lexicon',default='data/lexicon/digital_terms.csv')
    p.add_argument('--out',default='outputs');p.add_argument('--start',required=True);p.add_argument('--end',required=True)
    p.add_argument('--radius-km',type=float,default=5)
    p.add_argument('--category',default='ALL')
    a=p.parse_args(argv)
    print(run(a.patents,a.stations,a.lexicon,a.out,a.start,a.end,a.radius_km,a.category).to_string(index=False))

if __name__=='__main__':main()
