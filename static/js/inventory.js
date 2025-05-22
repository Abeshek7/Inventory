
const form = document.getElementById('inventory_capture_2');
const inputs = form.querySelectorAll('input');
const stars = form.querySelectorAll('.required');
let formsubmitted = 0;

// remove case field since it is not required for validation

const requiredFields = ['locn', 'sku', 'uom', 'qty'];

inputs.forEach((input, index) => {
    input.addEventListener('keydown', (event) => {
        if (event.key === 'Enter') {
            event.preventDefault();

            // If this is a required field
            if (requiredFields.includes(input.name) && input.value.trim() === "") {
              
                const starIndex = requiredFields.indexOf(input.name);
                stars[starIndex].classList.add('visible');
                input.focus();
            } else {
               
                if (requiredFields.includes(input.name)) {
                    const starIndex = requiredFields.indexOf(input.name);
                    stars[starIndex].classList.remove('visible');
                }

                // Check if it's the last field
                if (index === inputs.length - 1) {
                    // Validate all required fields
                    let allValid = true;
                    requiredFields.forEach((name, i) => {
                        const inputField = form.querySelector(`input[name="${name}"]`);
                        if (inputField.value.trim() === "") {
                            stars[i].classList.add('visible');
                            allValid = false;
                        }
                    });

                    if (!allValid) return;
                    
                    //formData -- js object that takes all input values from form and converts into key-value pair format.
                    const formData = new FormData(form);

                    //method that take iterable from formdata.entries and converts into js object
                    const formObject = Object.fromEntries(formData.entries());

                    fetch('/second_form', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(formObject)
                    })
                        .then(response => response.json())
                        .then(result => {
                            alert(result.message);
                            formsubmitted = 1;
                            form.reset();
                            stars.forEach(star => star.classList.remove('visible'));
                            inputs[0].focus();
                        })
                        .catch(error => {
                            console.error('Error:', error);
                        });
                } else {
                    inputs[index + 1].focus();
                }
            }
        }
    });

    // When I press enter key it will go back to the main page.
    input.addEventListener('input', () => {
        if (requiredFields.includes(input.name)) {
            const starIndex = requiredFields.indexOf(input.name);
            if (input.value.trim() !== "") {
                stars[starIndex].classList.remove('visible');
            }
        }
    });
});

// When I press enter key it will go back to the main page.
document.addEventListener('keydown', function (event) {
    if (event.key === 'Escape' && formsubmitted) {
        window.location.href = '/';
    }
});
