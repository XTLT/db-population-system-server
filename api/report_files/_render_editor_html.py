from flask import render_template_string


def _render_editor_html(report_id: str, report_name: str, token: str) -> str:
    """渲染在线编辑器 HTML 页面"""
    return render_template_string(EDITOR_HTML_TEMPLATE,
                                  report_id=report_id,
                                  report_name=report_name,
                                  token=token)


EDITOR_HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>在线编辑 - {{ report_name }}</title>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: "Microsoft YaHei", sans-serif; background: #f5f5f5; }
.header { background: #4472C4; color: white; padding: 12px 20px; display: flex; justify-content: space-between; align-items: center; }
.header h1 { font-size: 18px; }
.toolbar { padding: 10px 20px; background: white; border-bottom: 1px solid #ddd; display: flex; gap: 10px; }
.btn { padding: 6px 16px; border: none; border-radius: 4px; cursor: pointer; font-size: 14px; }
.btn-save { background: #4472C4; color: white; }
.btn-save:hover { background: #3656b8; }
.btn-cancel { background: #e0e0e0; }
.btn-cancel:hover { background: #d0d0d0; }
.table-container { overflow: auto; max-height: calc(100vh - 120px); padding: 10px; }
table { border-collapse: collapse; background: white; }
th, td { border: 1px solid #ccc; padding: 4px 8px; min-width: 80px; max-width: 300px; }
th { background: #4472C4; color: white; position: sticky; top: 0; font-weight: bold; }
td { white-space: pre-wrap; word-break: break-all; }
td[contenteditable="true"]:focus { background: #e6f2ff; outline: 2px solid #4472C4; }
.status { padding: 8px 20px; font-size: 13px; color: #666; }
.status .success { color: #4CAF50; }
.status .error { color: #f44336; }
.loading { text-align: center; padding: 40px; font-size: 16px; color: #999; }
</style>
</head>
<body>
<div class="header">
  <h1>📋 {{ report_name }}</h1>
</div>
<div class="toolbar">
  <button class="btn btn-save" onclick="saveData()">💾 保存</button>
  <button class="btn btn-cancel" onclick="window.close()">关闭</button>
  <span id="status" class="status"></span>
</div>
<div id="content" class="table-container">
  <div class="loading">正在加载报表数据...</div>
</div>
<script>
const REPORT_ID = '{{ report_id }}';
const TOKEN = '{{ token }}';

function showStatus(msg, type) {
  const el = document.getElementById('status');
  el.innerHTML = '<span class="' + (type||'') + '">' + msg + '</span>';
}

async function loadData() {
  try {
    const resp = await fetch('/api/reports/' + REPORT_ID + '/data?token=' + TOKEN);
    if (!resp.ok) {
      const err = await resp.json().catch(() => ({error: 'HTTP ' + resp.status}));
      throw new Error(err.error || '加载失败');
    }
    const data = await resp.json();
    renderTable(data.headers, data.rows);
    showStatus('已加载 ' + data.rows.length + ' 行数据', 'success');
  } catch(e) {
    document.getElementById('content').innerHTML = '<div class="loading" style="color:#f44336;">加载失败: ' + e.message + '</div>';
  }
}

function renderTable(headers, rows) {
  let html = '<table><thead><tr>';
  headers.forEach(h => { html += '<th>' + escapeHtml(h) + '</th>'; });
  html += '</tr></thead><tbody>';
  rows.forEach((row, ri) => {
    html += '<tr>';
    headers.forEach((h, ci) => {
      const val = row[ci] !== undefined ? escapeHtml(row[ci]) : '';
      html += '<td contenteditable="true" data-row="' + ri + '" data-col="' + ci + '">' + val + '</td>';
    });
    html += '</tr>';
  });
  html += '</tbody></table>';
  document.getElementById('content').innerHTML = html;
}

function escapeHtml(s) {
  if (s === null || s === undefined) return '';
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

async function saveData() {
  const table = document.querySelector('table');
  if (!table) return;

  const headers = [];
  table.querySelectorAll('thead th').forEach(th => {
    headers.push(th.textContent);
  });

  const rows = [];
  table.querySelectorAll('tbody tr').forEach(tr => {
    const row = [];
    tr.querySelectorAll('td').forEach(td => {
      row.push(td.textContent);
    });
    rows.push(row);
  });

  showStatus('正在保存...', '');

  try {
    const resp = await fetch('/api/reports/' + REPORT_ID + '/save?token=' + TOKEN, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({headers: headers, rows: rows})
    });
    if (!resp.ok) {
      const err = await resp.json().catch(() => ({error: 'HTTP ' + resp.status}));
      throw new Error(err.error || '保存失败');
    }
    showStatus('保存成功 (' + rows.length + ' 行)', 'success');
  } catch(e) {
    showStatus('保存失败: ' + e.message, 'error');
  }
}

loadData();
</script>
</body>
</html>
'''
