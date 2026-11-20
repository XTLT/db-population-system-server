








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



document.getElementById('searchInput').addEventListener('keypress', function(e) {
    if (e.key === 'Enter') doSearch();
});

document.getElementById('editDisability').addEventListener('change', toggleDisabilityDetail);
document.getElementById('editTekun').addEventListener('change', toggleTekunDetail);
