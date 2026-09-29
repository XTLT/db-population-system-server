let currentPersonId = null;
let currentHuHao = null;
let authToken = localStorage.getItem('token') || '';
let currentUser = null;
let userRole = '';
let currentPersonUpdatedAt = '';
let currentPersonLandArea = '';
let currentPersonLocalWelfareForest = '';
let currentPersonNationalWelfareForest = '';
let currentPersonCommercialForest = '';
let isDefaultUser = false;

function apiRequest(method, path, data = null) {
    const headers = {'Content-Type': 'application/json'};
    if (authToken) {
        headers['Authorization'] = `Bearer ${authToken}`;
    }
    const opts = {method, headers};
    if (data) opts.body = JSON.stringify(data);
    return fetch(path, opts).then(res => {
        if (res.status === 401) {
            showLogin();
            throw new Error('登录已过期');
        }
        return res.json().catch(() => null).then(data => {
            if (!res.ok) {
                throw new Error((data && data.error) || ('请求失败(' + res.status + ')'));
            }
            if (data === null) {
                return {error: '请求失败'};
            }
            return data;
        });
    });
}
