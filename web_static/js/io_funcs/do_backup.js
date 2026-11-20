function doBackup() {
    if (!confirm('确定要备份数据库吗？')) return;
    // 服务器端备份需复制数据库 + 压缩全部照片 + 加密，耗时较长：
    // 确认后立即禁用按钮并显示“正在备份...”，避免“点击后干等、完成才弹提示”，同时防止重复提交。
    const btn = document.getElementById('btnBackup');
    const oldText = btn.textContent;
    btn.disabled = true;
    btn.textContent = '正在备份...';
    apiRequest('POST', '/api/backup').then(result => {
        if (result.success) {
            alert('备份成功！');
        } else {
            alert('备份失败：' + (result.error || '未知错误'));
        }
    }).catch(err => {
        alert('备份失败：' + ((err && err.message) || '网络错误'));
    }).finally(() => {
        btn.disabled = false;
        btn.textContent = oldText;
    });
}
