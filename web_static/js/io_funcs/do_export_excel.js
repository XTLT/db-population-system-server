function doExportExcel() {
    const doFetch = (password) => {
        return fetch('/api/export/excel', {
            method: 'POST',
            headers: {'Authorization': `Bearer ${authToken}`, 'Content-Type': 'application/json'},
            body: JSON.stringify(password ? {password: password} : {})
        });
    };
    doFetch('').then(res => {
        if (res.status === 401) {
            const password = prompt('导出敏感数据需要验证密码：');
            if (password === null || password === '') throw new Error('已取消导出');
            return doFetch(password);
        }
        return res;
    }).then(res => {
        if (!res.ok) return res.json().then(d => { throw new Error(d.error || '导出失败'); });
        return res.blob();
    }).then(blob => {
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `人口信息_${new Date().toISOString().slice(0,10).replace(/-/g,'')}.xlsx`;
        a.click();
        URL.revokeObjectURL(url);
    }).catch(err => alert('导出失败：' + err.message));
}
