function doMergeHousehold() {
    const target = document.getElementById('mergeTargetHuHao').value.trim();
    const ids = [...document.querySelectorAll('.merge-check:checked')].map(c => c.value);
    if (!target) { alert('请输入目标户号'); return; }
    if (ids.length === 0) { alert('请选择要合并的人员'); return; }
    if (!confirm(`确定将 ${ids.length} 人合并到户号 ${target}？`)) return;
    fetch('/api/household/merge', {
        method: 'POST',
        headers: {'Content-Type': 'application/json', 'Authorization': `Bearer ${authToken}`},
        body: JSON.stringify({target_hu_hao: target, person_ids: ids})
    }).then(r => r.json()).then(result => {
        if (result.success) {
            closeMergeHouseholdModal();
            alert('合户成功！');
            doSearch();
        } else {
            alert(result.error || '合户失败');
        }
    }).catch(err => alert('合户失败：' + err.message));
}
