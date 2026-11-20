function editUser(id, username, realName, role, isActive) {
    document.getElementById('editUserId').value = id;
    document.getElementById('editUsername').value = username;
    document.getElementById('editRealName').value = realName;
    document.getElementById('editRole').value = role;
    document.getElementById('editIsActive').value = isActive;
    document.getElementById('editPassword').value = '';
    document.getElementById('editUserModal').style.display = 'flex';
}
