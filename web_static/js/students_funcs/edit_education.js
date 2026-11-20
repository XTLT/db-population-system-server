function editEducation(personId, name, school, grade, className, guardian, guardianPhone, isLeftBehind, status, enrollDate) {
    document.getElementById('eduPersonId').value = personId;
    document.getElementById('eduName').value = name;
    document.getElementById('eduSchool').value = school || '';
    document.getElementById('eduClass').value = className || '';
    document.getElementById('eduGuardian').value = guardian || '';
    document.getElementById('eduGuardianPhone').value = guardianPhone || '';
    document.getElementById('eduLeftBehind').value = isLeftBehind || '否';
    document.getElementById('eduStatus').value = status || '在读';
    document.getElementById('eduEnrollDate').value = enrollDate || '';

    const gradeSelect = document.getElementById('eduGrade');
    if (gradeSelect.options.length <= 1) {
        const grades = [
            ['','请选择'],['T1','托班'],
            ['K1','幼儿园小班'],['K2','幼儿园中班'],['K3','幼儿园大班'],
            ['G1','小学1年级'],['G2','小学2年级'],['G3','小学3年级'],['G4','小学4年级'],['G5','小学5年级'],['G6','小学6年级'],
            ['G7','初中1年级'],['G8','初中2年级'],['G9','初中3年级'],
            ['G10','高中1年级'],['G11','高中2年级'],['G12','高中3年级'],
            ['V1','职高1年级'],['V2','职高2年级'],['V3','职高3年级'],
            ['C1','中专1年级'],['C2','中专2年级'],['C3','中专3年级'],
            ['U1','大学1年级'],['U2','大学2年级'],['U3','大学3年级'],['U4','大学4年级'],['U5','大学5年级'],
            ['M1','硕士1年级'],['M2','硕士2年级'],['M3','硕士3年级'],
            ['D1','博士1年级'],['D2','博士2年级'],['D3','博士3年级'],['D4','博士4年级'],
            ['GRADUATED','已毕业']
        ];
        grades.forEach(([code, label]) => {
            const opt = document.createElement('option');
            opt.value = code;
            opt.textContent = label;
            gradeSelect.appendChild(opt);
        });
    }
    gradeSelect.value = grade || '';

    document.getElementById('eduEditModal').style.display = 'flex';
}
