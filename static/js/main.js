document.getElementById('download_excel_btn').addEventListener('click', function () {
    const messageDiv = document.getElementById('download-message');
    messageDiv.textContent = '';
    messageDiv.style.display = 'none';
    messageDiv.classList.remove('error', 'success');

    fetch('/download_excel', {
        method: 'GET'
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(data => {
                throw new Error(data.error || "Unexpected error");
            });
        }

        const disposition = response.headers.get('Content-Disposition');
        let filename = 'inventory_export.xlsx';  // fallback filename

        if (disposition && disposition.includes('filename=')) {
            const match = disposition.match(/filename="?([^"]+)"?/);
            if (match && match[1]) {
                filename = match[1];
            }
        }

        return response.blob().then(blob => ({ blob, filename }));
    })
    .then(({ blob, filename }) => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
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

document.getElementById('Inventory-btn').addEventListener('click', function () {
    window.location.href = '{{ url_for("firstpage") }}';
});
