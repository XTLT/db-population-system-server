function exportDisabilityCarePayments() {
    if (!authToken) { alert('请先登录'); return; }
    const period = document.getElementById('dcpPeriodSearch').value;
    let url = '/api/disability_care_payment/export?';
    if (period) url += 'period=' + encodeURIComponent(period) + '&';

    fetch(url, {
        method: 'GET',
        headers: {'Authorization': 'Bearer ' + authToken}
    }).then(res => {
        if (!res.ok) return res.json().then(data => { throw new Error(data.error || '导出失败'); });
        return res.blob();
    }).then(blob => {
        const link = document.createElement('a');
        link.href = URL.createObjectURL(blob);
        link.download = '残疾人护理补贴.xlsx';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(link.href);
    }).catch(err => alert('导出失败：' + err.message));
}
