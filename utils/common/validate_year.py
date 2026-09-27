from datetime import date


def validate_year(year_str: str) -> tuple[bool, str]:
    if not year_str:
        return True, ""

    year_str = year_str.strip()

    if not year_str.isdigit():
        return False, "年份必须是数字"

    year = int(year_str)
    current_year = date.today().year

    if year < 2000:
        return False, "年份不能早于2000年"
    if year > current_year + 1:
        return False, f"年份不能晚于{current_year + 1}年"

    return True, ""
