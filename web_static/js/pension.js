// 养老保险相关函数
function showPensionInsuranceModal() {
    document.getElementById('pensionInsuranceModal').style.display = 'flex';
    loadPensionInsurance();
}

function closePensionInsuranceModal() {
    document.getElementById('pensionInsuranceModal').style.display = 'none';
}

function loadPensionInsurance() {
    const period = document.getElementById('pensionPeriodSearch').value;
    const idCard = document.getElementById('pensionIdCardSearch').value;
    let url = '/api/pension_insurance?';
    if (period) url += `period=${period}&`;
    if (idCard) url += `id_card=${idCard}&`;

    apiRequest('GET', url).then(data => {
        const tbody = document.getElementById('pensionInsuranceBody');
        tbody.innerHTML = '';
        if (data.records) {
            data.records.forEach(p => {
                const row = document.createElement('tr');
                const deleteBtn = userRole === 'admin'
                    ? `<button onclick="deletePensionInsurance('${p.id}')" class="btn-delete" style="padding:4px 8px;font-size:12px;">删除</button>`
                    : '';
                row.innerHTML = `
                    <td>${p.period || ''}</td>
                    <td>${p.name || ''}</td>
                    <td>${p.id_card || ''}</td>
                    <td>${p.village || ''}</td>
                    <td style="font-size:11px;">${p.bank_account || ''}</td>
                    <td>${p.amount || ''}</td>
                    <td>${p.payment_status || ''}</td>
                    <td style="font-size:11px;max-width:120px;overflow:hidden;text-overflow:ellipsis;" title="${p.import_source || ''}">${p.import_source || ''}</td>
                    <td>${deleteBtn}</td>
                `;
                tbody.appendChild(row);
            });
        }
    });
}

function showPensionImportModal() {
    document.getElementById('pensionImportModal').style.display = 'flex';
    document.getElementById('pensionImportFile').value = '';
    document.getElementById('pensionImportProgress').style.display = 'none';
}

function closePensionImportModal() {
    document.getElementById('pensionImportModal').style.display = 'none';
}

function doPensionImport() {
    const fileInput = document.getElementById('pensionImportFile');
    const periodInput = document.getElementById('pensionImportPeriod');
    if (!fileInput.files.length) { alert('请选择文件'); return; }
    if (!periodInput.value.trim()) { alert('请输入费款所属期'); return; }

    const formData = new FormData();
    formData.append('file', fileInput.files[0]);
    formData.append('period', periodInput.value.trim());

    document.getElementById('pensionImportProgress').style.display = 'block';
    document.getElementById('pensionImportStatus').textContent = '正在导入...';

    fetch('/api/pension_insurance/import', {
        method: 'POST',
        headers: {'Authorization': `Bearer ${authToken}`},
        body: formData
    }).then(r => r.json()).then(result => {
        if (result.imported !== undefined) {
            let msg = `导入完成！\n成功：${result.imported}条\n跳过：${result.skipped}条`;
            if (result.errors && result.errors.length > 0) {
                msg += `\n错误：${result.errors.length}条\n` + result.errors.slice(0, 5).join('\n');
            }
            document.getElementById('pensionImportStatus').textContent = msg;
            loadPensionInsurance();
        } else {
            document.getElementById('pensionImportStatus').textContent = '导入失败：' + (result.error || '未知错误');
        }
    }).catch(err => {
        document.getElementById('pensionImportStatus').textContent = '导入失败：' + err.message;
    });
}

function deletePensionInsurance(id) {
    if (!confirm('确定要删除这条记录吗？')) return;
    fetch(`/api/pension_insurance/${id}`, {
        method: 'DELETE',
        headers: {'Authorization': `Bearer ${authToken}`}
    }).then(r => r.json()).then(result => {
        if (result.success) {
            loadPensionInsurance();
        } else {
            alert(result.error || '删除失败');
        }
    }).catch(err => alert('删除失败：' + err.message));
}

function exportPensionInsurance() {
    if (!authToken) {
        alert('请先登录');
        return;
    }
    const period = document.getElementById('pensionPeriodSearch').value;
    let url = '/api/pension_insurance/export?';
    if (period) url += 'period=' + encodeURIComponent(period) + '&';

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
        link.download = '养老保险.xlsx';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(link.href);
    }).catch(err => alert('导出失败：' + err.message));
}
