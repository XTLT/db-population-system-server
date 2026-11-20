function migratePerson() {
    if (!currentPersonId) return;
    document.getElementById('migrateId').value = currentPersonId;
    document.getElementById('migrateDate').value = new Date().toISOString().split('T')[0];
    document.getElementById('migrateModal').style.display = 'flex';
}
