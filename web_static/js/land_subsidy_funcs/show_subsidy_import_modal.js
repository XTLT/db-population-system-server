function showSubsidyImportModal() {
    document.getElementById('subsidyImportModal').style.display = 'flex';
    document.getElementById('subsidyImportYear').value = new Date().getFullYear();
    document.getElementById('subsidyImportFile').value = '';
    document.getElementById('subsidyImportProgress').style.display = 'none';
}
