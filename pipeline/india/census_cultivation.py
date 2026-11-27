"""Prepare urban-district resident cultivation shares from Census 2011 PCA SD."""

import argparse
from pathlib import Path

from ..core.store import load_interim, save_interim
from .census_work_sources import CULTIVATION_INTERIM, CULTIVATION_SOURCE, PCA_WORKBOOK

CULTIVATION = ("MAIN_CL_P", "MAIN_AL_P", "MARG_CL_P", "MARG_AL_P")


def cultivation_share(row):
    total = row["TOT_WORK_P"]
    count = sum(row[key] for key in CULTIVATION)
    if row["MAINWORK_P"] + row["MARGWORK_P"] != total or not 0 <= count <= total:
        raise ValueError("Inconsistent PCA SD worker totals")
    return round(count / total, 6) if total else None


def urban_districts(rows):
    header = next(rows)
    result = {}
    for cells in rows:
        row = dict(zip(header, cells))
        if str(row.get("Level", "")).casefold() != "district" or row["TRU"] != "Urban":
            continue
        code = f"{int(row['State']):02d}-{int(row['District']):03d}"
        if code in result:
            raise ValueError(f"Duplicate urban district {code}")
        share = cultivation_share(row)
        result[code] = None if share is None else {
            "value": share, "workers": row["TOT_WORK_P"], "cultivation_workers": sum(row[key] for key in CULTIVATION),
        }
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workbook", type=Path)
    args = parser.parse_args()
    expected = {f"{d['state_code']:02d}-{d['code']:03d}" for d in load_interim("datameet")["districts"]}
    shares = urban_districts(PCA_WORKBOOK.rows(args.workbook))
    if shares.keys() != expected:
        raise ValueError("PCA SD district keys do not match the IndiaCiv map")
    save_interim(CULTIVATION_INTERIM, {
        "districts": {code: {**record, "period": "Census 2011", "vintage": "older",
                             "source": CULTIVATION_SOURCE, "coverage": "Urban residents of the 2011 district"}
                      for code, record in shares.items() if record is not None},
    })


if __name__ == "__main__":
    main()
