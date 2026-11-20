function displayFamily(members) {
    const tbody = document.getElementById('familyBody');
    tbody.innerHTML = '';
    const canEdit = userRole === 'admin' || userRole === 'user';

    members.forEach(m => {
        const tr = document.createElement('tr');
        if (m.is_dead === '是') tr.className = 'dead';
        if (m.is_migrated === '是') tr.className = 'migrated';

        const editBtn = canEdit
            ? `<button onclick="showPerson('${m.id}')" class="btn-edit" style="padding:5px 10px;font-size:12px;">详情</button>`
            : `<button onclick="showPerson('${m.id}')" class="btn-cancel" style="padding:5px 10px;font-size:12px;">查看</button>`;

        tr.innerHTML = `
            <td>${m.name}</td>
            <td>${m.id_card}</td>
            <td>${m.relation}</td>
            <td>${m.age}</td>
            <td>${m.phone === '无' ? '' : m.phone}</td>
            <td>${m.land_area || ''}</td>
            <td>${m.local_welfare_forest_area || ''}</td>
            <td>${m.national_welfare_forest_area || ''}</td>
            <td>${m.commercial_forest_area || ''}</td>
            <td>${m.is_dead === '是' ? '已故' : (m.is_migrated === '是' ? '已迁出' : '正常')}</td>
            <td class="student-mark">${m.student_mark}</td>
            <td>${editBtn}</td>
        `;
        tbody.appendChild(tr);
    });
}
