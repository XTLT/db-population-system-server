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
