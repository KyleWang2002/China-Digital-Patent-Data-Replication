import io
import unittest
import pandas as pd
import numpy as np
from patentrep.records import normalize_records
from patentrep.classify import classify_patents, contains_term
from patentrep.coords import haversine_km,wgs84_to_gcj02,gcj02_to_wgs84,standardize_wgs84
from patentrep.spatial import match_stations,daily_station_stock
from patentrep.browser_capture import parse_detail_html

class PipelineTests(unittest.TestCase):
    def fixture(self):
        pat=normalize_records(pd.DataFrame([
            {'申请号':'CN001','申请日':'20200101','标题':'人工智能设备','经度':'121.4737',
             '纬度':'31.2304','坐标系':'wgs84','合享价值度':'8'},
            {'申请号':'CN002','申请日':'20200103','标题':'区块链平台','经度':'121.475',
             '纬度':'31.2304','坐标系':'wgs84','合享价值度':''},
        ]))
        stations=pd.DataFrame([{'station_id':'S1','longitude':121.4737,'latitude':31.2304,'coordinate_system':'wgs84'},
                {'station_id':'S2','longitude':122.0,'latitude':31.2,'coordinate_system':'wgs84'}])
        return pat,stations
    def test_chinese_fields_and_dates(self):
        d,_=self.fixture();self.assertEqual(d.loc[0,'application_no'],'CN001')
        self.assertEqual(d.loc[0,'application_date'],pd.Timestamp('2020-01-01'))
    def test_deduplicate_application_no(self):
        d,_=self.fixture();self.assertEqual(len(normalize_records(pd.concat([d,d],ignore_index=True))),2)
    def test_missing_identifier_rejected(self):
        with self.assertRaises(ValueError):normalize_records(pd.DataFrame([{'标题':'missing'}]))
    def test_short_english_token_not_inside_word(self):
        self.assertFalse(contains_term('CERTAIN CLAIM','AI'))
        self.assertTrue(contains_term('AI 系统','AI'))
    def test_classification(self):
        p,_=self.fixture();c=classify_patents(p,{'artificial_intelligence':['人工智能'],'blockchain':['区块链']})
        self.assertEqual(c.loc[0,'tech_category'],'artificial_intelligence')
        self.assertTrue(c.loc[1,'candidate_digital'])
    def test_multi_label_needs_review(self):
        p,_=self.fixture();p.loc[0,'title']='人工智能区块链'
        c=classify_patents(p,{'artificial_intelligence':['人工智能'],'blockchain':['区块链']})
        self.assertTrue(c.loc[0,'needs_review']);self.assertEqual(c.loc[0,'tech_category'],'')
    def test_gcj02_round_trip(self):
        gcj=wgs84_to_gcj02(116.404,39.915)
        lon,lat=gcj02_to_wgs84(*gcj)
        self.assertAlmostEqual(lon,116.404,places=5);self.assertAlmostEqual(lat,39.915,places=5)
    def test_require_explicit_crs(self):
        p,_=self.fixture();p.loc[0,'coordinate_system']=''
        with self.assertRaises(ValueError):standardize_wgs84(p)
    def test_haversine(self):
        self.assertAlmostEqual(float(haversine_km(121,31,121,31)),0.0)
        self.assertGreater(float(haversine_km(121,31,121,32)),100)
    def test_matching_5km(self):
        p,s=self.fixture();m=match_stations(p,s,5)
        self.assertEqual(len(m),2);self.assertEqual(set(m.station_id),{'S1'})
    def test_stock_missing_values(self):
        p,s=self.fixture();m=match_stations(p,s,5)
        r=daily_station_stock(m,s,'2020-01-01','2020-01-04')
        first=r[(r.station_id=='S1')&(r.date==pd.Timestamp('2020-01-02'))].iloc[0]
        second=r[(r.station_id=='S1')&(r.date==pd.Timestamp('2020-01-04'))].iloc[0]
        self.assertEqual(first.patent_value_stock,8)
        self.assertEqual(second.patent_count_stock,2)
        self.assertTrue(np.isnan(second.patent_value_stock))
    def test_zero_station(self):
        p,s=self.fixture();m=match_stations(p,s,5)
        r=daily_station_stock(m,s,'2020-01-01','2020-01-02')
        self.assertEqual(r[r.station_id=='S2'].patent_count_stock.sum(),0)
    def test_html_parser(self):
        html="""<div class="title"><span class="overflow" title="测试专利"></span></div>
          <div class="fold_con"><table class="tablelist1"><tbody>
          <tr><td>申请号</td><td>CN123</td></tr><tr><td>申请日</td><td>20250101</td></tr>
          </tbody></table></div>"""
        r=parse_detail_html(html)
        self.assertEqual(r['application_no'],'CN123');self.assertEqual(r['title'],'测试专利')
    def test_no_partial_html(self):
        with self.assertRaises(ValueError):parse_detail_html('<p>empty</p>')

if __name__=='__main__':unittest.main()
