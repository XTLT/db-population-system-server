function showMain() {
    document.getElementById('loginPage').style.display = 'none';
    document.getElementById('mainPage').style.display = 'block';
    document.getElementById('currentUser').textContent = currentUser?.real_name || currentUser?.username || '';
    const roleMap = {admin: '管理员', user: '普通用户'};
    document.getElementById('currentRole').textContent = roleMap[userRole] || userRole;
    applyRolePermissions();
}
