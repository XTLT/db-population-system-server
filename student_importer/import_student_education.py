from datetime import datetime
from config import GRADES
from database import get_session, StudentEducation, EducationHistory, Person
from utils import safe_str
from .backup_database import backup_database
from ._read_excel_robust import _read_excel_robust


def import_student_education(file_path: str, mode: str = "incremental", progress_callback=None) -> dict:
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
                    errors.append(f"行{idx + 2}: 身份证号为空")
                    continue

                person = session.query(Person).filter(Person.id_card == id_card).first()
                if not person:
                    skipped += 1
                    errors.append(f"行{idx + 2}: 身份证号 {id_card} 不存在")
                    continue

                grade = safe_str(row.get("年级", ""))
                if grade and grade not in GRADES:
                    skipped += 1
                    errors.append(f"行{idx + 2}: 年级 {grade} 不合法")
                    continue

                existing = session.query(StudentEducation).filter(
                    StudentEducation.person_id == person.id
                ).first()

                if existing:
                    old_grade = existing.grade
                    existing.school_name = safe_str(row.get("学校名称", existing.school_name))
                    existing.grade = grade or existing.grade
                    existing.class_name = safe_str(row.get("班级", existing.class_name))
                    existing.guardian = safe_str(row.get("监护人", existing.guardian))
                    existing.guardian_phone = safe_str(row.get("监护人电话", existing.guardian_phone))
                    existing.is_left_behind = safe_str(row.get("是否留守儿童", existing.is_left_behind))
                    existing.student_status = safe_str(row.get("学生状态", existing.student_status))
                    existing.enrollment_date = safe_str(row.get("入学日期", existing.enrollment_date))
                    updated += 1

                    if old_grade != existing.grade:
                        history = EducationHistory(
                            id=f"hist_{datetime.now().strftime('%Y%m%d%H%M%S')}_{person.id}",
                            person_id=person.id,
                            id_card=id_card,
                            school_name=existing.school_name,
                            grade=old_grade,
                            class_name=existing.class_name,
                            student_status=existing.student_status,
                            change_date=datetime.now().strftime("%Y-%m-%d"),
                            change_reason="Excel导入更新"
                        )
                        session.add(history)
                else:
                    edu = StudentEducation(
                        id=f"edu_{person.id}",
                        person_id=person.id,
                        id_card=id_card,
                        school_name=safe_str(row.get("学校名称", "")),
                        grade=grade,
                        class_name=safe_str(row.get("班级", "")),
                        guardian=safe_str(row.get("监护人", "")),
                        guardian_phone=safe_str(row.get("监护人电话", "")),
                        is_left_behind=safe_str(row.get("是否留守儿童", "否")),
                        student_status=safe_str(row.get("学生状态", "")),
                        enrollment_date=safe_str(row.get("入学日期", ""))
                    )
                    session.add(edu)
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

    return {
        "imported": imported,
        "updated": updated,
        "skipped": skipped,
        "errors": errors,
        "total": total
    }
