function showLogsModal() {
    document.getElementById('logsModal').style.display = 'flex';
    loadLogs();
}

function closeLogsModal() {
    document.getElementById('logsModal').style.display = 'none';
}

function loadLogs() {
    apiRequest('GET', '/api/logs?limit=200').then(logs => {
        const tbody = document.getElementById('logsBody');
        tbody.innerHTML = '';
        if (logs.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" style="color:#999;">暂无日志</td></tr>';
            return;
        }
        logs.forEach(l => {
            const tr = document.createElement('tr');
            if (l.is_high_risk === '是') tr.style.backgroundColor = '#fff0f0';
            tr.innerHTML = `
                <td>${l.created_at}</td>
                <td>${l.username}</td>
                <td>${l.operation_type}</td>
                <td>${l.operation_target || ''}</td>
                <td>${l.ip_address}</td>
                <td>${l.client_type}</td>
                <td>${l.is_high_risk === '是' ? '⚠️' : ''}</td>
            `;
            tbody.appendChild(tr);
        });
    });
}
