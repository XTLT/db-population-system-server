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

function doDownloadPaymentTemplate(paymentType, fileName) {
    fetch(`/api/template/payment/${paymentType}`, {
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
        a.download = fileName;
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

function recoverPerson(deletedId, name) {
    if (!confirm(`确定要找回 ${name} 吗？`)) return;
    apiRequest('POST', `/api/recover/${deletedId}`).then(result => {
        if (result.success) {
            alert('找回成功！');
            loadDeleted();
        } else {
            alert('找回失败：' + (result.error || '未知错误'));
        }
    }).catch(err => {
        alert('找回失败：' + ((err && err.message) || '网络错误'));
    });
}
