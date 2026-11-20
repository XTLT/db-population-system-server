function showMergeHouseholdModal() {
    document.getElementById('mergeTargetHuHao').value = currentHuHao || '';
    apiRequest('GET', `/api/family/${currentHuHao || ''}`).then(data => {
        const members = data.members || data;
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
