import pandas as pd
from config import EXCEL_TEMPLATE_COLUMNS


def generate_template(file_path: str):
    df = pd.DataFrame(columns=EXCEL_TEMPLATE_COLUMNS)
    df.to_excel(file_path, index=False, engine="openpyxl")
