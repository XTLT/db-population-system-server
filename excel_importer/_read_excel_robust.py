import os
import pandas as pd


def _read_excel_robust(file_path: str, header=None):
    """读取 Excel 文件，自动检测格式和引擎"""
    ext = os.path.splitext(file_path)[1].lower()
    engines = (['openpyxl', 'xlrd'] if ext == '.xlsx'
               else ['xlrd', 'openpyxl'] if ext == '.xls'
               else ['openpyxl', 'xlrd'])
    for engine in engines:
        try:
            return pd.read_excel(file_path, dtype=str, header=header, engine=engine)
        except Exception:
            continue
    try:
        return pd.read_csv(file_path, dtype=str, header=header, encoding='utf-8')
    except Exception:
        return pd.read_csv(file_path, dtype=str, header=header, encoding='gbk')


def _engines_for(file_path: str):
    ext = os.path.splitext(file_path)[1].lower()
    if ext == '.xlsx':
        return ['openpyxl', 'xlrd']
    if ext == '.xls':
        return ['xlrd', 'openpyxl']
    return ['openpyxl', 'xlrd']


def _read_excel_with_header(file_path: str, known_columns, max_scan: int = 12):
    """自动定位表头行并读取完整 DataFrame。

    known_columns: 该模板已知列名列表（用于匹配定位表头行）。
    1) 用引擎探测读前 max_scan 行（header=None, dtype=str）；
    2) 逐行统计该行非空单元格与 known_columns 的精确匹配数（值 strip，过滤 "" 与 "nan"）；
    3) 取匹配数最大的行为表头行；最大匹配数 < 2 则回退 header=0；
    4) 用该行号调 _read_excel_robust(file_path, header=header_row) 返回完整 df。
    """
    known = {str(c).strip() for c in known_columns}
    raw = None
    for engine in _engines_for(file_path):
        try:
            raw = pd.read_excel(file_path, dtype=str, header=None, nrows=max_scan, engine=engine)
            break
        except Exception:
            continue

    header_row = 0
    if raw is not None and len(raw) > 0:
        best_row = 0
        best_hits = -1
        for r in range(len(raw)):
            hits = 0
            for v in raw.iloc[r].tolist():
                s = "" if v is None else str(v).strip()
                if s in ("", "nan"):
                    continue
                if s in known:
                    hits += 1
            if hits > best_hits:
                best_hits = hits
                best_row = r
        if best_hits >= 2:
            header_row = best_row

    return _read_excel_robust(file_path, header=header_row)
