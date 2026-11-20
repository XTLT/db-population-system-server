function checkAuth() {
    if (authToken) {
        apiRequest('GET', '/api/stats').then(() => {
            showMain();
        }).catch(() => {
            showLogin();
        });
    } else {
        showLogin();
    }
}
