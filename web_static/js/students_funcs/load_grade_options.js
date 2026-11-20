function loadGradeOptions() {
    const gradeSelect = document.getElementById('stuGrade');
    if (gradeSelect.options.length > 1) return;
    const grades = [
        ['K1','幼儿园小班'],['K2','幼儿园中班'],['K3','幼儿园大班'],
        ['G1','小学1年级'],['G2','小学2年级'],['G3','小学3年级'],['G4','小学4年级'],['G5','小学5年级'],['G6','小学6年级'],
        ['G7','初中1年级'],['G8','初中2年级'],['G9','初中3年级'],
        ['G10','高中1年级'],['G11','高中2年级'],['G12','高中3年级']
    ];
    grades.forEach(([code, name]) => {
        const opt = document.createElement('option');
        opt.value = code;
        opt.textContent = name;
        gradeSelect.appendChild(opt);
    });
}
