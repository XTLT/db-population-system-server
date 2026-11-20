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
