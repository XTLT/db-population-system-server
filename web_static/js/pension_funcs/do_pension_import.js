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
