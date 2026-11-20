function deleteDibaoPayment(id) {
    if (!confirm('确定要删除这条记录吗？')) return;
    fetch(`/api/dibao_payment/${id}`, {
        method: 'DELETE',
        headers: {'Authorization': `Bearer ${authToken}`}
    }).then(r => r.json()).then(result => {
        if (result.success) {
            loadDibaoPayments();
        } else {
            alert(result.error || '删除失败');
        }
    }).catch(err => alert('删除失败：' + err.message));
}
