from database import get_session, Person
from utils import safe_str
from .backup_database import backup_database
from ._read_excel_robust import _read_excel_robust
from ._row_to_person import _row_to_person
from ._update_person_from_row import _update_person_from_row


def import_excel_incremental(file_path: str, progress_callback=None) -> dict:
    backup_database()
    df = _read_excel_robust(file_path, header=0)
    df = df.fillna("")
    total = len(df)
    imported = 0
    updated = 0
    skipped = 0
    errors = []
    session = get_session()
    try:
        for idx, row in df.iterrows():
            try:
                id_card = safe_str(row.get("身份证号", ""))
                if not id_card:
                    skipped += 1
                    continue
                existing = session.query(Person).filter(Person.id_card == id_card).first()
                if existing:
                    _update_person_from_row(existing, row)
                    updated += 1
                else:
                    person = _row_to_person(row, idx)
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
    return {"imported": imported, "updated": updated, "skipped": skipped, "errors": errors, "total": total}
