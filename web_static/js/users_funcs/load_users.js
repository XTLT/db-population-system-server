function loadUsers() {
    apiRequest('GET', '/api/users').then(response => {
        const users = response.users || [];
        const tbody = document.getElementById('userBody');
        tbody.innerHTML = '';
        const roleMap = {admin: '管理员', user: '普通用户'};
        users.forEach(u => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${u.username}</td>
                <td>${u.real_name || ''}</td>
                <td>${roleMap[u.role] || u.role}</td>
                <td>${u.is_active === '是' ? '启用' : '禁用'}</td>
                <td>${u.last_login || ''}</td>
                <td>
                    <button onclick="editUser('${u.id}','${u.username}','${u.real_name || ''}','${u.role}','${u.is_active}')" class="btn-edit" style="padding:4px 8px;font-size:12px;">编辑</button>
                    <button onclick="deleteUser('${u.id}','${u.username}')" class="btn-delete" style="padding:4px 8px;font-size:12px;">删除</button>
                </td>
            `;
            tbody.appendChild(tr);
        });
    });
}
