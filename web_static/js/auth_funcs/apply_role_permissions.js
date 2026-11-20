function applyRolePermissions() {
    const canEdit = userRole === 'admin' || userRole === 'user';
    const canDelete = userRole === 'admin';
    document.getElementById('btnEdit').style.display = canEdit ? '' : 'none';
    document.getElementById('btnMigrate').style.display = canEdit ? '' : 'none';
    document.getElementById('btnDelete').style.display = canDelete ? '' : 'none';
    document.getElementById('btnUserManage').style.display = canDelete ? '' : 'none';
    document.getElementById('btnImport').style.display = canDelete ? '' : 'none';
    document.getElementById('btnExport').style.display = canDelete ? '' : 'none';
    document.getElementById('btnTemplate').style.display = canEdit ? '' : 'none';
    document.getElementById('btnDeleted').style.display = canDelete ? '' : 'none';
    document.getElementById('btnBackup').style.display = canDelete ? '' : 'none';
    document.getElementById('btnLogs').style.display = canDelete ? '' : 'none';
    document.getElementById('btnStuImport').style.display = canDelete ? '' : 'none';
    document.getElementById('btnStuExport').style.display = canDelete ? '' : 'none';
    document.getElementById('btnAddHousehold').style.display = canEdit ? '' : 'none';
    document.getElementById('btnSplitHousehold').style.display = canEdit ? '' : 'none';
    document.getElementById('btnMergeHousehold').style.display = canEdit ? '' : 'none';
    document.getElementById('btnAddPerson').style.display = canEdit ? '' : 'none';
    document.getElementById('btnLandSubsidy').style.display = canEdit ? '' : 'none';
    document.getElementById('btnSubsidyImport').style.display = canDelete ? '' : 'none';
}
