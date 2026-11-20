




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
