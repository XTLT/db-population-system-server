function calculateEnrollmentAndGraduation() {
    const grade = document.getElementById('editEduGrade').value;
    if (!grade) return;

    const now = new Date();
    const currentYear = now.getFullYear();
    const currentMonth = now.getMonth() + 1;

    const gradeToYears = {
        '一年级': 6, '二年级': 5, '三年级': 4, '四年级': 3, '五年级': 2, '六年级': 1,
        '七年级': 3, '八年级': 2, '九年级': 1,
        '高一': 3, '高二': 2, '高三': 1,
    };

    const gradeToOffset = {
        '一年级': 0, '二年级': 1, '三年级': 2, '四年级': 3, '五年级': 4, '六年级': 5,
        '七年级': 0, '八年级': 1, '九年级': 2,
        '高一': 0, '高二': 1, '高三': 2,
    };

    const offset = gradeToOffset[grade] ?? 0;
    const totalYears = gradeToYears[grade] ?? 0;

    let enrollmentYear;
    if (currentMonth >= 9) {
        enrollmentYear = currentYear - offset;
    } else {
        enrollmentYear = currentYear - offset - 1;
    }

    const enrollDateField = document.getElementById('editEduEnrollDate');
    const gradDateField = document.getElementById('editEduGradDate');

    if (!enrollDateField.value) {
        enrollDateField.value = `${enrollmentYear}-09`;
    }

    if (!gradDateField.value && totalYears > 0) {
        const gradYear = enrollmentYear + totalYears;
        gradDateField.value = `${gradYear}-06`;
    }
}
