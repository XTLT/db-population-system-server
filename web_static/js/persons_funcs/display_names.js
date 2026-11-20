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
