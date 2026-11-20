function showAddUser() {
    document.getElementById('addUserModal').style.display = 'flex';
    document.getElementById('newUsername').value = '';
    document.getElementById('newPassword').value = '';
    document.getElementById('newRealName').value = '';
    document.getElementById('newRole').value = 'user';
}
