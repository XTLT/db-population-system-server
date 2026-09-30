from database import get_session, Person
from utils import validate_id_card
from .backup_database import backup_database
from ._read_excel_robust import _read_excel_robust
from ._row_to_person import _row_to_person


def import_excel_full(file_path: str, progress_callback=None) -> dict:
    backup_database()
    df = _read_excel_robust(file_path, header=0)
    df = df.fillna("")
    total = len(df)
    imported = 0
    skipped = 0
    errors = []
    session = get_session()
    try:
        session.query(Person).delete()
        session.commit()
        for idx, row in df.iterrows():
            try:
                person = _row_to_person(row, idx)
                id_card = person.id_card or ""
                if id_card:
                    valid, msg = validate_id_card(id_card)
                    if not valid:
                        skipped += 1
                        errors.append(f"行{idx + 2}: 身份证号 {id_card} 无效（{msg}）")
                        continue
                session.add(person)
                imported += 1
                if progress_callback:
                    progress_callback(int((idx + 1) / total * 100))
            except Exception as e:
                skipped += 1
                errors.append(f"行{idx + 2}: {str(e)}")
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
    return {"imported": imported, "skipped": skipped, "errors": errors, "total": total}
