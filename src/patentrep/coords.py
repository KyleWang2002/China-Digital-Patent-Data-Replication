"""Coordinate validation, GCJ-02 -> WGS84 conversion, geodesic distances."""
import math
import numpy as np
R_KM = 6371.0088

def _out_of_china(lon,lat): return lon<72.004 or lon>137.8347 or lat<0.8293 or lat>55.8271

def _transform_lat(x,y):
    return (-100+2*x+3*y+0.2*y*y+0.1*x*y+0.2*math.sqrt(abs(x))+
        (20*math.sin(6*x*math.pi)+20*math.sin(2*x*math.pi))*2/3+
        (20*math.sin(y*math.pi)+40*math.sin(y/3*math.pi))*2/3+
        (160*math.sin(y/12*math.pi)+320*math.sin(y*math.pi/30))*2/3)

def _transform_lon(x,y):
    return (300+x+2*y+0.1*x*x+0.1*x*y+0.1*math.sqrt(abs(x))+
        (20*math.sin(6*x*math.pi)+20*math.sin(2*x*math.pi))*2/3+
        (20*math.sin(x*math.pi)+40*math.sin(x/3*math.pi))*2/3+
        (150*math.sin(x/12*math.pi)+300*math.sin(x/30*math.pi))*2/3)

def wgs84_to_gcj02(lon,lat):
    if _out_of_china(lon,lat): return lon,lat
    a=6378245.0;ee=0.00669342162296594323
    dlat=_transform_lat(lon-105,lat-35);dlon=_transform_lon(lon-105,lat-35)
    radlat=lat/180*math.pi
    magic=1-ee*math.sin(radlat)**2
    sqrt_magic=math.sqrt(magic)
    dlat=dlat*180/((a*(1-ee))/(magic*sqrt_magic)*math.pi)
    dlon=dlon*180/(a/sqrt_magic*math.cos(radlat)*math.pi)
    return lon+dlon,lat+dlat

def gcj02_to_wgs84(lon,lat):
    if _out_of_china(lon,lat):return lon,lat
    # Iterative inverse of the standard forward approximation.
    wl,wa=lon,lat
    for _ in range(5):
        gl,ga=wgs84_to_gcj02(wl,wa)
        wl+=lon-gl; wa+=lat-ga
    return wl,wa

def standardize_wgs84(frame, crs_col='coordinate_system'):
    """Require explicit CRS for every geocoded record; missing CRS is not silently assumed."""
    out=frame.copy()
    if crs_col not in out: raise ValueError('coordinate_system column is required')
    for i,r in out.iterrows():
        if not np.isfinite(float(r['latitude'])) or not np.isfinite(float(r['longitude'])):continue
        crs=str(r[crs_col]).strip().lower()
        if crs=='gcj02':
            lon,lat=gcj02_to_wgs84(float(r['longitude']),float(r['latitude']))
            out.at[i,'longitude']=lon;out.at[i,'latitude']=lat;out.at[i,crs_col]='wgs84'
        elif crs=='wgs84':continue
        else:raise ValueError(f'Unknown coordinate system on row {i}: {crs!r}')
    return out

def haversine_km(lon1,lat1,lon2,lat2):
    lon1,lat1,lon2,lat2=np.radians([lon1,lat1,lon2,lat2])
    dl=lon2-lon1;da=lat2-lat1
    a=np.sin(da/2)**2+np.cos(lat1)*np.cos(lat2)*np.sin(dl/2)**2
    return 2*R_KM*np.arcsin(np.minimum(1,np.sqrt(a)))

def unit_sphere_xyz(lon,lat):
    lo=np.radians(np.asarray(lon,dtype=float));la=np.radians(np.asarray(lat,dtype=float))
    return np.column_stack((np.cos(la)*np.cos(lo),np.cos(la)*np.sin(lo),np.sin(la)))
