function toggleDisabilityDetail() {
    const val = document.getElementById('editDisability').value;
    document.getElementById('disabilityDetail').style.display = val === '是' ? 'block' : 'none';
    if (val !== '是') {
        document.getElementById('editDisabilityType').value = '';
        document.getElementById('editDisLevel').value = '';
    }
}
