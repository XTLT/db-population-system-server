function deletePerson() {
    if (!currentPersonId) return;
    if (!confirm('确定要删除该人员吗？删除后可在找回功能中恢复。')) return;
    if (!confirm('请再次确认：是否删除该人员？')) return;

    apiRequest('DELETE', `/api/person/${currentPersonId}`)
        .then(result => {
            if (result.success) {
                alert('人员已删除！');
                document.getElementById('personDetail').style.display = 'none';
                showFamily(currentHuHao, '');
            }
        });
}
