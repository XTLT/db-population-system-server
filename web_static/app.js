let currentPersonId = null;
let currentHuHao = null;
let authToken = localStorage.getItem('token') || '';
let currentUser = null;
let userRole = '';
let currentPersonUpdatedAt = '';
let currentPersonLandArea = '';
let isDefaultUser = false;

function apiRequest(method, path, data = null) {
    const headers = {'Content-Type': 'application/json'};
    if (authToken) {
        headers['Authorization'] = `Bearer ${authToken}`;
    }
    const opts = {method, headers};
    if (data) opts.body = JSON.stringify(data);
    return fetch(path, opts).then(res => {
        if (res.status === 401) {
            showLogin();
            throw new Error('登录已过期');
        }
        return res.json().catch(() => ({error: '请求失败'}));
    });
}

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

function displayNames(persons) {
    const nameList = document.getElementById('nameList');
    nameList.innerHTML = '';
    document.getElementById('familyInfo').style.display = 'none';
    document.getElementById('personDetail').style.display = 'none';

    if (persons.length === 0) {
        nameList.innerHTML = '<p style="color: red; font-weight: bold;">未找到该人员</p>';
        return;
    }

    persons.forEach(p => {
        const btn = document.createElement('button');
        btn.className = 'name-btn' + (p.is_migrated === '是' ? ' migrated' : '');
        btn.textContent = p.name;
        btn.onclick = () => showFamily(p.hu_hao, p.name);
        nameList.appendChild(btn);
    });
}

function showFamily(huHao, name) {
    currentHuHao = huHao;
    document.getElementById('familyInfo').style.display = 'block';
    document.getElementById('personDetail').style.display = 'none';

    apiRequest('GET', `/api/family/${huHao}`)
        .then(data => {
            const sameNameCount = data.filter(m => m.name === name).length;
            document.getElementById('familyTitle').textContent =
                `您选择查看：${name}（共找到 ${sameNameCount} 个同名人员）`;
            displayFamily(data);
        });
}

function displayFamily(members) {
    const tbody = document.getElementById('familyBody');
    tbody.innerHTML = '';
    const canEdit = userRole === 'admin' || userRole === 'user';

    members.forEach(m => {
        const tr = document.createElement('tr');
        if (m.is_dead === '是') tr.className = 'dead';
        if (m.is_migrated === '是') tr.className = 'migrated';

        const editBtn = canEdit
            ? `<button onclick="showPerson('${m.id}')" class="btn-edit" style="padding:5px 10px;font-size:12px;">详情</button>`
            : `<button onclick="showPerson('${m.id}')" class="btn-cancel" style="padding:5px 10px;font-size:12px;">查看</button>`;

        tr.innerHTML = `
            <td>${m.name}</td>
            <td>${m.id_card}</td>
            <td>${m.relation}</td>
            <td>${m.age}</td>
            <td>${m.phone === '无' ? '' : m.phone}</td>
            <td>${m.land_area || ''}</td>
            <td>${m.is_dead === '是' ? '已故' : (m.is_migrated === '是' ? '已迁出' : '正常')}</td>
            <td class="student-mark">${m.student_mark}</td>
            <td>${editBtn}</td>
        `;
        tbody.appendChild(tr);
    });
}

function showPerson(personId) {
    currentPersonId = personId;
    document.getElementById('personDetail').style.display = 'block';

    apiRequest('GET', `/api/person/${personId}`)
        .then(data => {
            currentPersonUpdatedAt = data.updated_at || '';
            let html = `
                <div class="detail-item"><label>姓名</label><span>${data.name}</span></div>
                <div class="detail-item"><label>身份证号</label><span>${data.id_card}</span></div>
                <div class="detail-item"><label>户号</label><span>${data.hu_hao}</span></div>
                <div class="detail-item"><label>与户主关系</label><span>${data.relation}</span></div>
                <div class="detail-item"><label>年龄</label><span>${data.age}</span></div>
                <div class="detail-item"><label>电话</label><span>${data.phone === '无' ? '' : data.phone}</span></div>
                <div class="detail-item"><label>状态</label><span>${data.is_dead === '是' ? '已故' : (data.is_migrated === '是' ? '已迁出' : '正常')}</span></div>
                <div class="detail-item"><label>地址</label><span>${data.address || ''}</span></div>
                <div class="detail-item"><label>社保卡号1</label><span>${data.social_card1 === '无' ? '' : data.social_card1}</span></div>
                <div class="detail-item"><label>社保卡号2</label><span>${data.social_card2 === '无' ? '' : data.social_card2}</span></div>
                <div class="detail-item"><label>社保卡号3</label><span>${data.social_card3 === '无' ? '' : data.social_card3}</span></div>
                <div class="detail-item"><label>脱贫户</label><span>${data.poor_type === '无' ? '' : data.poor_type}</span></div>
                <div class="detail-item"><label>备注</label><span>${data.remark === '无' ? '' : data.remark}</span></div>
                <div class="detail-item"><label>残疾</label><span>${data.disability === '无' ? '' : data.disability}</span></div>
                <div class="detail-item"><label>残疾等级</label><span>${data.dis_level === '无' ? '' : data.dis_level}</span></div>
                <div class="detail-item"><label>低保</label><span>${data.dibao === '无' ? '' : data.dibao}</span></div>
                <div class="detail-item"><label>计生家庭</label><span>${data.jisheng === '无' ? '' : data.jisheng}</span></div>
                <div class="detail-item"><label>土地面积</label><span>${data.land_area || ''}</span></div>
                ${data.land_area_change_reason ? `<div class="detail-item"><label>土地变更原因</label><span>${data.land_area_change_reason}</span></div><div class="detail-item"><label>土地变更时间</label><span>${data.land_area_change_time}</span></div>` : ''}
            `;

            if (data.education) {
                html += `
                    <div class="detail-item" style="grid-column: span 2;"><label>就读信息</label></div>
                    <div class="detail-item"><label>学校</label><span>${data.education.school_name}</span></div>
                    <div class="detail-item"><label>年级</label><span>${data.education.grade}</span></div>
                    <div class="detail-item"><label>班级</label><span>${data.education.class_name}</span></div>
                    <div class="detail-item"><label>监护人</label><span>${data.education.guardian}</span></div>
                    <div class="detail-item"><label>监护人电话</label><span>${data.education.guardian_phone}</span></div>
                    <div class="detail-item"><label>留守儿童</label><span>${data.education.is_left_behind}</span></div>
                    <div class="detail-item"><label>学生状态</label><span>${data.education.student_status}</span></div>
                `;
            }

            document.getElementById('detailContent').innerHTML = html;
        });
}

function editPerson() {
    if (!currentPersonId) return;

    apiRequest('GET', `/api/person/${currentPersonId}`)
        .then(data => {
            currentPersonUpdatedAt = data.updated_at || '';
            document.getElementById('editId').value = data.id;
            document.getElementById('editName').value = data.name;
            document.getElementById('editIdCard').value = data.id_card;
            document.getElementById('editRelation').value = data.relation || '';
            document.getElementById('editPhone').value = data.phone === '无' ? '' : data.phone;
            document.getElementById('editIsDead').value = data.is_dead;
            document.getElementById('editLandArea').value = data.land_area || '';
            currentPersonLandArea = data.land_area || '';
            document.getElementById('editSocial1').value = data.social_card1 === '无' ? '' : (data.social_card1 || '');
            document.getElementById('editSocial2').value = data.social_card2 === '无' ? '' : (data.social_card2 || '');
            document.getElementById('editSocial3').value = data.social_card3 === '无' ? '' : (data.social_card3 || '');

            if (data.education) {
                document.getElementById('editEduSchool').value = data.education.school_name || '';
                document.getElementById('editEduClass').value = data.education.class_name || '';
                document.getElementById('editEduGuardian').value = data.education.guardian || '';
                document.getElementById('editEduGuardianPhone').value = data.education.guardian_phone || '';
                document.getElementById('editEduLeftBehind').value = data.education.is_left_behind || '否';
                document.getElementById('editEduStatus').value = data.education.student_status || '在读';
                document.getElementById('editEduEnrollDate').value = data.education.enrollment_date || '';
                setTimeout(() => { document.getElementById('editEduGrade').value = data.education.grade || ''; }, 0);
            } else {
                document.getElementById('editEduSchool').value = '';
                document.getElementById('editEduGrade').value = '';
                document.getElementById('editEduClass').value = '';
                document.getElementById('editEduGuardian').value = '';
                document.getElementById('editEduGuardianPhone').value = '';
                document.getElementById('editEduLeftBehind').value = '否';
                document.getElementById('editEduStatus').value = '在读';
                document.getElementById('editEduEnrollDate').value = '';
            }

            const gradeSelect = document.getElementById('editEduGrade');
            if (gradeSelect.options.length <= 1) {
                const grades = [
                    ['','请选择'],['T1','托班'],
                    ['K1','幼儿园小班'],['K2','幼儿园中班'],['K3','幼儿园大班'],
                    ['G1','小学1年级'],['G2','小学2年级'],['G3','小学3年级'],['G4','小学4年级'],['G5','小学5年级'],['G6','小学6年级'],
                    ['G7','初中1年级'],['G8','初中2年级'],['G9','初中3年级'],
                    ['G10','高中1年级'],['G11','高中2年级'],['G12','高中3年级'],
                    ['V1','职高1年级'],['V2','职高2年级'],['V3','职高3年级'],
                    ['C1','中专1年级'],['C2','中专2年级'],['C3','中专3年级'],
                    ['U1','大学1年级'],['U2','大学2年级'],['U3','大学3年级'],['U4','大学4年级'],['U5','大学5年级'],
                    ['M1','硕士1年级'],['M2','硕士2年级'],['M3','硕士3年级'],
                    ['D1','博士1年级'],['D2','博士2年级'],['D3','博士3年级'],['D4','博士4年级'],
                    ['GRADUATED','已毕业']
                ];
                grades.forEach(([code, label]) => {
                    const opt = document.createElement('option');
                    opt.value = code;
                    opt.textContent = label;
                    gradeSelect.appendChild(opt);
                });
            }

            document.getElementById('editModal').style.display = 'flex';
        });
}

function closeEdit() {
    document.getElementById('editModal').style.display = 'none';
}

document.getElementById('editForm').onsubmit = function(e) {
    e.preventDefault();
    const id = document.getElementById('editId').value;
    const newLandArea = document.getElementById('editLandArea').value;
    const oldLandArea = currentPersonLandArea || '';

    if (newLandArea !== oldLandArea) {
        const reason = prompt(`土地面积从「${oldLandArea || '空'}」变更为「${newLandArea || '空'}」\n\n请输入变更原因：`);
        if (!reason || !reason.trim()) {
            alert('土地面积变更时必须填写变更原因！');
            return;
        }
        window._landAreaChangeReason = reason.trim();
    } else {
        window._landAreaChangeReason = '';
    }

    const data = {
        name: document.getElementById('editName').value,
        relation: document.getElementById('editRelation').value,
        phone: document.getElementById('editPhone').value || '无',
        is_dead: document.getElementById('editIsDead').value,
        land_area: newLandArea,
        land_area_change_reason: window._landAreaChangeReason,
        social_card1: document.getElementById('editSocial1').value || '无',
        social_card2: document.getElementById('editSocial2').value || '无',
        social_card3: document.getElementById('editSocial3').value || '无',
        updated_at: currentPersonUpdatedAt
    };

    fetch(`/api/person/${id}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${authToken}`
        },
        body: JSON.stringify(data)
    })
    .then(res => {
        if (res.status === 409) {
            return res.json().then(result => {
                alert(result.message || '数据冲突，请刷新后重试');
                closeEdit();
                showFamily(currentHuHao, data.name);
            });
        }
        return res.json().catch(() => ({error: '请求失败'}));
    })
    .then(result => {
        if (result && result.success) {
            currentPersonUpdatedAt = result.updated_at || '';

            const eduData = {
                school_name: document.getElementById('editEduSchool').value.trim(),
                grade: document.getElementById('editEduGrade').value,
                class_name: document.getElementById('editEduClass').value.trim(),
                guardian: document.getElementById('editEduGuardian').value.trim(),
                guardian_phone: document.getElementById('editEduGuardianPhone').value.trim(),
                is_left_behind: document.getElementById('editEduLeftBehind').value,
                student_status: document.getElementById('editEduStatus').value,
                enrollment_date: document.getElementById('editEduEnrollDate').value
            };

            return fetch(`/api/person/${id}/education`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${authToken}`
                },
                body: JSON.stringify(eduData)
            }).then(r => r.json()).then(() => {
                closeEdit();
                showFamily(currentHuHao, data.name);
                showPerson(id);
            });
        }
    });
};

function migratePerson() {
    if (!currentPersonId) return;
    document.getElementById('migrateId').value = currentPersonId;
    document.getElementById('migrateDate').value = new Date().toISOString().split('T')[0];
    document.getElementById('migrateModal').style.display = 'flex';
}

function closeMigrate() {
    document.getElementById('migrateModal').style.display = 'none';
}

document.getElementById('migrateForm').onsubmit = function(e) {
    e.preventDefault();
    const id = document.getElementById('migrateId').value;
    const data = {
        date: document.getElementById('migrateDate').value,
        place: document.getElementById('migratePlace').value,
        reason: document.getElementById('migrateReason').value
    };

    apiRequest('POST', `/api/person/${id}/migrate`, data)
        .then(result => {
            if (result.success) {
                closeMigrate();
                alert('户籍迁出操作成功！');
                showFamily(currentHuHao, '');
            }
        });
};

function deletePerson() {
    if (!currentPersonId) return;
    if (!confirm('确定要删除该人员吗？删除后可在找回功能中恢复。')) return;
    if (!confirm('请再次确认：是否删除该人员？')) return;

    apiRequest('DELETE', `/api/person/${currentPersonId}`)
        .then(result => {
            if (result.success) {
                alert('人员已删除！');
                document.getElementById('personDetail').style.display = 'none';
                showFamily(currentHuHao, '');
            }
        });
}

function closeDetail() {
    document.getElementById('personDetail').style.display = 'none';
}

document.getElementById('searchInput').addEventListener('keypress', function(e) {
    if (e.key === 'Enter') doSearch();
});

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

function doSearch() {
    const name = document.getElementById('searchInput').value.trim();
    if (!name) return;
    apiRequest('GET', `/api/search?name=${encodeURIComponent(name)}`)
        .then(data => displayNames(data.results || data));
}

function showImportModal() {
    document.getElementById('importModal').style.display = 'flex';
    document.getElementById('importFile').value = '';
    document.getElementById('importProgress').style.display = 'none';
}

function closeImportModal() {
    document.getElementById('importModal').style.display = 'none';
}

function doImport() {
    const file = document.getElementById('importFile').files[0];
    if (!file) { alert('请选择文件'); return; }
    const mode = document.getElementById('importMode').value;
    const formData = new FormData();
    formData.append('file', file);
    formData.append('mode', mode);

    document.getElementById('importProgress').style.display = 'block';
    document.getElementById('importStatus').textContent = '正在导入...';

    fetch('/api/import/excel', {
        method: 'POST',
        headers: {'Authorization': `Bearer ${authToken}`},
        body: formData
    }).then(res => res.json().catch(() => ({error: '请求失败'}))).then(result => {
        if (result.error) {
            document.getElementById('importStatus').textContent = '导入失败：' + result.error;
        } else {
            const msg = `导入完成！成功：${result.imported}条，跳过：${result.skipped}条`;
            document.getElementById('importStatus').textContent = msg;
        }
    }).catch(err => {
        document.getElementById('importStatus').textContent = '导入失败：' + err.message;
    });
}

function doExportExcel() {
    fetch('/api/export/excel', {
        headers: {'Authorization': `Bearer ${authToken}`}
    }).then(res => {
        if (!res.ok) return res.json().then(d => { throw new Error(d.error || '导出失败'); });
        return res.blob();
    }).then(blob => {
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `人口信息_${new Date().toISOString().slice(0,10).replace(/-/g,'')}.xlsx`;
        a.click();
        URL.revokeObjectURL(url);
    }).catch(err => alert('导出失败：' + err.message));
}

function doDownloadTemplate() {
    fetch('/api/template/excel', {
        headers: {'Authorization': `Bearer ${authToken}`}
    }).then(res => {
        if (res.status === 401) {
            showLogin();
            throw new Error('登录已过期，请重新登录');
        }
        if (!res.ok) {
            if (res.headers.get('content-type')?.includes('json')) {
                return res.json().then(d => { throw new Error(d.error || '下载失败'); });
            }
            throw new Error('下载失败');
        }
        return res.blob();
    }).then(blob => {
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = '人口信息导入模板.xlsx';
        a.click();
        URL.revokeObjectURL(url);
    }).catch(err => alert(err.message));
}

function doBackup() {
    if (!confirm('确定要备份数据库吗？')) return;
    apiRequest('POST', '/api/backup').then(result => {
        if (result.success) {
            alert('备份成功！');
        } else {
            alert('备份失败：' + (result.error || '未知错误'));
        }
    });
}

function showDeletedModal() {
    document.getElementById('deletedModal').style.display = 'flex';
    loadDeleted();
}

function closeDeletedModal() {
    document.getElementById('deletedModal').style.display = 'none';
}

function loadDeleted() {
    apiRequest('GET', '/api/deleted').then(persons => {
        const tbody = document.getElementById('deletedBody');
        tbody.innerHTML = '';
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
    });
}

function recoverPerson(deletedId, name) {
    if (!confirm(`确定要找回 ${name} 吗？`)) return;
    apiRequest('POST', `/api/recover/${deletedId}`).then(result => {
        if (result.success) {
            alert('找回成功！');
            loadDeleted();
        } else {
            alert('找回失败：' + (result.error || '未知错误'));
        }
    });
}

function showStudentModal() {
    document.getElementById('studentModal').style.display = 'flex';
    loadGradeOptions();
    searchStudents();
}

function closeStudentModal() {
    document.getElementById('studentModal').style.display = 'none';
}

function loadGradeOptions() {
    const gradeSelect = document.getElementById('stuGrade');
    if (gradeSelect.options.length > 1) return;
    const grades = [
        ['K1','幼儿园小班'],['K2','幼儿园中班'],['K3','幼儿园大班'],
        ['G1','小学1年级'],['G2','小学2年级'],['G3','小学3年级'],['G4','小学4年级'],['G5','小学5年级'],['G6','小学6年级'],
        ['G7','初中1年级'],['G8','初中2年级'],['G9','初中3年级'],
        ['G10','高中1年级'],['G11','高中2年级'],['G12','高中3年级']
    ];
    grades.forEach(([code, name]) => {
        const opt = document.createElement('option');
        opt.value = code;
        opt.textContent = name;
        gradeSelect.appendChild(opt);
    });
}

function searchStudents() {
    const params = new URLSearchParams();
    const school = document.getElementById('stuSchool').value;
    const grade = document.getElementById('stuGrade').value;
    if (school) params.set('school', school);
    if (grade) params.set('grade', grade);

    apiRequest('GET', `/api/students/search?${params}`).then(students => {
        const tbody = document.getElementById('studentBody');
        tbody.innerHTML = '';
        if (students.length === 0) {
            tbody.innerHTML = '<tr><td colspan="9" style="color:#999;">没有学生数据</td></tr>';
            return;
        }
        const canEdit = userRole === 'admin' || userRole === 'user';
        students.forEach(s => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${s.name}</td>
                <td>${s.id_card}</td>
                <td>${s.school_name}</td>
                <td>${s.grade_display || s.grade}</td>
                <td>${s.class_name}</td>
                <td>${s.guardian}</td>
                <td>${s.is_left_behind}</td>
                <td>${s.student_status}</td>
                <td>${canEdit ? `<button onclick="editEducation('${s.person_id}','${s.name}','${s.school_name}','${s.grade}','${s.class_name}','${s.guardian}','${s.guardian_phone || ''}','${s.is_left_behind}','${s.student_status}','${s.enrollment_date || ''}')" class="btn-edit" style="padding:4px 8px;font-size:12px;">编辑</button>` : ''}</td>
            `;
            tbody.appendChild(tr);
        });
    });
}

function showStuImportModal() {
    document.getElementById('stuImportModal').style.display = 'flex';
    document.getElementById('stuImportFile').value = '';
    document.getElementById('stuImportProgress').style.display = 'none';
}

function closeStuImportModal() {
    document.getElementById('stuImportModal').style.display = 'none';
}

function doStuImport() {
    const file = document.getElementById('stuImportFile').files[0];
    if (!file) { alert('请选择文件'); return; }
    const formData = new FormData();
    formData.append('file', file);

    document.getElementById('stuImportProgress').style.display = 'block';
    document.getElementById('stuImportStatus').textContent = '正在导入...';

    fetch('/api/students/import', {
        method: 'POST',
        headers: {'Authorization': `Bearer ${authToken}`},
        body: formData
    }).then(res => res.json().catch(() => ({error: '请求失败'}))).then(result => {
        if (result.error) {
            document.getElementById('stuImportStatus').textContent = '导入失败：' + result.error;
        } else {
            const msg = `导入完成！成功：${result.imported}条，更新：${result.updated}条，跳过：${result.skipped}条`;
            document.getElementById('stuImportStatus').textContent = msg;
        }
    }).catch(err => {
        document.getElementById('stuImportStatus').textContent = '导入失败：' + err.message;
    });
}

function doExportStudents() {
    fetch('/api/students/export', {
        headers: {'Authorization': `Bearer ${authToken}`}
    }).then(res => {
        if (!res.ok) return res.json().then(d => { throw new Error(d.error || '导出失败'); });
        return res.blob();
    }).then(blob => {
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `学生就读信息_${new Date().toISOString().slice(0,10).replace(/-/g,'')}.xlsx`;
        a.click();
        URL.revokeObjectURL(url);
    }).catch(err => alert('导出失败：' + err.message));
}

function doDownloadStudentTemplate() {
    fetch('/api/template/student', {
        headers: {'Authorization': `Bearer ${authToken}`}
    }).then(res => {
        if (res.status === 401) {
            showLogin();
            throw new Error('登录已过期，请重新登录');
        }
        if (!res.ok) {
            if (res.headers.get('content-type')?.includes('json')) {
                return res.json().then(d => { throw new Error(d.error || '下载失败'); });
            }
            throw new Error('下载失败');
        }
        return res.blob();
    }).then(blob => {
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = '学生就读信息模板.xlsx';
        a.click();
        URL.revokeObjectURL(url);
    }).catch(err => alert(err.message));
}

function showLogsModal() {
    document.getElementById('logsModal').style.display = 'flex';
    loadLogs();
}

function closeLogsModal() {
    document.getElementById('logsModal').style.display = 'none';
}

function loadLogs() {
    apiRequest('GET', '/api/logs?limit=200').then(logs => {
        const tbody = document.getElementById('logsBody');
        tbody.innerHTML = '';
        if (logs.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" style="color:#999;">暂无日志</td></tr>';
            return;
        }
        logs.forEach(l => {
            const tr = document.createElement('tr');
            if (l.is_high_risk === '是') tr.style.backgroundColor = '#fff0f0';
            tr.innerHTML = `
                <td>${l.created_at}</td>
                <td>${l.username}</td>
                <td>${l.operation_type}</td>
                <td>${l.operation_target || ''}</td>
                <td>${l.ip_address}</td>
                <td>${l.client_type}</td>
                <td>${l.is_high_risk === '是' ? '⚠️' : ''}</td>
            `;
            tbody.appendChild(tr);
        });
    });
}

function editEducation(personId, name, school, grade, className, guardian, guardianPhone, isLeftBehind, status, enrollDate) {
    document.getElementById('eduPersonId').value = personId;
    document.getElementById('eduName').value = name;
    document.getElementById('eduSchool').value = school || '';
    document.getElementById('eduClass').value = className || '';
    document.getElementById('eduGuardian').value = guardian || '';
    document.getElementById('eduGuardianPhone').value = guardianPhone || '';
    document.getElementById('eduLeftBehind').value = isLeftBehind || '否';
    document.getElementById('eduStatus').value = status || '在读';
    document.getElementById('eduEnrollDate').value = enrollDate || '';

    const gradeSelect = document.getElementById('eduGrade');
    if (gradeSelect.options.length <= 1) {
        const grades = [
            ['','请选择'],['T1','托班'],
            ['K1','幼儿园小班'],['K2','幼儿园中班'],['K3','幼儿园大班'],
            ['G1','小学1年级'],['G2','小学2年级'],['G3','小学3年级'],['G4','小学4年级'],['G5','小学5年级'],['G6','小学6年级'],
            ['G7','初中1年级'],['G8','初中2年级'],['G9','初中3年级'],
            ['G10','高中1年级'],['G11','高中2年级'],['G12','高中3年级'],
            ['V1','职高1年级'],['V2','职高2年级'],['V3','职高3年级'],
            ['C1','中专1年级'],['C2','中专2年级'],['C3','中专3年级'],
            ['U1','大学1年级'],['U2','大学2年级'],['U3','大学3年级'],['U4','大学4年级'],['U5','大学5年级'],
            ['M1','硕士1年级'],['M2','硕士2年级'],['M3','硕士3年级'],
            ['D1','博士1年级'],['D2','博士2年级'],['D3','博士3年级'],['D4','博士4年级'],
            ['GRADUATED','已毕业']
        ];
        grades.forEach(([code, label]) => {
            const opt = document.createElement('option');
            opt.value = code;
            opt.textContent = label;
            gradeSelect.appendChild(opt);
        });
    }
    gradeSelect.value = grade || '';

    document.getElementById('eduEditModal').style.display = 'flex';
}

function closeEduEdit() {
    document.getElementById('eduEditModal').style.display = 'none';
}

document.getElementById('eduEditForm').onsubmit = function(e) {
    e.preventDefault();
    const personId = document.getElementById('eduPersonId').value;
    const data = {
        school_name: document.getElementById('eduSchool').value.trim(),
        grade: document.getElementById('eduGrade').value,
        class_name: document.getElementById('eduClass').value.trim(),
        guardian: document.getElementById('eduGuardian').value.trim(),
        guardian_phone: document.getElementById('eduGuardianPhone').value.trim(),
        is_left_behind: document.getElementById('eduLeftBehind').value,
        student_status: document.getElementById('eduStatus').value,
        enrollment_date: document.getElementById('eduEnrollDate').value
    };

    fetch(`/api/person/${personId}/education`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${authToken}`
        },
        body: JSON.stringify(data)
    })
    .then(res => res.json())
    .then(result => {
        if (result.success) {
            closeEduEdit();
            searchStudents();
        } else {
            alert(result.error || '保存失败');
        }
    })
    .catch(err => alert('保存失败：' + err.message));
};

function showAddHouseholdModal() {
    fetch('/api/household/new_number', {
        headers: {'Authorization': `Bearer ${authToken}`}
    }).then(r => r.json()).then(data => {
        document.getElementById('newHhHuhao').value = data.hu_hao || '';
    });
    document.getElementById('newHhName').value = '';
    document.getElementById('newHhIdCard').value = '';
    document.getElementById('newHhAddress').value = '';
    document.getElementById('newHhPhone').value = '';
    document.getElementById('newHhLandArea').value = '';
    document.getElementById('addHouseholdModal').style.display = 'flex';
}

function closeAddHouseholdModal() {
    document.getElementById('addHouseholdModal').style.display = 'none';
}

document.getElementById('addHouseholdForm').onsubmit = function(e) {
    e.preventDefault();
    const data = {
        hu_hao: document.getElementById('newHhHuhao').value.trim(),
        name: document.getElementById('newHhName').value.trim(),
        id_card: document.getElementById('newHhIdCard').value.trim(),
        address: document.getElementById('newHhAddress').value.trim(),
        phone: document.getElementById('newHhPhone').value.trim(),
        land_area: document.getElementById('newHhLandArea').value.trim()
    };
    fetch('/api/household/add', {
        method: 'POST',
        headers: {'Content-Type': 'application/json', 'Authorization': `Bearer ${authToken}`},
        body: JSON.stringify(data)
    }).then(r => r.json()).then(result => {
        if (result.success) {
            closeAddHouseholdModal();
            alert('新户创建成功！');
        } else {
            alert(result.error || '创建失败');
        }
    }).catch(err => alert('创建失败：' + err.message));
};

let splitPersons = [];
function showSplitHouseholdModal() {
    if (!currentHuHao) { alert('请先选择一个家庭'); return; }
    apiRequest('GET', `/api/family/${currentHuHao}`).then(members => {
        splitPersons = members;
        const list = document.getElementById('splitPersonList');
        list.innerHTML = members.map(m =>
            `<label style="display:block;padding:5px;"><input type="checkbox" value="${m.id}" class="split-check"> ${m.name} (${m.id_card})</label>`
        ).join('');
        document.getElementById('splitHouseholdModal').style.display = 'flex';
    });
}

function closeSplitHouseholdModal() {
    document.getElementById('splitHouseholdModal').style.display = 'none';
}

function doSplitHousehold() {
    const ids = [...document.querySelectorAll('.split-check:checked')].map(c => c.value);
    if (ids.length === 0) { alert('请选择要分户的人员'); return; }
    if (!confirm(`确定将 ${ids.length} 人分出为新户？`)) return;
    fetch('/api/household/split', {
        method: 'POST',
        headers: {'Content-Type': 'application/json', 'Authorization': `Bearer ${authToken}`},
        body: JSON.stringify({person_ids: ids})
    }).then(r => r.json()).then(result => {
        if (result.success) {
            closeSplitHouseholdModal();
            alert(`分户成功！新户号：${result.new_hu_hao}`);
            doSearch();
        } else {
            alert(result.error || '分户失败');
        }
    }).catch(err => alert('分户失败：' + err.message));
}

function showMergeHouseholdModal() {
    document.getElementById('mergeTargetHuHao').value = currentHuHao || '';
    apiRequest('GET', `/api/family/${currentHuHao || ''}`).then(members => {
        const list = document.getElementById('mergePersonList');
        list.innerHTML = members.map(m =>
            `<label style="display:block;padding:5px;"><input type="checkbox" value="${m.id}" class="merge-check"> ${m.name} (${m.id_card}) - 户号:${currentHuHao}</label>`
        ).join('');
        document.getElementById('mergeHouseholdModal').style.display = 'flex';
    }).catch(() => {
        document.getElementById('mergePersonList').innerHTML = '<p style="color:red;">请先搜索并选择一个家庭</p>';
        document.getElementById('mergeHouseholdModal').style.display = 'flex';
    });
}

function closeMergeHouseholdModal() {
    document.getElementById('mergeHouseholdModal').style.display = 'none';
}

function doMergeHousehold() {
    const target = document.getElementById('mergeTargetHuHao').value.trim();
    const ids = [...document.querySelectorAll('.merge-check:checked')].map(c => c.value);
    if (!target) { alert('请输入目标户号'); return; }
    if (ids.length === 0) { alert('请选择要合并的人员'); return; }
    if (!confirm(`确定将 ${ids.length} 人合并到户号 ${target}？`)) return;
    fetch('/api/household/merge', {
        method: 'POST',
        headers: {'Content-Type': 'application/json', 'Authorization': `Bearer ${authToken}`},
        body: JSON.stringify({target_hu_hao: target, person_ids: ids})
    }).then(r => r.json()).then(result => {
        if (result.success) {
            closeMergeHouseholdModal();
            alert('合户成功！');
            doSearch();
        } else {
            alert(result.error || '合户失败');
        }
    }).catch(err => alert('合户失败：' + err.message));
}

function showAddPersonModal() {
    if (!currentHuHao) { alert('请先选择一个家庭'); return; }
    document.getElementById('addPersonHuHao').value = currentHuHao;
    document.getElementById('addPersonName').value = '';
    document.getElementById('addPersonIdCard').value = '';
    document.getElementById('addPersonRelation').value = '';
    document.getElementById('addPersonPhone').value = '';
    document.getElementById('addPersonLandArea').value = '';
    apiRequest('GET', `/api/family/${currentHuHao}`).then(members => {
        if (members.length > 0) {
            document.getElementById('addPersonAddress').value = members[0].address || '';
        }
    });
    document.getElementById('addPersonModal').style.display = 'flex';
}

function closeAddPersonModal() {
    document.getElementById('addPersonModal').style.display = 'none';
}

document.getElementById('addPersonForm').onsubmit = function(e) {
    e.preventDefault();
    const data = {
        hu_hao: document.getElementById('addPersonHuHao').value,
        name: document.getElementById('addPersonName').value.trim(),
        id_card: document.getElementById('addPersonIdCard').value.trim(),
        relation: document.getElementById('addPersonRelation').value.trim(),
        address: document.getElementById('addPersonAddress').value.trim(),
        phone: document.getElementById('addPersonPhone').value.trim() || '无',
        land_area: document.getElementById('addPersonLandArea').value.trim()
    };
    if (!data.name || !data.id_card) {
        alert('姓名和身份证号不能为空！');
        return;
    }
    fetch('/api/person', {
        method: 'POST',
        headers: {'Content-Type': 'application/json', 'Authorization': `Bearer ${authToken}`},
        body: JSON.stringify(data)
    }).then(r => r.json()).then(result => {
        if (result.success) {
            closeAddPersonModal();
            showFamily(currentHuHao, '');
        } else {
            alert(result.error || '添加失败');
        }
    }).catch(err => alert('添加失败：' + err.message));
};

// 地力补贴相关函数
function showLandSubsidyModal() {
    document.getElementById('landSubsidyModal').style.display = 'flex';
    loadSubsidyYears();
    loadLandSubsidies();
}

function closeLandSubsidyModal() {
    document.getElementById('landSubsidyModal').style.display = 'none';
}

function loadSubsidyYears() {
    apiRequest('GET', '/api/land_subsidy/years').then(data => {
        const select = document.getElementById('subsidyYear');
        select.innerHTML = '<option value="">全部年度</option>';
        if (data.years) {
            data.years.forEach(year => {
                select.innerHTML += `<option value="${year}">${year}</option>`;
            });
        }
    });
}

function loadLandSubsidies() {
    const year = document.getElementById('subsidyYear').value;
    const search = document.getElementById('subsidySearch').value;
    let url = '/api/land_subsidy?';
    if (year) url += `year=${year}&`;
    if (search) url += `search=${search}`;

    apiRequest('GET', url).then(data => {
        const tbody = document.getElementById('landSubsidyBody');
        tbody.innerHTML = '';
        if (data.subsidies) {
            data.subsidies.forEach(s => {
                const row = document.createElement('tr');
                const deleteBtn = userRole === 'admin'
                    ? `<button onclick="deleteLandSubsidy('${s.id}')" class="btn-delete" style="padding:4px 8px;font-size:12px;">删除</button>`
                    : '';
                row.innerHTML = `
                    <td>${s.name || ''}</td>
                    <td>${s.id_card || ''}</td>
                    <td>${s.certified_area || ''}</td>
                    <td>${s.subsidy_area || ''}</td>
                    <td>${s.base_standard || ''}</td>
                    <td>${s.rape_area || ''}</td>
                    <td>${s.rape_amount || ''}</td>
                    <td>${s.total_amount || ''}</td>
                    <td>${s.import_time || ''}</td>
                    <td>${deleteBtn}</td>
                `;
                tbody.appendChild(row);
            });
        }
    });
}

function showSubsidyImportModal() {
    document.getElementById('subsidyImportModal').style.display = 'flex';
    document.getElementById('subsidyImportYear').value = new Date().getFullYear();
    document.getElementById('subsidyImportFile').value = '';
    document.getElementById('subsidyImportProgress').style.display = 'none';
}

function closeSubsidyImportModal() {
    document.getElementById('subsidyImportModal').style.display = 'none';
}

function doSubsidyImport() {
    const year = document.getElementById('subsidyImportYear').value.trim();
    const fileInput = document.getElementById('subsidyImportFile');
    if (!year) { alert('请输入补贴年度'); return; }
    if (!fileInput.files.length) { alert('请选择文件'); return; }

    const formData = new FormData();
    formData.append('subsidy_year', year);
    formData.append('file', fileInput.files[0]);

    document.getElementById('subsidyImportProgress').style.display = 'block';
    document.getElementById('subsidyImportStatus').textContent = '正在导入...';

    fetch('/api/land_subsidy/import', {
        method: 'POST',
        headers: {'Authorization': `Bearer ${authToken}`},
        body: formData
    }).then(r => r.json()).then(result => {
        if (result.imported !== undefined) {
            let msg = `导入完成！\n成功：${result.imported}条\n跳过：${result.skipped}条`;
            if (result.errors && result.errors.length > 0) {
                msg += `\n错误：${result.errors.length}条\n` + result.errors.slice(0, 5).join('\n');
            }
            document.getElementById('subsidyImportStatus').textContent = msg;
            loadLandSubsidies();
        } else {
            document.getElementById('subsidyImportStatus').textContent = '导入失败：' + (result.error || '未知错误');
        }
    }).catch(err => {
        document.getElementById('subsidyImportStatus').textContent = '导入失败：' + err.message;
    });
}

function deleteLandSubsidy(id) {
    if (!confirm('确定要删除这条记录吗？')) return;
    fetch(`/api/land_subsidy/${id}`, {
        method: 'DELETE',
        headers: {'Authorization': `Bearer ${authToken}`}
    }).then(r => r.json()).then(result => {
        if (result.success) {
            loadLandSubsidies();
        } else {
            alert(result.error || '删除失败');
        }
    }).catch(err => alert('删除失败：' + err.message));
}

function exportLandSubsidies() {
    if (!authToken) {
        alert('请先登录');
        return;
    }
    const year = document.getElementById('subsidyYear').value;
    const search = document.getElementById('subsidySearch').value;
    let url = '/api/land_subsidy/export?';
    if (year) url += 'year=' + encodeURIComponent(year) + '&';
    if (search) url += 'search=' + encodeURIComponent(search) + '&';

    fetch(url, {
        method: 'GET',
        headers: {'Authorization': 'Bearer ' + authToken}
    }).then(res => {
        if (!res.ok) {
            return res.json().then(data => { throw new Error(data.error || '导出失败'); });
        }
        return res.blob();
    }).then(blob => {
        const link = document.createElement('a');
        link.href = URL.createObjectURL(blob);
        link.download = '地力补贴.xlsx';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(link.href);
    }).catch(err => alert('导出失败：' + err.message));
}

// 待遇发放相关函数
function showTreatmentPaymentModal() {
    document.getElementById('treatmentPaymentModal').style.display = 'flex';
    loadTreatmentPayments();
}

function closeTreatmentPaymentModal() {
    document.getElementById('treatmentPaymentModal').style.display = 'none';
}

function loadTreatmentPayments() {
    const period = document.getElementById('treatmentPeriodSearch').value;
    const idCard = document.getElementById('treatmentIdCardSearch').value;
    const subsidyType = document.getElementById('treatmentSubsidyTypeFilter').value;
    let url = '/api/treatment_payment?';
    if (period) url += `period=${period}&`;
    if (idCard) url += `id_card=${idCard}&`;
    if (subsidyType) url += `subsidy_type=${encodeURIComponent(subsidyType)}&`;

    apiRequest('GET', url).then(data => {
        const tbody = document.getElementById('treatmentPaymentBody');
        tbody.innerHTML = '';
        if (data.payments) {
            data.payments.forEach(p => {
                const row = document.createElement('tr');
                const deleteBtn = userRole === 'admin'
                    ? `<button onclick="deleteTreatmentPayment('${p.id}')" class="btn-delete" style="padding:4px 8px;font-size:12px;">删除</button>`
                    : '';
                row.innerHTML = `
                    <td>${p.period || ''}</td>
                    <td>${p.name || ''}</td>
                    <td>${p.id_card || ''}</td>
                    <td>${p.village || ''}</td>
                    <td style="font-size:11px;">${p.bank_account || ''}</td>
                    <td>${p.amount || ''}</td>
                    <td>${p.payment_status || ''}</td>
                    <td>${p.subsidy_type || ''}</td>
                    <td style="font-size:11px;max-width:120px;overflow:hidden;text-overflow:ellipsis;" title="${p.import_source || ''}">${p.import_source || ''}</td>
                    <td>${deleteBtn}</td>
                `;
                tbody.appendChild(row);
            });
        }
    });
}

function showTreatmentImportModal() {
    document.getElementById('treatmentImportModal').style.display = 'flex';
    document.getElementById('treatmentImportFile').value = '';
    document.getElementById('treatmentImportProgress').style.display = 'none';
}

function closeTreatmentImportModal() {
    document.getElementById('treatmentImportModal').style.display = 'none';
}

function doTreatmentImport() {
    const fileInput = document.getElementById('treatmentImportFile');
    if (!fileInput.files.length) { alert('请选择文件'); return; }

    const formData = new FormData();
    formData.append('file', fileInput.files[0]);

    document.getElementById('treatmentImportProgress').style.display = 'block';
    document.getElementById('treatmentImportStatus').textContent = '正在导入...';

    fetch('/api/treatment_payment/import', {
        method: 'POST',
        headers: {'Authorization': `Bearer ${authToken}`},
        body: formData
    }).then(r => r.json()).then(result => {
        if (result.imported !== undefined) {
            let msg = `导入完成！\n成功：${result.imported}条\n跳过：${result.skipped}条`;
            if (result.errors && result.errors.length > 0) {
                msg += `\n错误：${result.errors.length}条\n` + result.errors.slice(0, 5).join('\n');
            }
            if (result.not_found && result.not_found.length > 0) {
                const uniqueNotFound = [...new Set(result.not_found)];
                msg += `\n\n数据库中未找到的人员（${uniqueNotFound.length}人）：\n`;
                msg += uniqueNotFound.slice(0, 20).join('\n');
                if (uniqueNotFound.length > 20) {
                    msg += `\n...等${uniqueNotFound.length}人`;
                }
            }
            document.getElementById('treatmentImportStatus').textContent = msg;
            loadTreatmentPayments();
        } else {
            document.getElementById('treatmentImportStatus').textContent = '导入失败：' + (result.error || '未知错误');
        }
    }).catch(err => {
        document.getElementById('treatmentImportStatus').textContent = '导入失败：' + err.message;
    });
}

function deleteTreatmentPayment(id) {
    if (!confirm('确定要删除这条记录吗？')) return;
    fetch(`/api/treatment_payment/${id}`, {
        method: 'DELETE',
        headers: {'Authorization': `Bearer ${authToken}`}
    }).then(r => r.json()).then(result => {
        if (result.success) {
            loadTreatmentPayments();
        } else {
            alert(result.error || '删除失败');
        }
    }).catch(err => alert('删除失败：' + err.message));
}

function exportTreatmentPayments() {
    if (!authToken) {
        alert('请先登录');
        return;
    }
    const period = document.getElementById('treatmentPeriodSearch').value;
    const subsidyType = document.getElementById('treatmentSubsidyTypeFilter').value;
    let url = '/api/treatment_payment/export?';
    if (period) url += 'period=' + encodeURIComponent(period) + '&';
    if (subsidyType) url += 'subsidy_type=' + encodeURIComponent(subsidyType) + '&';

    fetch(url, {
        method: 'GET',
        headers: {'Authorization': 'Bearer ' + authToken}
    }).then(res => {
        if (!res.ok) {
            return res.json().then(data => { throw new Error(data.error || '导出失败'); });
        }
        return res.blob();
    }).then(blob => {
        const link = document.createElement('a');
        link.href = URL.createObjectURL(blob);
        link.download = '待遇发放.xlsx';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(link.href);
    }).catch(err => alert('导出失败：' + err.message));
}
