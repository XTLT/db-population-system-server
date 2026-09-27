function checkAuth() {
    if (authToken) {
        apiRequest('GET', '/api/stats').then(() => {
            showMain();
        }).catch(() => {
            showLogin();
        });
    } else {
        showLogin();
    }
}

function showLogin() {
    document.getElementById('loginPage').style.display = 'flex';
    document.getElementById('mainPage').style.display = 'none';
}

function showMain() {
    document.getElementById('loginPage').style.display = 'none';
    document.getElementById('mainPage').style.display = 'block';
    document.getElementById('currentUser').textContent = currentUser?.real_name || currentUser?.username || '';
    const roleMap = {admin: '管理员', user: '普通用户'};
    document.getElementById('currentRole').textContent = roleMap[userRole] || userRole;
    applyRolePermissions();
}

function applyRolePermissions() {
    const canEdit = userRole === 'admin' || userRole === 'user';
    const canDelete = userRole === 'admin';
    document.getElementById('btnEdit').style.display = canEdit ? '' : 'none';
    document.getElementById('btnMigrate').style.display = canEdit ? '' : 'none';
    document.getElementById('btnDelete').style.display = canDelete ? '' : 'none';
    document.getElementById('btnUserManage').style.display = canDelete ? '' : 'none';
    document.getElementById('btnImport').style.display = canDelete ? '' : 'none';
    document.getElementById('btnExport').style.display = canDelete ? '' : 'none';
    document.getElementById('btnTemplate').style.display = canEdit ? '' : 'none';
    document.getElementById('btnDeleted').style.display = canDelete ? '' : 'none';
    document.getElementById('btnBackup').style.display = canDelete ? '' : 'none';
    document.getElementById('btnLogs').style.display = canDelete ? '' : 'none';
    document.getElementById('btnStuImport').style.display = canDelete ? '' : 'none';
    document.getElementById('btnStuExport').style.display = canDelete ? '' : 'none';
    document.getElementById('btnAddHousehold').style.display = canEdit ? '' : 'none';
    document.getElementById('btnSplitHousehold').style.display = canEdit ? '' : 'none';
    document.getElementById('btnMergeHousehold').style.display = canEdit ? '' : 'none';
    document.getElementById('btnAddPerson').style.display = canEdit ? '' : 'none';
    document.getElementById('btnLandSubsidy').style.display = canEdit ? '' : 'none';
    document.getElementById('btnSubsidyImport').style.display = canDelete ? '' : 'none';
}

document.getElementById('loginForm').onsubmit = function(e) {
    e.preventDefault();
    const username = document.getElementById('loginUsername').value.trim();
    const password = document.getElementById('loginPassword').value;
    const errorEl = document.getElementById('loginError');

    if (!username || !password) {
        errorEl.textContent = '请输入用户名和密码';
        errorEl.style.display = 'block';
        return;
    }

    fetch('/api/login', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({username, password})
    })
    .then(res => {
        if (!res.ok) {
            return res.json().catch(() => ({error: '登录失败，请检查用户名和密码'}));
        }
        return res.json();
    })
    .then(result => {
        if (result.success) {
            authToken = result.token;
            currentUser = result.user;
            userRole = result.user.role;
            isDefaultUser = result.is_default_user || false;
            localStorage.setItem('token', authToken);
            localStorage.setItem('user', JSON.stringify(result.user));
            localStorage.setItem('isDefaultUser', isDefaultUser);

            if (isDefaultUser) {
                showCreateAdmin();
            } else {
                showMain();
            }
        } else {
            errorEl.textContent = result.error || '登录失败';
            errorEl.style.display = 'block';
        }
    })
    .catch(err => {
        errorEl.textContent = '登录失败：' + err.message;
        errorEl.style.display = 'block';
    });
};

function showCreateAdmin() {
    document.getElementById('loginPage').style.display = 'none';
    document.getElementById('mainPage').style.display = 'none';
    document.getElementById('createAdminPage').style.display = 'flex';
}

function logout() {
    apiRequest('POST', '/api/logout').catch(() => {});
    authToken = '';
    currentUser = null;
    userRole = '';
    isDefaultUser = false;
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    localStorage.removeItem('isDefaultUser');
    showLogin();
}

window.onload = function() {
    fetch('/api/status').then(r => r.json()).then(data => {
        if (data.need_create_admin) {
            document.getElementById('defaultAccountInfo').style.display = 'block';
        } else {
            document.getElementById('defaultAccountInfo').style.display = 'none';
        }
        const saved = localStorage.getItem('user');
        if (saved && authToken) {
            currentUser = JSON.parse(saved);
            userRole = currentUser.role;
            isDefaultUser = localStorage.getItem('isDefaultUser') === 'true';
            if (isDefaultUser) {
                showCreateAdmin();
            } else {
                checkAuth();
            }
        } else {
            checkAuth();
        }
    }).catch(() => {
        const saved = localStorage.getItem('user');
        if (saved && authToken) {
            currentUser = JSON.parse(saved);
            userRole = currentUser.role;
            isDefaultUser = localStorage.getItem('isDefaultUser') === 'true';
            if (isDefaultUser) {
                showCreateAdmin();
            } else {
                checkAuth();
            }
        } else {
            checkAuth();
        }
    });
};

document.getElementById('createAdminForm').onsubmit = function(e) {
    e.preventDefault();
    const username = document.getElementById('adminUsername').value.trim();
    const password = document.getElementById('adminPassword').value;
    const confirm = document.getElementById('adminConfirm').value;
    const realName = document.getElementById('adminRealName').value.trim();
    const errorEl = document.getElementById('createAdminError');

    if (!username || !password) {
        errorEl.textContent = '用户名和密码不能为空';
        errorEl.style.display = 'block';
        return;
    }
    if (password !== confirm) {
        errorEl.textContent = '两次输入的密码不一致';
        errorEl.style.display = 'block';
        return;
    }
    if (password.length < 8) {
        errorEl.textContent = '密码至少8位';
        errorEl.style.display = 'block';
        return;
    }
    if (!/[a-zA-Z]/.test(password)) {
        errorEl.textContent = '密码必须包含字母';
        errorEl.style.display = 'block';
        return;
    }
    if (!/[0-9]/.test(password)) {
        errorEl.textContent = '密码必须包含数字';
        errorEl.style.display = 'block';
        return;
    }

    fetch('/api/create-admin', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${authToken}`
        },
        body: JSON.stringify({username, password, real_name: realName})
    })
    .then(res => res.json())
    .then(result => {
        if (result.success) {
            alert('管理员账户创建成功！初始账户已禁用。\n\n请使用新账户重新登录。');
            authToken = '';
            currentUser = null;
            userRole = '';
            isDefaultUser = false;
            localStorage.removeItem('token');
            localStorage.removeItem('user');
            localStorage.removeItem('isDefaultUser');
            document.getElementById('createAdminPage').style.display = 'none';
            document.getElementById('loginPage').style.display = 'flex';
            document.getElementById('defaultAccountInfo').style.display = 'none';
        } else {
            errorEl.textContent = result.error || '创建失败';
            errorEl.style.display = 'block';
        }
    })
    .catch(err => {
        errorEl.textContent = '创建失败：' + err.message;
        errorEl.style.display = 'block';
    });
};
