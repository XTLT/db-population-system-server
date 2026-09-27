function showAddHouseholdModal() {
    fetch('/api/household/new_number', {
        headers: {'Authorization': `Bearer ${authToken}`}
    }).then(r => r.json()).then(data => {
        document.getElementById('newHhHuhao').value = data.hu_hao || '';
    });
    document.getElementById('newHhName').value = '';
    document.getElementById('newHhIdCard').value = '';
    document.getElementById('newHhAddress').value = '';
    document.getElementById('newHhPhone').value = '';
    document.getElementById('newHhLandArea').value = '';
    document.getElementById('newHhLocalWelfareForest').value = '';
    document.getElementById('newHhNationalWelfareForest').value = '';
    document.getElementById('newHhCommercialForest').value = '';
    document.getElementById('addHouseholdModal').style.display = 'flex';
}

function closeAddHouseholdModal() {
    document.getElementById('addHouseholdModal').style.display = 'none';
}

document.getElementById('addHouseholdForm').onsubmit = function(e) {
    e.preventDefault();
    const data = {
        hu_hao: document.getElementById('newHhHuhao').value.trim(),
        name: document.getElementById('newHhName').value.trim(),
        id_card: document.getElementById('newHhIdCard').value.trim(),
        address: document.getElementById('newHhAddress').value.trim(),
        phone: document.getElementById('newHhPhone').value.trim(),
        land_area: document.getElementById('newHhLandArea').value.trim(),
        local_welfare_forest_area: document.getElementById('newHhLocalWelfareForest').value.trim(),
        national_welfare_forest_area: document.getElementById('newHhNationalWelfareForest').value.trim(),
        commercial_forest_area: document.getElementById('newHhCommercialForest').value.trim()
    };
    fetch('/api/household/add', {
        method: 'POST',
        headers: {'Content-Type': 'application/json', 'Authorization': `Bearer ${authToken}`},
        body: JSON.stringify(data)
    }).then(r => r.json()).then(result => {
        if (result.success) {
            closeAddHouseholdModal();
            alert('新户创建成功！');
        } else {
            alert(result.error || '创建失败');
        }
    }).catch(err => alert('创建失败：' + err.message));
};

let splitPersons = [];
function showSplitHouseholdModal() {
    if (!currentHuHao) { alert('请先选择一个家庭'); return; }
    apiRequest('GET', `/api/family/${currentHuHao}`).then(members => {
        splitPersons = members;
        const list = document.getElementById('splitPersonList');
        list.innerHTML = members.map(m =>
            `<label style="display:block;padding:5px;"><input type="checkbox" value="${m.id}" class="split-check"> ${m.name} (${m.id_card})</label>`
        ).join('');
        document.getElementById('splitHouseholdModal').style.display = 'flex';
    });
}

function closeSplitHouseholdModal() {
    document.getElementById('splitHouseholdModal').style.display = 'none';
}

function doSplitHousehold() {
    const ids = [...document.querySelectorAll('.split-check:checked')].map(c => c.value);
    if (ids.length === 0) { alert('请选择要分户的人员'); return; }
    if (!confirm(`确定将 ${ids.length} 人分出为新户？`)) return;
    fetch('/api/household/split', {
        method: 'POST',
        headers: {'Content-Type': 'application/json', 'Authorization': `Bearer ${authToken}`},
        body: JSON.stringify({person_ids: ids})
    }).then(r => r.json()).then(result => {
        if (result.success) {
            closeSplitHouseholdModal();
            alert(`分户成功！新户号：${result.new_hu_hao}`);
            doSearch();
        } else {
            alert(result.error || '分户失败');
        }
    }).catch(err => alert('分户失败：' + err.message));
}

function showMergeHouseholdModal() {
    document.getElementById('mergeTargetHuHao').value = currentHuHao || '';
    apiRequest('GET', `/api/family/${currentHuHao || ''}`).then(members => {
        const list = document.getElementById('mergePersonList');
        list.innerHTML = members.map(m =>
            `<label style="display:block;padding:5px;"><input type="checkbox" value="${m.id}" class="merge-check"> ${m.name} (${m.id_card}) - 户号:${currentHuHao}</label>`
        ).join('');
        document.getElementById('mergeHouseholdModal').style.display = 'flex';
    }).catch(() => {
        document.getElementById('mergePersonList').innerHTML = '<p style="color:red;">请先搜索并选择一个家庭</p>';
        document.getElementById('mergeHouseholdModal').style.display = 'flex';
    });
}

function closeMergeHouseholdModal() {
    document.getElementById('mergeHouseholdModal').style.display = 'none';
}

function doMergeHousehold() {
    const target = document.getElementById('mergeTargetHuHao').value.trim();
    const ids = [...document.querySelectorAll('.merge-check:checked')].map(c => c.value);
    if (!target) { alert('请输入目标户号'); return; }
    if (ids.length === 0) { alert('请选择要合并的人员'); return; }
    if (!confirm(`确定将 ${ids.length} 人合并到户号 ${target}？`)) return;
    fetch('/api/household/merge', {
        method: 'POST',
        headers: {'Content-Type': 'application/json', 'Authorization': `Bearer ${authToken}`},
        body: JSON.stringify({target_hu_hao: target, person_ids: ids})
    }).then(r => r.json()).then(result => {
        if (result.success) {
            closeMergeHouseholdModal();
            alert('合户成功！');
            doSearch();
        } else {
            alert(result.error || '合户失败');
        }
    }).catch(err => alert('合户失败：' + err.message));
}

function showAddPersonModal() {
    if (!currentHuHao) { alert('请先选择一个家庭'); return; }
    document.getElementById('addPersonHuHao').value = currentHuHao;
    document.getElementById('addPersonName').value = '';
    document.getElementById('addPersonIdCard').value = '';
    document.getElementById('addPersonRelation').value = '';
    document.getElementById('addPersonPhone').value = '';
    document.getElementById('addPersonLandArea').value = '';
    document.getElementById('addPersonLocalWelfareForest').value = '';
    document.getElementById('addPersonNationalWelfareForest').value = '';
    document.getElementById('addPersonCommercialForest').value = '';
    apiRequest('GET', `/api/family/${currentHuHao}`).then(members => {
        if (members.length > 0) {
            document.getElementById('addPersonAddress').value = members[0].address || '';
        }
    });
    document.getElementById('addPersonModal').style.display = 'flex';
}

function closeAddPersonModal() {
    document.getElementById('addPersonModal').style.display = 'none';
}

document.getElementById('addPersonForm').onsubmit = function(e) {
    e.preventDefault();
    const data = {
        hu_hao: document.getElementById('addPersonHuHao').value,
        name: document.getElementById('addPersonName').value.trim(),
        id_card: document.getElementById('addPersonIdCard').value.trim(),
        relation: document.getElementById('addPersonRelation').value.trim(),
        address: document.getElementById('addPersonAddress').value.trim(),
        phone: document.getElementById('addPersonPhone').value.trim(),
        land_area: document.getElementById('addPersonLandArea').value.trim(),
        local_welfare_forest_area: document.getElementById('addPersonLocalWelfareForest').value.trim(),
        national_welfare_forest_area: document.getElementById('addPersonNationalWelfareForest').value.trim(),
        commercial_forest_area: document.getElementById('addPersonCommercialForest').value.trim()
    };
    if (!data.name || !data.id_card) {
        alert('姓名和身份证号不能为空！');
        return;
    }
    fetch('/api/person', {
        method: 'POST',
        headers: {'Content-Type': 'application/json', 'Authorization': `Bearer ${authToken}`},
        body: JSON.stringify(data)
    }).then(r => r.json()).then(result => {
        if (result.success) {
            closeAddPersonModal();
            showFamily(currentHuHao, '');
        } else {
            alert(result.error || '添加失败');
        }
    }).catch(err => alert('添加失败：' + err.message));
};
