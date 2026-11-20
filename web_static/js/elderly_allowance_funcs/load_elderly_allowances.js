function loadElderlyAllowances() {
    const period = document.getElementById('eaPeriodSearch').value;
    const idCard = document.getElementById('eaIdCardSearch').value;
    const name = document.getElementById('eaNameSearch').value;
    let url = '/api/elderly_allowance?';
    if (period) url += `period=${period}&`;
    if (idCard) url += `id_card=${idCard}&`;
    if (name) url += `name=${encodeURIComponent(name)}&`;

    apiRequest('GET', url).then(data => {
        const tbody = document.getElementById('elderlyAllowanceBody');
        tbody.innerHTML = '';
        if (data.records) {
            data.records.forEach(p => {
                const row = document.createElement('tr');
                const deleteBtn = userRole === 'admin'
                    ? `<button onclick="deleteElderlyAllowance('${p.id}')" class="btn-delete" style="padding:4px 8px;font-size:12px;">删除</button>`
                    : '';
                row.innerHTML = `
                    <td>${p.period || ''}</td>
                    <td>${p.name || ''}</td>
                    <td>${p.id_card || ''}</td>
                    <td>${p.village || ''}</td>
                    <td style="font-size:11px;">${p.bank_account || ''}</td>
                    <td>${p.amount || ''}</td>
                    <td>${p.payment_status || ''}</td>
                    <td>${p.relation || ''}</td>
                    <td style="font-size:11px;max-width:120px;overflow:hidden;text-overflow:ellipsis;" title="${p.import_source || ''}">${p.import_source || ''}</td>
                    <td>${deleteBtn}</td>
                `;
                tbody.appendChild(row);
            });
        }
    });
}
