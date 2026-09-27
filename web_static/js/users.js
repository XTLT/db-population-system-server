function showUserModal() {
    document.getElementById('userModal').style.display = 'flex';
    loadUsers();
}

function closeUserModal() {
    document.getElementById('userModal').style.display = 'none';
}

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

function showAddUser() {
    document.getElementById('addUserModal').style.display = 'flex';
    document.getElementById('newUsername').value = '';
    document.getElementById('newPassword').value = '';
    document.getElementById('newRealName').value = '';
    document.getElementById('newRole').value = 'user';
}

function closeAddUser() {
    document.getElementById('addUserModal').style.display = 'none';
}

document.getElementById('addUserForm').onsubmit = function(e) {
    e.preventDefault();
    const data = {
        username: document.getElementById('newUsername').value.trim(),
        password: document.getElementById('newPassword').value,
        real_name: document.getElementById('newRealName').value.trim(),
        role: document.getElementById('newRole').value
    };
    if (!data.username || !data.password) {
        alert('用户名和密码不能为空');
        return;
    }
    apiRequest('POST', '/api/users', data).then(result => {
        if (result.success) {
            closeAddUser();
            loadUsers();
        } else {
            alert(result.error || '添加失败');
        }
    });
};

function editUser(id, username, realName, role, isActive) {
    document.getElementById('editUserId').value = id;
    document.getElementById('editUsername').value = username;
    document.getElementById('editRealName').value = realName;
    document.getElementById('editRole').value = role;
    document.getElementById('editIsActive').value = isActive;
    document.getElementById('editPassword').value = '';
    document.getElementById('editUserModal').style.display = 'flex';
}

function closeEditUser() {
    document.getElementById('editUserModal').style.display = 'none';
}

document.getElementById('editUserForm').onsubmit = function(e) {
    e.preventDefault();
    const id = document.getElementById('editUserId').value;
    const data = {
        real_name: document.getElementById('editRealName').value.trim(),
        role: document.getElementById('editRole').value,
        is_active: document.getElementById('editIsActive').value
    };
    const password = document.getElementById('editPassword').value;
    if (password) data.password = password;

    apiRequest('PUT', `/api/users/${id}`, data).then(result => {
        if (result.success) {
            closeEditUser();
            loadUsers();
        } else {
            alert(result.error || '修改失败');
        }
    });
};

function deleteUser(id, username) {
    if (!confirm(`确定要删除用户 ${username} 吗？`)) return;
    apiRequest('DELETE', `/api/users/${id}`).then(result => {
        if (result.success) {
            loadUsers();
        } else {
            alert(result.error || '删除失败');
        }
    });
}
