function loadSubsidyYears() {
    apiRequest('GET', '/api/land_subsidy/years').then(data => {
        const select = document.getElementById('subsidyYear');
        select.innerHTML = '<option value="">全部年度</option>';
        if (data.years) {
            data.years.forEach(year => {
                select.innerHTML += `<option value="${year}">${year}</option>`;
            });
        }
    });
}
