"""Efficient geospatial patent -> monitoring-station matching."""
from __future__ import annotations
import numpy as np
import pandas as pd
from scipy.spatial import cKDTree
from .coords import R_KM, unit_sphere_xyz, haversine_km

def load_stations(path:str)->pd.DataFrame:
    df=pd.read_csv(path,dtype={'station_id':str},encoding='utf-8-sig')
    needed={'station_id','longitude','latitude','coordinate_system'}
    if not needed.issubset(df):raise ValueError('Station data must include station_id, latitude, longitude, coordinate_system')
    df['station_id']=df['station_id'].astype(str)
    if df['station_id'].duplicated().any():raise ValueError('Duplicate station_id')
    df[['longitude','latitude']]=df[['longitude','latitude']].apply(pd.to_numeric,errors='raise')
    return df

def match_stations(patents:pd.DataFrame,stations:pd.DataFrame,radius_km:float=5)->pd.DataFrame:
    if radius_km<=0 or radius_km>100:raise ValueError('radius_km must be in (0,100]')
    for name,df in [('patents',patents),('stations',stations)]:
        if not set(df['coordinate_system'].dropna().astype(str))<= {'wgs84'}:
            raise ValueError(f'{name}: convert all geocoded points to WGS84 before matching')
    pts=patents.dropna(subset=['longitude','latitude']).reset_index(drop=True)
    sts=stations.dropna(subset=['longitude','latitude']).reset_index(drop=True)
    cols=['station_id','application_no','application_date','tech_category','distance_km','value_score']
    if len(pts)==0 or len(sts)==0:return pd.DataFrame(columns=cols)
    tree=cKDTree(unit_sphere_xyz(pts.longitude,pts.latitude))
    arc=2*np.sin(radius_km/(2*R_KM))
    inds=tree.query_ball_point(unit_sphere_xyz(sts.longitude,sts.latitude),r=arc+1e-12)
    rows=[]
    for si, candidates in enumerate(inds):
        st=sts.iloc[si]
        for idx in candidates:
            p=pts.iloc[idx]
            d=float(haversine_km(st.longitude,st.latitude,p.longitude,p.latitude))
            if d<=radius_km+1e-7:
                rows.append({'station_id':st.station_id,'application_no':p.application_no,
                  'application_date':p.application_date,'tech_category':p.tech_category,
                  'distance_km':round(d,5),'value_score':p.value_score})
    return pd.DataFrame(rows,columns=cols).sort_values(['station_id','application_no']).reset_index(drop=True) if rows else pd.DataFrame(columns=cols)

def daily_station_stock(matches:pd.DataFrame,stations:pd.DataFrame,start:str,end:str,category:str|None=None)->pd.DataFrame:
    """Daily cumulative stock of patent counts and of observed proprietary value scores.

    A missing value score makes weighted stock unavailable when that patent is active,
    rather than silently using zero or equating patent counts with patent value.
    """
    days=pd.date_range(start,end,freq='D')
    if len(days)==0:raise ValueError('Empty date range')
    df=matches.copy()
    if category and category!='ALL':df=df[df['tech_category']==category]
    if not df.empty:df['application_date']=pd.to_datetime(df['application_date'],errors='coerce')
    frames=[]
    for sid in stations['station_id'].astype(str).unique():
        sub=df[df['station_id'].astype(str)==sid].dropna(subset=['application_date']).copy()
        sub=sub[sub['application_date']<=days[-1]].sort_values('application_date')
        dat=sub['application_date'].to_numpy(dtype='datetime64[ns]')
        indexes=np.searchsorted(dat,days.to_numpy(),side='right')
        count=indexes.astype(int)
        vals=pd.to_numeric(sub['value_score'],errors='coerce').to_numpy(dtype=float)
        weights=np.r_[0,np.cumsum(np.nan_to_num(vals,nan=0.0))]
        n_missing=np.r_[0,np.cumsum(~np.isfinite(vals))]
        v=weights[indexes].astype(float)
        v[n_missing[indexes]>0]=np.nan
        frames.append(pd.DataFrame({'station_id':sid,'date':days,'patent_count_stock':count,
                                    'patent_value_stock':v,'n_unscored_patents':n_missing[indexes]}))
    if not frames:return pd.DataFrame(columns=['station_id','date','patent_count_stock','patent_value_stock','n_unscored_patents'])
    return pd.concat(frames,ignore_index=True)
