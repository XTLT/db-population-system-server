function loadDibaoPayments() {
    const period = document.getElementById('dibaoPeriodSearch').value;
    const idCard = document.getElementById('dibaoIdCardSearch').value;
    const name = document.getElementById('dibaoNameSearch').value;
    let url = '/api/dibao_payment?';
    if (period) url += `period=${period}&`;
    if (idCard) url += `id_card=${idCard}&`;
    if (name) url += `name=${encodeURIComponent(name)}&`;

    apiRequest('GET', url).then(data => {
        const tbody = document.getElementById('dibaoPaymentBody');
        tbody.innerHTML = '';
        if (data.records) {
            data.records.forEach(p => {
                const row = document.createElement('tr');
                const deleteBtn = userRole === 'admin'
                    ? `<button onclick="deleteDibaoPayment('${p.id}')" class="btn-delete" style="padding:4px 8px;font-size:12px;">删除</button>`
                    : '';
                row.innerHTML = `
                    <td>${p.period || ''}</td>
                    <td>${p.name || ''}</td>
                    <td>${p.id_card || ''}</td>
                    <td>${p.village || ''}</td>
                    <td>${p.gender || ''}</td>
                    <td>${p.relation || ''}</td>
                    <td>${p.family_members || ''}</td>
                    <td>${p.family_count || ''}</td>
                    <td>${p.amount || ''}</td>
                    <td>${p.base_amount || ''}</td>
                    <td>${p.special_amount || ''}</td>
                    <td>${p.adjust_amount || ''}</td>
                    <td>${p.special_situation || ''}</td>
                    <td>${p.special_subsidy || ''}</td>
                    <td>${p.start_time || ''}</td>
                    <td>${p.issue_month || ''}</td>
                    <td style="font-size:11px;max-width:120px;overflow:hidden;text-overflow:ellipsis;" title="${p.import_source || ''}">${p.import_source || ''}</td>
                    <td>${deleteBtn}</td>
                `;
                tbody.appendChild(row);
            });
        }
    });
}
