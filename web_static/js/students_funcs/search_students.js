function searchStudents() {
    const params = new URLSearchParams();
    const school = document.getElementById('stuSchool').value;
    const grade = document.getElementById('stuGrade').value;
    if (school) params.set('school', school);
    if (grade) params.set('grade', grade);

    apiRequest('GET', `/api/students/search?${params}`).then(data => {
        const students = data.results || data;
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
