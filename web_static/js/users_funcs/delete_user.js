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
