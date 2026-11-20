function showSplitHouseholdModal() {
    if (!currentHuHao) { alert('请先选择一个家庭'); return; }
    apiRequest('GET', `/api/family/${currentHuHao}`).then(data => {
        const members = data.members || data;
        splitPersons = members;
        const list = document.getElementById('splitPersonList');
        list.innerHTML = members.map(m =>
            `<label style="display:block;padding:5px;"><input type="checkbox" value="${m.id}" class="split-check"> ${m.name} (${m.id_card})</label>`
        ).join('');
        document.getElementById('splitHouseholdModal').style.display = 'flex';
    });
}
