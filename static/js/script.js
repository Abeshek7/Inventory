const form = document.getElementById('inventory_capture');
const input = document.getElementById('owner');
const Star = document.querySelector('.required');

// Get CSRF token with fallback
function getCSRFToken() {
    const metaToken = document.querySelector('meta[name="csrf-token"]');
    if (metaToken) {
        return metaToken.getAttribute('content');
    }
    // Fallback: try to get from hidden input if meta tag not available
    const hiddenInput = document.querySelector('input[name="csrf_token"]');
    return hiddenInput ? hiddenInput.value : null;
}

const csrfToken = getCSRFToken();

// Show error message function
function showError(message) {
    // You can customize this based on your UI
    alert(message); // Simple alert, replace with your preferred error display method
}

form.addEventListener('keydown', function(event) {
    if (event.key === 'Enter') {
        event.preventDefault();

        const ownerinput = input.value.trim();

        // If the field is empty it will show the asterisk
        if (ownerinput === "") {
            Star.classList.add('visible');
            input.focus();
            return;
        }

        // Validate CSRF token exists
        if (!csrfToken) {
            showError('Security token missing. Please refresh the page and try again.');
            return;
        }

        fetch('/capture_owner', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({ owner: ownerinput })
        })
        .then(response => {
            if (!response.ok) {
                // Handle HTTP errors
                if (response.status === 400) {
                    throw new Error('Invalid request. Please check your input.');
                } else if (response.status === 403) {
                    throw new Error('Security validation failed. Please refresh the page.');
                } else {
                    throw new Error(`Server error: ${response.status}`);
                }
            }
            return response.json();
        })
        .then(data => {
            if (data.error) {
                showError(data.error);
            } else if (data.redirect) {
                window.location.href = data.redirect;
            } else {
                showError('Unexpected response from server.');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showError(error.message || 'An error occurred. Please try again.');
        });
    }
});

input.addEventListener('input', function() {
    if (input.value.trim() !== "") {
        Star.classList.remove('visible'); // Hide the star when the user starts typing
    }
});

// When I press esc key it will go back to the main page.
document.addEventListener('keydown', function (event) {
    if (event.key === 'Escape') {
        window.location.href = '/';
    }
});