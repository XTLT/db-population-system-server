function loadLandSubsidies() {
    const year = document.getElementById('subsidyYear').value;
    const search = document.getElementById('subsidySearch').value;
    let url = '/api/land_subsidy?';
    if (year) url += `year=${year}&`;
    if (search) url += `search=${search}`;

    apiRequest('GET', url).then(data => {
        const tbody = document.getElementById('landSubsidyBody');
        tbody.innerHTML = '';
        if (data.subsidies) {
            data.subsidies.forEach((s, i) => {
                const row = document.createElement('tr');
                const deleteBtn = userRole === 'admin'
                    ? `<button onclick="deleteLandSubsidy('${s.id}')" class="btn-delete" style="padding:4px 8px;font-size:12px;">删除</button>`
                    : '';
                row.innerHTML = `
                    <td>${i + 1}</td>
                    <td>${s.year || ''}</td>
                    <td>${s.name || ''}</td>
                    <td>${s.id_card || ''}</td>
                    <td>${s.phone || ''}</td>
                    <td>${s.bank_account || ''}</td>
                    <td>${s.bank_name || ''}</td>
                    <td>${s.total_amount || ''}</td>
                    <td>${s.land_time || ''}</td>
                    <td>${s.certified_area || ''}</td>
                    <td>${s.base_standard || ''}</td>
                    <td>${s.rape_area || ''}</td>
                    <td>${s.rape_standard || ''}</td>
                    <td>${s.rape_amount || ''}</td>
                    <td>${deleteBtn}</td>
                `;
                tbody.appendChild(row);
            });
        }
    });
}
