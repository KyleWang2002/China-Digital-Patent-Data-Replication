"""Optional geocoding of applicant addresses using the user's own Amap API key."""
import argparse
import pandas as pd
from patentrep.records import load_patents
from patentrep.geocode import geocode_amap

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--input',required=True);p.add_argument('--output',required=True)
    p.add_argument('--cache',default='data/cache/geocoded_addresses.json')
    a=p.parse_args()
    raw=load_patents(a.input)
    result=geocode_amap(raw,a.cache)
    result.to_csv(a.output,index=False,encoding='utf-8-sig')
    print(f'Saved {len(result)} normalized records to {a.output}')
if __name__=='__main__':main()
