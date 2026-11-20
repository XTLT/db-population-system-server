function toggleTekunDetail() {
    const val = document.getElementById('editTekun').value;
    document.getElementById('tekunDetail').style.display = val === '是' ? 'block' : 'none';
    if (val !== '是') {
        document.getElementById('editTekunType').value = '';
    }
}
