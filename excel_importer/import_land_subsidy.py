import secrets
from datetime import datetime
from database import get_session, LandSubsidy
from utils import safe_str
from ._read_excel_robust import _read_excel_robust


def import_land_subsidy(file_path: str, subsidy_year: str = "", progress_callback=None) -> dict:

    df = _read_excel_robust(file_path, header=None)
    df = df.fillna("")

    header_row = -1
    for idx, row in df.iterrows():
        values = [str(v).strip() for v in row.values]
        if "姓名" in values and "身份证号" in values:
            header_row = idx
            break

    if header_row == -1:
        return {"imported": 0, "skipped": 0, "errors": ["未找到表头（姓名、身份证号）"], "total": 0}

    main_headers = [str(v).strip() for v in df.iloc[header_row].values]

    # 检查是否需要处理副表头
    # 如果下一行的第一个单元格是数字（如补贴年度）或身份证号格式，则认为是数据行，不需要副表头
    use_sub_header = False
    if header_row + 1 < len(df):
        next_row = [str(v).strip() for v in df.iloc[header_row + 1].values]
        # 检查下一行是否是数据行（通常数据行的补贴年度是年份，身份证号是数字）
        # 如果下一行不包含"姓名"、"身份证号"等表头关键词，则认为是数据行
        header_keywords = ["姓名", "身份证", "补贴", "面积", "金额", "标准"]
        has_header_keyword = any(kw in " ".join(next_row) for kw in header_keywords)
        if has_header_keyword:
            use_sub_header = True
            sub_headers = next_row
        else:
            sub_headers = [""] * len(main_headers)
    else:
        sub_headers = [""] * len(main_headers)

    col_map = {}
    for i, (main, sub) in enumerate(zip(main_headers, sub_headers)):
        if main:
            if sub:
                col_map[i] = f"{main}_{sub}"
            else:
                col_map[i] = main
        elif sub:
            col_map[i] = sub
        else:
            col_map[i] = f"col_{i}"

    # 根据是否使用副表头，决定数据起始行
    data_start_row = header_row + 2 if use_sub_header else header_row + 1
    data_df = df.iloc[data_start_row:].reset_index(drop=True)
    data_df.columns = [col_map.get(i, f"col_{i}") for i in range(len(col_map))]

    total = len(data_df)
    imported = 0
    skipped = 0
    errors = []
    session = get_session()

    try:
        for idx, row in data_df.iterrows():
            try:
                name = safe_str(row.get("姓名", ""))
                id_card = safe_str(row.get("身份证号", ""))

                if not name and not id_card:
                    skipped += 1
                    continue

                certified_area = ""
                for key in row.index:
                    if "确权颁证面积" in key or "确权颁发面积" in key:
                        certified_area = safe_str(row.get(key, ""))
                        break

                subsidy_area = ""
                for key in row.index:
                    if "补贴面积" in key:
                        val = safe_str(row.get(key, ""))
                        subsidy_area = val.replace("（亩）", "").replace("(亩)", "").strip()
                        break

                base_standard = ""
                for key in row.index:
                    if "基础补贴标准" in key:
                        val = safe_str(row.get(key, ""))
                        base_standard = val.replace("（元/亩）", "").replace("(元/亩)", "").strip()
                        break

                rape_area = ""
                for key in row.index:
                    if "其中种植油菜" in key and "面积" in key:
                        rape_area = safe_str(row.get(key, "")).strip()
                        break

                rape_amount = ""
                for key in row.index:
                    if "其中种植油菜" in key and "金额" in key:
                        rape_amount = safe_str(row.get(key, "")).strip()
                        break

                total_amount = ""
                for key in row.index:
                    if "补贴总金额" in key:
                        val = safe_str(row.get(key, ""))
                        total_amount = val.replace("（元）", "").replace("(元)", "").strip()
                        break

                subsidy = LandSubsidy(
                    id=f"ls_{secrets.token_hex(8)}",
                    id_card=id_card,
                    name=name,
                    subsidy_year=subsidy_year,
                    certified_area=certified_area,
                    subsidy_area=subsidy_area,
                    base_standard=base_standard,
                    rape_area=rape_area,
                    rape_amount=rape_amount,
                    total_amount=total_amount,
                    import_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                )
                session.add(subsidy)
                imported += 1

                if progress_callback:
                    progress_callback(int((idx + 1) / total * 100))
            except Exception as e:
                skipped += 1
                errors.append(f"行{idx + header_row + 3}: {str(e)}")

        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

    return {"imported": imported, "skipped": skipped, "errors": errors, "total": total}
