function doSplitHousehold() {
    const ids = [...document.querySelectorAll('.split-check:checked')].map(c => c.value);
    if (ids.length === 0) { alert('请选择要分户的人员'); return; }
    if (!confirm(`确定将 ${ids.length} 人分出为新户？`)) return;
    fetch('/api/household/split', {
        method: 'POST',
        headers: {'Content-Type': 'application/json', 'Authorization': `Bearer ${authToken}`},
        body: JSON.stringify({person_ids: ids})
    }).then(r => r.json()).then(result => {
        if (result.success) {
            closeSplitHouseholdModal();
            alert(`分户成功！新户号：${result.new_hu_hao}`);
            doSearch();
        } else {
            alert(result.error || '分户失败');
        }
    }).catch(err => alert('分户失败：' + err.message));
}
