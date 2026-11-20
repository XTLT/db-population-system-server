function showAddHouseholdModal() {
    fetch('/api/household/new_number', {
        headers: {'Authorization': `Bearer ${authToken}`}
    }).then(r => r.json()).then(data => {
        document.getElementById('newHhHuhao').value = data.hu_hao || '';
    });
    document.getElementById('newHhName').value = '';
    document.getElementById('newHhIdCard').value = '';
    document.getElementById('newHhAddress').value = '';
    document.getElementById('newHhPhone').value = '';
    document.getElementById('newHhLandArea').value = '';
    document.getElementById('newHhLocalWelfareForest').value = '';
    document.getElementById('newHhNationalWelfareForest').value = '';
    document.getElementById('newHhCommercialForest').value = '';
    document.getElementById('addHouseholdModal').style.display = 'flex';
}
