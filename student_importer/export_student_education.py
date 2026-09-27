import pandas as pd
from config import STUDENT_EDUCATION_COLUMNS
from database import get_session, StudentEducation, Person


def export_student_education(file_path: str, progress_callback=None) -> bool:
    session = get_session()
    try:
        students = session.query(StudentEducation).all()
        if not students:
            return False

        data = []
        for i, s in enumerate(students):
            person = session.query(Person).filter(Person.id == s.person_id).first()
            data.append({
                "身份证号": s.id_card,
                "姓名": person.name if person else "",
                "学校名称": s.school_name,
                "年级": s.grade,
                "班级": s.class_name,
                "监护人": s.guardian,
                "监护人电话": s.guardian_phone,
                "是否留守儿童": s.is_left_behind,
                "学生状态": s.student_status,
                "入学日期": s.enrollment_date
            })
            if progress_callback and (i + 1) % 50 == 0:
                progress_callback(int((i + 1) / len(students) * 100))

        df = pd.DataFrame(data, columns=["身份证号", "姓名"] + STUDENT_EDUCATION_COLUMNS[1:])
        df.to_excel(file_path, index=False, engine="openpyxl")
        return True
    finally:
        session.close()
