"""Self-contained synthetic example: no credentials, no network."""
from pathlib import Path
from patentrep.pipeline import run

def main():
    base=Path(__file__).resolve().parents[1]
    summary=run(str(base/'data/example/patents_synthetic.csv'),
        str(base/'data/example/stations_synthetic.csv'),
        str(base/'data/lexicon/digital_terms.csv'),str(base/'outputs/demo'),
        '2020-01-01','2020-01-12',radius_km=5)
    print(summary.to_string(index=False))
    print('Outputs: '+str(base/'outputs/demo'))
if __name__=='__main__':main()
