document.getElementById('download_excel_btn').addEventListener('click', function () {
    const messageDiv = document.getElementById('download-message');
    messageDiv.textContent = ''; // Clear any previous message
    messageDiv.style.display = 'none';
    messageDiv.classList.remove('error', 'success');

    fetch('/download_excel', {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json', // specify content type
        }
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(data => {
                throw new Error(data.error || "Unexpected error");
            });
        }
        return response.blob();
    })
    .then(blob => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'inventory_export.xlsx';
        document.body.appendChild(a);
        a.click();
        a.remove();
        window.URL.revokeObjectURL(url);
    })
    .catch(error => {
        messageDiv.textContent = error.message;
        messageDiv.style.display = 'block';
        messageDiv.classList.remove('success');
        messageDiv.classList.add('error');

        setTimeout(() => {
            messageDiv.textContent = '';
            messageDiv.style.display = 'none';
            messageDiv.classList.remove('error');
        }, 3000);
    });
});
document.getElementById('Inventory-btn').addEventListener('click', function() {
    window.location.href = '{{ url_for("firstpage") }}';
});
