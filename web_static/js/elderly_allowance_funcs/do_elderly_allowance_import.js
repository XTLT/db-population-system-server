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
