function doDownloadTemplate() {
    fetch('/api/template/excel', {
        headers: {'Authorization': `Bearer ${authToken}`}
    }).then(res => {
        if (res.status === 401) {
            showLogin();
            throw new Error('登录已过期，请重新登录');
        }
        if (!res.ok) {
            if (res.headers.get('content-type')?.includes('json')) {
                return res.json().then(d => { throw new Error(d.error || '下载失败'); });
            }
            throw new Error('下载失败');
        }
        return res.blob();
    }).then(blob => {
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = '人口信息导入模板.xlsx';
        a.click();
        URL.revokeObjectURL(url);
    }).catch(err => alert(err.message));
}
