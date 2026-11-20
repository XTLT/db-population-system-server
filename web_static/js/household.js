

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
