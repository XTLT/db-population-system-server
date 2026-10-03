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
            data.subsidies.forEach((s, i) => {
                const row = document.createElement('tr');
                const deleteBtn = userRole === 'admin'
                    ? `<button onclick="deleteLandSubsidy('${s.id}')" class="btn-delete" style="padding:4px 8px;font-size:12px;">删除</button>`
                    : '';
                row.innerHTML = `
                    <td>${i + 1}</td>
                    <td>${s.year || ''}</td>
                    <td>${s.name || ''}</td>
                    <td>${s.id_card || ''}</td>
                    <td>${s.phone || ''}</td>
                    <td></td>
                    <td>${s.bank_name || ''}</td>
                    <td>${s.total_amount || ''}</td>
                    <td>${s.land_time || ''}</td>
                    <td>${s.certified_area || ''}</td>
                    <td>${s.base_standard || ''}</td>
                    <td>${s.rape_area || ''}</td>
                    <td></td>
                    <td>${s.rape_amount || ''}</td>
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
