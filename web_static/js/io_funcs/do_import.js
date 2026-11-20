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
            document.getElementById('importDetail').style.display = 'none';
        } else {
            let msg = `导入完成！成功：${result.imported}条`;
            if (result.updated) msg += `，更新：${result.updated}条`;
            msg += `，跳过：${result.skipped}条`;
            document.getElementById('importStatus').textContent = msg;
            const detailEl = document.getElementById('importDetail');
            if (result.errors && result.errors.length > 0) {
                detailEl.textContent = '跳过明细：\n' + result.errors.join('\n');
                detailEl.style.display = 'block';
            } else {
                detailEl.style.display = 'none';
            }
        }
    }).catch(err => {
        document.getElementById('importStatus').textContent = '导入失败：' + err.message;
    });
}
