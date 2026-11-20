function recoverPerson(deletedId, name) {
    if (!confirm(`确定要找回 ${name} 吗？`)) return;
    apiRequest('POST', `/api/recover/${deletedId}`).then(result => {
        if (result.success) {
            alert('找回成功！');
            loadDeleted();
        } else {
            alert('找回失败：' + (result.error || '未知错误'));
        }
    }).catch(err => {
        alert('找回失败：' + ((err && err.message) || '网络错误'));
    });
}
