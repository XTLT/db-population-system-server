// 高龄补贴相关函数
function showElderlyAllowanceModal() {
    document.getElementById('elderlyAllowanceModal').style.display = 'flex';
    loadElderlyAllowances();
}

function closeElderlyAllowanceModal() {
    document.getElementById('elderlyAllowanceModal').style.display = 'none';
}

function loadElderlyAllowances() {
    const period = document.getElementById('eaPeriodSearch').value;
    const idCard = document.getElementById('eaIdCardSearch').value;
    const name = document.getElementById('eaNameSearch').value;
    let url = '/api/elderly_allowance?';
    if (period) url += `period=${period}&`;
    if (idCard) url += `id_card=${idCard}&`;
    if (name) url += `name=${encodeURIComponent(name)}&`;

    apiRequest('GET', url).then(data => {
        const tbody = document.getElementById('elderlyAllowanceBody');
        tbody.innerHTML = '';
        if (data.records) {
            data.records.forEach(p => {
                const row = document.createElement('tr');
                const deleteBtn = userRole === 'admin'
                    ? `<button onclick="deleteElderlyAllowance('${p.id}')" class="btn-delete" style="padding:4px 8px;font-size:12px;">删除</button>`
                    : '';
                row.innerHTML = `
                    <td>${p.period || ''}</td>
                    <td>${p.name || ''}</td>
                    <td>${p.id_card || ''}</td>
                    <td>${p.village || ''}</td>
                    <td style="font-size:11px;">${p.bank_account || ''}</td>
                    <td>${p.amount || ''}</td>
                    <td>${p.payment_status || ''}</td>
                    <td>${p.relation || ''}</td>
                    <td style="font-size:11px;max-width:120px;overflow:hidden;text-overflow:ellipsis;" title="${p.import_source || ''}">${p.import_source || ''}</td>
                    <td>${deleteBtn}</td>
                `;
                tbody.appendChild(row);
            });
        }
    });
}

function showElderlyAllowanceImportModal() {
    document.getElementById('elderlyAllowanceImportModal').style.display = 'flex';
    document.getElementById('eaImportFile').value = '';
    document.getElementById('eaImportProgress').style.display = 'none';
}

function closeElderlyAllowanceImportModal() {
    document.getElementById('elderlyAllowanceImportModal').style.display = 'none';
}

function doElderlyAllowanceImport() {
    const fileInput = document.getElementById('eaImportFile');
    if (!fileInput.files.length) { alert('请选择文件'); return; }

    const period = document.getElementById('eaImportPeriod').value.trim();
    if (!period) { alert('请输入费款所属期（如202606）'); return; }

    const formData = new FormData();
    formData.append('file', fileInput.files[0]);
    formData.append('period', period);

    document.getElementById('eaImportProgress').style.display = 'block';
    document.getElementById('eaImportStatus').textContent = '正在导入...';

    fetch('/api/elderly_allowance/import', {
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
            document.getElementById('eaImportStatus').textContent = msg;
            loadElderlyAllowances();
        } else {
            document.getElementById('eaImportStatus').textContent = '导入失败：' + (result.error || '未知错误');
        }
    }).catch(err => {
        document.getElementById('eaImportStatus').textContent = '导入失败：' + err.message;
    });
}

function deleteElderlyAllowance(id) {
    if (!confirm('确定要删除这条记录吗？')) return;
    fetch(`/api/dibao_payment/${id}`, {
        method: 'DELETE',
        headers: {'Authorization': `Bearer ${authToken}`}
    }).then(r => r.json()).then(result => {
        if (result.success) {
            loadElderlyAllowances();
        } else {
            alert(result.error || '删除失败');
        }
    }).catch(err => alert('删除失败：' + err.message));
}

function exportElderlyAllowances() {
    if (!authToken) { alert('请先登录'); return; }
    const period = document.getElementById('eaPeriodSearch').value;
    let url = '/api/elderly_allowance/export?';
    if (period) url += 'period=' + encodeURIComponent(period) + '&';

    fetch(url, {
        method: 'GET',
        headers: {'Authorization': 'Bearer ' + authToken}
    }).then(res => {
        if (!res.ok) return res.json().then(data => { throw new Error(data.error || '导出失败'); });
        return res.blob();
    }).then(blob => {
        const link = document.createElement('a');
        link.href = URL.createObjectURL(blob);
        link.download = '高龄补贴.xlsx';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(link.href);
    }).catch(err => alert('导出失败：' + err.message));
}
