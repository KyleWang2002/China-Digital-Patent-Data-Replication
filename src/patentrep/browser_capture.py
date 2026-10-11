"""Optional supervised browser capture from an authorized, manually opened IncoPat session.

No unattended login, CAPTCHA handling, hidden API calls, or restriction evasion.
Page selectors reflect an earlier exploratory notebook and may require adjustment.
"""
from __future__ import annotations
import argparse,csv,time
from pathlib import Path
from bs4 import BeautifulSoup

ALIASES={
  '申请号':'application_no','申请日':'application_date','标准申请人':'standardized_applicant',
  '申请人(原始)':'applicant','申请人（原始）':'applicant','申请人地址':'applicant_address',
  '公开(公告)号':'publication_no','公开(公告)日':'publication_date',
  '合享价值度':'value_score','摘要':'abstract','当前权利人':'current_owner',
}
OUT_FIELDS=['title','application_no','application_date','standardized_applicant','applicant',
 'applicant_address','publication_no','publication_date','abstract','value_score','current_owner']

def parse_detail_html(html:str,title_selector:str='div.title span.overflow',panel_selector:str='div.fold_con') ->dict[str,str]:
    soup=BeautifulSoup(html,'html.parser')
    title_node=soup.select_one(title_selector)
    panel=soup.select_one(panel_selector)
    if title_node is None or panel is None:raise ValueError('Could not locate title or detail panel; check selectors and page state')
    title=(title_node.get('title') or title_node.get_text(' ',strip=True)).strip()
    out={f:'' for f in OUT_FIELDS};out['title']=title
    for tr in panel.select('table.tablelist1 tbody tr'):
        cells=tr.find_all('td',recursive=False)
        if len(cells)<2:continue
        key=cells[0].get_text(' ',strip=True).rstrip('：:')
        canonical=ALIASES.get(key)
        if canonical:out[canonical]=cells[1].get_text(' ',strip=True).rstrip(';；')
    return out

def append_unique_csv(row:dict[str,str],out_path:Path):
    out_path.parent.mkdir(parents=True,exist_ok=True)
    if out_path.exists():
        with out_path.open(encoding='utf-8-sig',newline='') as f:
            existing={r['application_no'] for r in csv.DictReader(f) if r.get('application_no')}
        if row.get('application_no') and row['application_no'] in existing:return False
    create=not out_path.exists()
    with out_path.open('a',encoding='utf-8-sig',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=OUT_FIELDS)
        if create:writer.writeheader()
        writer.writerow({k:row.get(k,'') for k in OUT_FIELDS})
    return True

def main(argv=None):
    p=argparse.ArgumentParser(description='Supervised IncoPat detail capture (requires permitted access and manual login).')
    p.add_argument('--output',default='data/raw/incopat_export.csv')
    p.add_argument('--max-records',type=int,default=5)
    p.add_argument('--interval',type=float,default=2.5)
    p.add_argument('--title-selector',default='div.title span.overflow')
    p.add_argument('--panel-selector',default='div.fold_con')
    p.add_argument('--next-selector',default='#nextBtn')
    args=p.parse_args(argv)
    if not 1<=args.max_records<=100:raise ValueError('--max-records must be 1 to 100')
    if args.interval<2:raise ValueError('--interval must be at least 2 seconds')
    try:
        from selenium import webdriver
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
    except ImportError as exc:raise SystemExit('Install optional dependencies: pip install -e ".[browser]"') from exc
    driver=webdriver.Chrome()
    try:
        driver.get('https://t.incopat.com/newLogin?locale=zh')
        input('Log in through the official interface and open a patent detail record. Press Enter to begin capturing: ')
        wait=WebDriverWait(driver,20)
        last_id=''
        for k in range(args.max_records):
            wait.until(lambda d: d.find_elements(By.CSS_SELECTOR,args.title_selector) and d.find_elements(By.CSS_SELECTOR,args.panel_selector))
            row=parse_detail_html(driver.page_source,args.title_selector,args.panel_selector)
            if not row.get('application_no'):
                print('No application number detected; stopping rather than save an incomplete row.');break
            if row['application_no']==last_id:
                print('Unchanged record; stopping.');break
            added=append_unique_csv(row,Path(args.output))
            print(f"{k+1}/{args.max_records}: {row['application_no']} {'saved' if added else 'duplicate'}")
            last_id=row['application_no']
            if k+1>=args.max_records:break
            buttons=driver.find_elements(By.CSS_SELECTOR,args.next_selector)
            if not buttons or not buttons[0].is_enabled():break
            time.sleep(args.interval)
            buttons[0].click()
            try:
                wait.until(lambda d: parse_detail_html(d.page_source,args.title_selector,args.panel_selector).get('application_no') != last_id)
            except Exception:
                print('Next record did not load; stopped safely.');break
    finally:driver.quit()

if __name__=='__main__':main()
