function loadDeleted() {
    const tbody = document.getElementById('deletedBody');
    tbody.innerHTML = '<tr><td colspan="5" style="color:#999;">加载中...</td></tr>';
    apiRequest('GET', '/api/deleted').then(persons => {
        tbody.innerHTML = '';
        if (!Array.isArray(persons)) {
            tbody.innerHTML = '<tr><td colspan="5" style="color:#e74c3c;">无法获取已删除人员列表</td></tr>';
            return;
        }
        if (persons.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" style="color:#999;">没有已删除的人员</td></tr>';
            return;
        }
        persons.forEach(p => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${p.name}</td>
                <td>${p.id_card}</td>
                <td>${p.hu_hao}</td>
                <td>${p.deleted_at}</td>
                <td><button onclick="recoverPerson('${p.id}','${p.name}')" class="btn-edit" style="padding:4px 8px;font-size:12px;">找回</button></td>
            `;
            tbody.appendChild(tr);
        });
    }).catch(err => {
        tbody.innerHTML = '<tr><td colspan="5" style="color:#e74c3c;">无法获取已删除人员列表' + (err && err.message ? '：' + err.message : '') + '</td></tr>';
    });
}
