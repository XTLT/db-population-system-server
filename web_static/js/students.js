function showStudentModal() {
    document.getElementById('studentModal').style.display = 'flex';
    loadGradeOptions();
    searchStudents();
}

function closeStudentModal() {
    document.getElementById('studentModal').style.display = 'none';
}

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

function searchStudents() {
    const params = new URLSearchParams();
    const school = document.getElementById('stuSchool').value;
    const grade = document.getElementById('stuGrade').value;
    if (school) params.set('school', school);
    if (grade) params.set('grade', grade);

    apiRequest('GET', `/api/students/search?${params}`).then(students => {
        const tbody = document.getElementById('studentBody');
        tbody.innerHTML = '';
        if (students.length === 0) {
            tbody.innerHTML = '<tr><td colspan="9" style="color:#999;">没有学生数据</td></tr>';
            return;
        }
        const canEdit = userRole === 'admin' || userRole === 'user';
        students.forEach(s => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${s.name}</td>
                <td>${s.id_card}</td>
                <td>${s.school_name}</td>
                <td>${s.grade_display || s.grade}</td>
                <td>${s.class_name}</td>
                <td>${s.guardian}</td>
                <td>${s.is_left_behind}</td>
                <td>${s.student_status}</td>
                <td>${canEdit ? `<button onclick="editEducation('${s.person_id}','${s.name}','${s.school_name}','${s.grade}','${s.class_name}','${s.guardian}','${s.guardian_phone || ''}','${s.is_left_behind}','${s.student_status}','${s.enrollment_date || ''}')" class="btn-edit" style="padding:4px 8px;font-size:12px;">编辑</button>` : ''}</td>
            `;
            tbody.appendChild(tr);
        });
    });
}

function showStuImportModal() {
    document.getElementById('stuImportModal').style.display = 'flex';
    document.getElementById('stuImportFile').value = '';
    document.getElementById('stuImportProgress').style.display = 'none';
}

function closeStuImportModal() {
    document.getElementById('stuImportModal').style.display = 'none';
}

function doStuImport() {
    const file = document.getElementById('stuImportFile').files[0];
    if (!file) { alert('请选择文件'); return; }
    const formData = new FormData();
    formData.append('file', file);

    document.getElementById('stuImportProgress').style.display = 'block';
    document.getElementById('stuImportStatus').textContent = '正在导入...';

    fetch('/api/students/import', {
        method: 'POST',
        headers: {'Authorization': `Bearer ${authToken}`},
        body: formData
    }).then(res => res.json().catch(() => ({error: '请求失败'}))).then(result => {
        if (result.error) {
            document.getElementById('stuImportStatus').textContent = '导入失败：' + result.error;
        } else {
            const msg = `导入完成！成功：${result.imported}条，更新：${result.updated}条，跳过：${result.skipped}条`;
            document.getElementById('stuImportStatus').textContent = msg;
        }
    }).catch(err => {
        document.getElementById('stuImportStatus').textContent = '导入失败：' + err.message;
    });
}

function doExportStudents() {
    fetch('/api/students/export', {
        headers: {'Authorization': `Bearer ${authToken}`}
    }).then(res => {
        if (!res.ok) return res.json().then(d => { throw new Error(d.error || '导出失败'); });
        return res.blob();
    }).then(blob => {
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `学生就读信息_${new Date().toISOString().slice(0,10).replace(/-/g,'')}.xlsx`;
        a.click();
        URL.revokeObjectURL(url);
    }).catch(err => alert('导出失败：' + err.message));
}

function doDownloadStudentTemplate() {
    fetch('/api/template/student', {
        headers: {'Authorization': `Bearer ${authToken}`}
    }).then(res => {
        if (res.status === 401) {
            showLogin();
            throw new Error('登录已过期，请重新登录');
        }
        if (!res.ok) {
            if (res.headers.get('content-type')?.includes('json')) {
                return res.json().then(d => { throw new Error(d.error || '下载失败'); });
            }
            throw new Error('下载失败');
        }
        return res.blob();
    }).then(blob => {
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = '学生就读信息模板.xlsx';
        a.click();
        URL.revokeObjectURL(url);
    }).catch(err => alert(err.message));
}

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

function closeEduEdit() {
    document.getElementById('eduEditModal').style.display = 'none';
}

document.getElementById('eduEditForm').onsubmit = function(e) {
    e.preventDefault();
    const personId = document.getElementById('eduPersonId').value;
    const data = {
        school_name: document.getElementById('eduSchool').value.trim(),
        grade: document.getElementById('eduGrade').value,
        class_name: document.getElementById('eduClass').value.trim(),
        guardian: document.getElementById('eduGuardian').value.trim(),
        guardian_phone: document.getElementById('eduGuardianPhone').value.trim(),
        is_left_behind: document.getElementById('eduLeftBehind').value,
        student_status: document.getElementById('eduStatus').value,
        enrollment_date: document.getElementById('eduEnrollDate').value
    };

    fetch(`/api/person/${personId}/education`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${authToken}`
        },
        body: JSON.stringify(data)
    })
    .then(res => res.json())
    .then(result => {
        if (result.success) {
            closeEduEdit();
            searchStudents();
        } else {
            alert(result.error || '保存失败');
        }
    })
    .catch(err => alert('保存失败：' + err.message));
};
