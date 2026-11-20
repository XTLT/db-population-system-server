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
