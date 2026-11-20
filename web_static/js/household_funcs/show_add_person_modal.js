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
    apiRequest('GET', `/api/family/${currentHuHao}`).then(data => {
        const members = data.members || data;
        if (members.length > 0) {
            document.getElementById('addPersonAddress').value = members[0].address || '';
        }
    });
    document.getElementById('addPersonModal').style.display = 'flex';
}
