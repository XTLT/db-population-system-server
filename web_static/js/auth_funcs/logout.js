function logout() {
    apiRequest('POST', '/api/logout').catch(() => {});
    authToken = '';
    currentUser = null;
    userRole = '';
    isDefaultUser = false;
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    localStorage.removeItem('isDefaultUser');
    showLogin();
}
