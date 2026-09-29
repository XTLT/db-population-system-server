function displayNames(persons) {
    const nameList = document.getElementById('nameList');
    nameList.innerHTML = '';
    document.getElementById('familyInfo').style.display = 'none';
    document.getElementById('personDetail').style.display = 'none';

    if (persons.length === 0) {
        nameList.innerHTML = '<p style="color: red; font-weight: bold;">未找到该人员</p>';
        return;
    }

    persons.forEach(p => {
        const btn = document.createElement('button');
        btn.className = 'name-btn' + (p.is_migrated === '是' ? ' migrated' : '');
        btn.textContent = p.name;
        btn.onclick = () => showFamily(p.hu_hao, p.name);
        nameList.appendChild(btn);
    });
}

function showFamily(huHao, name) {
    currentHuHao = huHao;
    document.getElementById('familyInfo').style.display = 'block';
    document.getElementById('personDetail').style.display = 'none';

    apiRequest('GET', `/api/family/${huHao}`)
        .then(data => {
            const members = data.members || data;
            const sameNameCount = members.filter(m => m.name === name).length;
            document.getElementById('familyTitle').textContent =
                `您选择查看：${name}（共找到 ${sameNameCount} 个同名人员）`;
            displayFamily(members);
        });
}

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

function showPerson(personId) {
    currentPersonId = personId;
    document.getElementById('personDetail').style.display = 'block';

    apiRequest('GET', `/api/person/${personId}`)
        .then(data => {
            const p = data.person || data;
            currentPersonUpdatedAt = p.updated_at || '';
            let html = `
                <div class="detail-item"><label>姓名</label><span>${p.name}</span></div>
                <div class="detail-item"><label>身份证号</label><span>${p.id_card}</span></div>
                <div class="detail-item"><label>户号</label><span>${p.hu_hao}</span></div>
                <div class="detail-item"><label>与户主关系</label><span>${p.relation}</span></div>
                <div class="detail-item"><label>年龄</label><span>${p.age}</span></div>
                <div class="detail-item"><label>电话</label><span>${p.phone === '无' ? '' : p.phone}</span></div>
                <div class="detail-item"><label>状态</label><span>${p.is_dead === '是' ? '已故' : (p.is_migrated === '是' ? '已迁出' : '正常')}</span></div>
                <div class="detail-item"><label>地址</label><span>${p.address || ''}</span></div>
                <div class="detail-item"><label>社保卡号1</label><span>${p.social_card1 === '无' ? '' : p.social_card1}</span></div>
                <div class="detail-item"><label>社保卡号2</label><span>${(p.social_card2 && p.social_card2 !== '无') ? p.social_card2 + (p.social_card2_source ? `（${p.social_card2_source}）` : '') : ''}</span></div>
                <div class="detail-item"><label>社保卡号3</label><span>${(p.social_card3 && p.social_card3 !== '无') ? p.social_card3 + (p.social_card3_source ? `（${p.social_card3_source}）` : '') : ''}</span></div>
                <div class="detail-item"><label>脱贫户</label><span>${p.poor_type === '无' ? '' : p.poor_type}</span></div>
                <div class="detail-item"><label>备注</label><span>${p.remark === '无' ? '' : p.remark}</span></div>
                <div class="detail-item"><label>残疾</label><span>${p.disability === '无' ? '' : p.disability}</span></div>
                ${p.disability === '是' ? `<div class="detail-item"><label>残疾类型</label><span>${p.disability_type === '无' ? '' : (p.disability_type || '')}</span></div><div class="detail-item"><label>残疾等级</label><span>${p.dis_level === '无' ? '' : (p.dis_level || '')}</span></div>` : ''}
                <div class="detail-item"><label>低保</label><span>${p.dibao === '无' ? '' : p.dibao}</span></div>
                <div class="detail-item"><label>计生家庭</label><span>${p.jisheng === '无' ? '' : p.jisheng}</span></div>
                <div class="detail-item"><label>特困供养</label><span>${p.tekun === '无' ? '' : (p.tekun || '')}</span></div>
                ${p.tekun === '是' ? `<div class="detail-item"><label>供养类型</label><span>${p.tekun_type === '无' ? '' : (p.tekun_type || '')}</span></div>` : ''}
                <div class="detail-item"><label>土地面积</label><span>${p.land_area || ''}</span></div>
                ${p.land_area_change_reason ? `<div class="detail-item"><label>土地变更原因</label><span>${p.land_area_change_reason}</span></div><div class="detail-item"><label>土地变更时间</label><span>${p.land_area_change_time}</span></div>` : ''}
                <div class="detail-item"><label>地方公益林</label><span>${p.local_welfare_forest_area || ''}</span></div>
                ${p.local_welfare_forest_change_reason ? `<div class="detail-item"><label>地方公益林变更原因</label><span>${p.local_welfare_forest_change_reason}</span></div><div class="detail-item"><label>地方公益林变更时间</label><span>${p.local_welfare_forest_change_time}</span></div>` : ''}
                <div class="detail-item"><label>国家公益林</label><span>${p.national_welfare_forest_area || ''}</span></div>
                ${p.national_welfare_forest_change_reason ? `<div class="detail-item"><label>国家公益林变更原因</label><span>${p.national_welfare_forest_change_reason}</span></div><div class="detail-item"><label>国家公益林变更时间</label><span>${p.national_welfare_forest_change_time}</span></div>` : ''}
                <div class="detail-item"><label>非国有天然商品林</label><span>${p.commercial_forest_area || ''}</span></div>
                ${p.commercial_forest_change_reason ? `<div class="detail-item"><label>非国有天然商品林变更原因</label><span>${p.commercial_forest_change_reason}</span></div><div class="detail-item"><label>非国有天然商品林变更时间</label><span>${p.commercial_forest_change_time}</span></div>` : ''}
            `;

            if (p.education) {
                html += `
                    <div class="detail-item" style="grid-column: span 2;"><label>就读信息</label></div>
                    <div class="detail-item"><label>学校</label><span>${p.education.school_name}</span></div>
                    <div class="detail-item"><label>年级</label><span>${p.education.grade}</span></div>
                    <div class="detail-item"><label>班级</label><span>${p.education.class_name}</span></div>
                    <div class="detail-item"><label>监护人</label><span>${p.education.guardian}</span></div>
                    <div class="detail-item"><label>监护人电话</label><span>${p.education.guardian_phone}</span></div>
                    <div class="detail-item"><label>留守儿童</label><span>${p.education.is_left_behind}</span></div>
                    <div class="detail-item"><label>学生状态</label><span>${p.education.student_status}</span></div>
                `;
            }

            document.getElementById('detailContent').innerHTML = html;
        });
}

function editPerson() {
    if (!currentPersonId) return;

    apiRequest('GET', `/api/person/${currentPersonId}`)
        .then(data => {
            const p = data.person || data;
            currentPersonUpdatedAt = p.updated_at || '';
            document.getElementById('editId').value = p.id;
            document.getElementById('editIdCard').value = p.id_card;
            document.getElementById('editName').value = p.name;
            document.getElementById('editHuHao').value = p.hu_hao || '';
            document.getElementById('editRelation').value = p.relation || '';
            document.getElementById('editIsDead').value = p.is_dead || '';
            document.getElementById('editPhone').value = (p.phone && p.phone !== '无') ? p.phone : '';
            document.getElementById('editAddress').value = (p.address && p.address !== '无') ? p.address : '';
            document.getElementById('editLandArea').value = p.land_area || '';
            currentPersonLandArea = p.land_area || '';
            document.getElementById('editLocalWelfareForest').value = p.local_welfare_forest_area || '';
            currentPersonLocalWelfareForest = p.local_welfare_forest_area || '';
            document.getElementById('editNationalWelfareForest').value = p.national_welfare_forest_area || '';
            currentPersonNationalWelfareForest = p.national_welfare_forest_area || '';
            document.getElementById('editCommercialForest').value = p.commercial_forest_area || '';
            currentPersonCommercialForest = p.commercial_forest_area || '';
            document.getElementById('editSocial1').value = (p.social_card1 && p.social_card1 !== '无') ? p.social_card1 : '';
            document.getElementById('editSocial2').value = (p.social_card2 && p.social_card2 !== '无') ? p.social_card2 + (p.social_card2_source ? `（${p.social_card2_source}）` : '') : '';
            document.getElementById('editSocial3').value = (p.social_card3 && p.social_card3 !== '无') ? p.social_card3 + (p.social_card3_source ? `（${p.social_card3_source}）` : '') : '';
            // 社保卡号2/3 仅由补贴导入自动回填，编辑框只读展示卡号+来源
            document.getElementById('editSocial2').readOnly = true;
            document.getElementById('editSocial3').readOnly = true;
            document.getElementById('editRemark').value = (p.remark && p.remark !== '无') ? p.remark : '';

            // 社会保障
            document.getElementById('editPoorType').value = (p.poor_type && p.poor_type !== '无') ? p.poor_type : '';

            const disValue = (p.disability && p.disability !== '无') ? p.disability : '';
            document.getElementById('editDisability').value = disValue;
            toggleDisabilityDetail();
            if (disValue === '是') {
                document.getElementById('editDisabilityType').value = (p.disability_type && p.disability_type !== '无') ? p.disability_type : '';
                document.getElementById('editDisLevel').value = (p.dis_level && p.dis_level !== '无') ? p.dis_level : '';
            }

            document.getElementById('editDibao').value = (p.dibao && p.dibao !== '无') ? p.dibao : '';
            document.getElementById('editJisheng').value = (p.jisheng && p.jisheng !== '无') ? p.jisheng : '';

            const tekunValue = (p.tekun && p.tekun !== '无') ? p.tekun : '';
            document.getElementById('editTekun').value = tekunValue;
            toggleTekunDetail();
            if (tekunValue === '是') {
                document.getElementById('editTekunType').value = (p.tekun_type && p.tekun_type !== '无') ? p.tekun_type : '';
            }

            // 就读信息
            document.getElementById('editEduSchool').value = p.education?.school_name || '';
            document.getElementById('editEduClass').value = p.education?.class_name || '';
            document.getElementById('editEduGuardian').value = p.education?.guardian || '';
            document.getElementById('editEduGuardianPhone').value = p.education?.guardian_phone || '';
            document.getElementById('editEduLeftBehind').value = p.education?.is_left_behind || '';
            document.getElementById('editEduStatus').value = p.education?.student_status || '';
            document.getElementById('editEduEnrollDate').value = p.education?.enrollment_date || '';
            document.getElementById('editEduGradDate').value = p.education?.graduation_date || '';
            document.getElementById('editEduGrade').value = p.education?.grade || '';

            // 添加年级变化监听，自动计算入学和毕业日期
            const gradeSelect = document.getElementById('editEduGrade');
            gradeSelect.onchange = function() {
                calculateEnrollmentAndGraduation();
            };

            document.getElementById('editModal').style.display = 'flex';
        });
}

function toggleDisabilityDetail() {
    const val = document.getElementById('editDisability').value;
    document.getElementById('disabilityDetail').style.display = val === '是' ? 'block' : 'none';
    if (val !== '是') {
        document.getElementById('editDisabilityType').value = '';
        document.getElementById('editDisLevel').value = '';
    }
}

function toggleTekunDetail() {
    const val = document.getElementById('editTekun').value;
    document.getElementById('tekunDetail').style.display = val === '是' ? 'block' : 'none';
    if (val !== '是') {
        document.getElementById('editTekunType').value = '';
    }
}

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

function closeEdit() {
    document.getElementById('editModal').style.display = 'none';
}

document.getElementById('editForm').onsubmit = function(e) {
    e.preventDefault();
    const id = document.getElementById('editId').value;
    const newLandArea = document.getElementById('editLandArea').value;
    const oldLandArea = currentPersonLandArea || '';

    if (newLandArea !== oldLandArea && oldLandArea) {
        const reason = prompt(`土地面积从「${oldLandArea}」变更为「${newLandArea || '空'}」\n\n请输入变更原因：`);
        if (!reason || !reason.trim()) {
            alert('土地面积变更时必须填写变更原因！');
            return;
        }
        window._landAreaChangeReason = reason.trim();
    } else {
        window._landAreaChangeReason = '';
    }

    const newLocalWelfareForest = document.getElementById('editLocalWelfareForest').value;
    const oldLocalWelfareForest = currentPersonLocalWelfareForest || '';

    if (newLocalWelfareForest !== oldLocalWelfareForest && oldLocalWelfareForest) {
        const reason = prompt(`地方公益林从「${oldLocalWelfareForest}」变更为「${newLocalWelfareForest || '空'}」\n\n请输入变更原因：`);
        if (!reason || !reason.trim()) {
            alert('地方公益林变更时必须填写变更原因！');
            return;
        }
        window._localWelfareForestChangeReason = reason.trim();
    } else {
        window._localWelfareForestChangeReason = '';
    }

    const newNationalWelfareForest = document.getElementById('editNationalWelfareForest').value;
    const oldNationalWelfareForest = currentPersonNationalWelfareForest || '';

    if (newNationalWelfareForest !== oldNationalWelfareForest && oldNationalWelfareForest) {
        const reason = prompt(`国家公益林从「${oldNationalWelfareForest}」变更为「${newNationalWelfareForest || '空'}」\n\n请输入变更原因：`);
        if (!reason || !reason.trim()) {
            alert('国家公益林变更时必须填写变更原因！');
            return;
        }
        window._nationalWelfareForestChangeReason = reason.trim();
    } else {
        window._nationalWelfareForestChangeReason = '';
    }

    const newCommercialForest = document.getElementById('editCommercialForest').value;
    const oldCommercialForest = currentPersonCommercialForest || '';

    if (newCommercialForest !== oldCommercialForest && oldCommercialForest) {
        const reason = prompt(`非国有天然商品林从「${oldCommercialForest}」变更为「${newCommercialForest || '空'}」\n\n请输入变更原因：`);
        if (!reason || !reason.trim()) {
            alert('非国有天然商品林变更时必须填写变更原因！');
            return;
        }
        window._commercialForestChangeReason = reason.trim();
    } else {
        window._commercialForestChangeReason = '';
    }

    const disabilityVal = document.getElementById('editDisability').value;
    const tekunVal = document.getElementById('editTekun').value;
    const data = {
        name: document.getElementById('editName').value,
        relation: document.getElementById('editRelation').value,
        phone: document.getElementById('editPhone').value,
        address: document.getElementById('editAddress').value || '',
        is_dead: document.getElementById('editIsDead').value || '否',
        remark: document.getElementById('editRemark').value,
        poor_type: document.getElementById('editPoorType').value,
        disability: disabilityVal,
        disability_type: disabilityVal === '是' ? document.getElementById('editDisabilityType').value : '',
        dis_level: disabilityVal === '是' ? document.getElementById('editDisLevel').value : '',
        dibao: document.getElementById('editDibao').value,
        jisheng: document.getElementById('editJisheng').value,
        tekun: tekunVal,
        tekun_type: tekunVal === '是' ? document.getElementById('editTekunType').value : '',
        social_card1: document.getElementById('editSocial1').value,
        land_area: newLandArea,
        land_area_change_reason: window._landAreaChangeReason,
        local_welfare_forest_area: newLocalWelfareForest,
        local_welfare_forest_change_reason: window._localWelfareForestChangeReason,
        national_welfare_forest_area: newNationalWelfareForest,
        national_welfare_forest_change_reason: window._nationalWelfareForestChangeReason,
        commercial_forest_area: newCommercialForest,
        commercial_forest_change_reason: window._commercialForestChangeReason,
        updated_at: currentPersonUpdatedAt
    };

    fetch(`/api/person/${id}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${authToken}`
        },
        body: JSON.stringify(data)
    })
    .then(res => {
        if (res.status === 409) {
            return res.json().then(result => {
                alert(result.message || '数据冲突，请刷新后重试');
                closeEdit();
                showFamily(currentHuHao, data.name);
            });
        }
        return res.json().catch(() => ({error: '请求失败'}));
    })
    .then(result => {
        if (result && result.success) {
            currentPersonUpdatedAt = result.updated_at || '';

            // 检查是否有就读信息需要保存
            const schoolName = document.getElementById('editEduSchool').value.trim();
            const grade = document.getElementById('editEduGrade').value;
            const hasEducation = schoolName || grade;

            const eduPromise = hasEducation ? fetch(`/api/person/${id}/education`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${authToken}`
                },
                body: JSON.stringify({
                    school_name: schoolName,
                    grade: grade,
                    class_name: document.getElementById('editEduClass').value.trim(),
                    guardian: document.getElementById('editEduGuardian').value.trim(),
                    guardian_phone: document.getElementById('editEduGuardianPhone').value.trim(),
                    is_left_behind: document.getElementById('editEduLeftBehind').value || '否',
                    student_status: document.getElementById('editEduStatus').value || '在读',
                    enrollment_date: document.getElementById('editEduEnrollDate').value,
                    graduation_date: document.getElementById('editEduGradDate').value
                })
            }).then(r => r.json()) : Promise.resolve();

            return eduPromise.then(() => {
                closeEdit();
                showFamily(currentHuHao, data.name);
                showPerson(id);
            });
        }
    });
};

function migratePerson() {
    if (!currentPersonId) return;
    document.getElementById('migrateId').value = currentPersonId;
    document.getElementById('migrateDate').value = new Date().toISOString().split('T')[0];
    document.getElementById('migrateModal').style.display = 'flex';
}

function closeMigrate() {
    document.getElementById('migrateModal').style.display = 'none';
}

document.getElementById('migrateForm').onsubmit = function(e) {
    e.preventDefault();
    const id = document.getElementById('migrateId').value;
    const data = {
        date: document.getElementById('migrateDate').value,
        place: document.getElementById('migratePlace').value,
        reason: document.getElementById('migrateReason').value
    };

    apiRequest('POST', `/api/person/${id}/migrate`, data)
        .then(result => {
            if (result.success) {
                closeMigrate();
                alert('户籍迁出操作成功！');
                showFamily(currentHuHao, '');
            }
        });
};

function deletePerson() {
    if (!currentPersonId) return;
    if (!confirm('确定要删除该人员吗？删除后可在找回功能中恢复。')) return;
    if (!confirm('请再次确认：是否删除该人员？')) return;

    apiRequest('DELETE', `/api/person/${currentPersonId}`)
        .then(result => {
            if (result.success) {
                alert('人员已删除！');
                document.getElementById('personDetail').style.display = 'none';
                showFamily(currentHuHao, '');
            }
        });
}

function closeDetail() {
    document.getElementById('personDetail').style.display = 'none';
}

document.getElementById('searchInput').addEventListener('keypress', function(e) {
    if (e.key === 'Enter') doSearch();
});

document.getElementById('editDisability').addEventListener('change', toggleDisabilityDetail);
document.getElementById('editTekun').addEventListener('change', toggleTekunDetail);

function doSearch() {
    const name = document.getElementById('searchInput').value.trim();
    if (!name) return;
    apiRequest('GET', `/api/search?name=${encodeURIComponent(name)}`)
        .then(data => displayNames(data.results || data));
}
