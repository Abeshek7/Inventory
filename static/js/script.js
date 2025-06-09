
const form = document.getElementById('inventory_capture');
const input = document.getElementById('owner');
const Star = document.querySelector('.required')

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

        fetch('/capture_owner', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ owner: ownerinput })
        })
        .then(response => response.json())
        .then(data => {
            if (data.redirect) {
                window.location.href = data.redirect;  
            }
        })
        .catch(error => console.error('Error:', error));
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