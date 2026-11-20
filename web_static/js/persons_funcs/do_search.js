function doSearch() {
    const name = document.getElementById('searchInput').value.trim();
    if (!name) return;
    apiRequest('GET', `/api/search?name=${encodeURIComponent(name)}`)
        .then(data => displayNames(data.results || data));
}
