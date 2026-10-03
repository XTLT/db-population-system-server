// 低保发放相关函数
function showDibaoPaymentModal() {
    document.getElementById('dibaoPaymentModal').style.display = 'flex';
    loadDibaoPayments();
}

function closeDibaoPaymentModal() {
    document.getElementById('dibaoPaymentModal').style.display = 'none';
}

function loadDibaoPayments() {
    const period = document.getElementById('dibaoPeriodSearch').value;
    const idCard = document.getElementById('dibaoIdCardSearch').value;
    const name = document.getElementById('dibaoNameSearch').value;
    let url = '/api/dibao_payment?';
    if (period) url += `period=${period}&`;
    if (idCard) url += `id_card=${idCard}&`;
    if (name) url += `name=${encodeURIComponent(name)}&`;

    apiRequest('GET', url).then(data => {
        const tbody = document.getElementById('dibaoPaymentBody');
        tbody.innerHTML = '';
        if (data.records) {
            data.records.forEach(p => {
                const row = document.createElement('tr');
                const deleteBtn = userRole === 'admin'
                    ? `<button onclick="deleteDibaoPayment('${p.id}')" class="btn-delete" style="padding:4px 8px;font-size:12px;">删除</button>`
                    : '';
                row.innerHTML = `
                    <td>${p.period || ''}</td>
                    <td>${p.name || ''}</td>
                    <td>${p.id_card || ''}</td>
                    <td>${p.village || ''}</td>
                    <td>${p.gender || ''}</td>
                    <td>${p.relation || ''}</td>
                    <td>${p.family_members || ''}</td>
                    <td>${p.family_count || ''}</td>
                    <td>${p.amount || ''}</td>
                    <td>${p.base_amount || ''}</td>
                    <td>${p.special_amount || ''}</td>
                    <td>${p.adjust_amount || ''}</td>
                    <td>${p.special_situation || ''}</td>
                    <td>${p.special_subsidy || ''}</td>
                    <td>${p.start_time || ''}</td>
                    <td>${p.issue_month || ''}</td>
                    <td style="font-size:11px;max-width:120px;overflow:hidden;text-overflow:ellipsis;" title="${p.import_source || ''}">${p.import_source || ''}</td>
                    <td>${deleteBtn}</td>
                `;
                tbody.appendChild(row);
            });
        }
    });
}

function showDibaoImportModal() {
    document.getElementById('dibaoImportModal').style.display = 'flex';
    document.getElementById('dibaoImportFile').value = '';
    document.getElementById('dibaoImportProgress').style.display = 'none';
}

function closeDibaoImportModal() {
    document.getElementById('dibaoImportModal').style.display = 'none';
}

function doDibaoImport() {
    const fileInput = document.getElementById('dibaoImportFile');
    if (!fileInput.files.length) { alert('请选择文件'); return; }

    const period = document.getElementById('dibaoImportPeriod').value.trim();
    if (!period) { alert('请输入费款所属期（如202606）'); return; }

    const formData = new FormData();
    formData.append('file', fileInput.files[0]);
    formData.append('period', period);

    document.getElementById('dibaoImportProgress').style.display = 'block';
    document.getElementById('dibaoImportStatus').textContent = '正在导入...';

    fetch('/api/dibao_payment/import', {
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
            document.getElementById('dibaoImportStatus').textContent = msg;
            loadDibaoPayments();
        } else {
            document.getElementById('dibaoImportStatus').textContent = '导入失败：' + (result.error || '未知错误');
        }
    }).catch(err => {
        document.getElementById('dibaoImportStatus').textContent = '导入失败：' + err.message;
    });
}

function deleteDibaoPayment(id) {
    if (!confirm('确定要删除这条记录吗？')) return;
    fetch(`/api/dibao_payment/${id}`, {
        method: 'DELETE',
        headers: {'Authorization': `Bearer ${authToken}`}
    }).then(r => r.json()).then(result => {
        if (result.success) {
            loadDibaoPayments();
        } else {
            alert(result.error || '删除失败');
        }
    }).catch(err => alert('删除失败：' + err.message));
}

function exportDibaoPayments() {
    if (!authToken) { alert('请先登录'); return; }
    const period = document.getElementById('dibaoPeriodSearch').value;
    let url = '/api/dibao_payment/export?';
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
        link.download = '低保发放.xlsx';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(link.href);
    }).catch(err => alert('导出失败：' + err.message));
}
