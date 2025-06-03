
const form = document.getElementById('inventory_capture_2');
const inputs = form.querySelectorAll('input');
const stars = form.querySelectorAll('.required');
let formsubmitted = 0;

const formMessageDiv = document.getElementById('form-message');

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
                            // Success: show success message
                            formMessageDiv.textContent = result.message || 'Data submitted successfully!';
                            formMessageDiv.classList.remove('error');
                            formMessageDiv.classList.add('success');
                            formMessageDiv.style.display = 'block';

                            // Clear after 5 seconds
                            setTimeout(() => {
                                formMessageDiv.textContent = '';
                                formMessageDiv.style.display = 'none';
                                formMessageDiv.classList.remove('success');
                            }, 5000);

                            // Reset form and clear stars
                            form.reset();
                            stars.forEach(star => star.classList.remove('visible'));
                            inputs[0].focus();
                        })
                        .catch(error => {
                            
                            formMessageDiv.textContent = error.message || 'Error submitting data.';
                            formMessageDiv.classList.remove('success');
                            formMessageDiv.classList.add('error');
                            formMessageDiv.style.display = 'block';

                            setTimeout(() => {
                                formMessageDiv.textContent = '';
                                formMessageDiv.style.display = 'none';
                                formMessageDiv.classList.remove('error');
                            }, 5000);
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

// When I press esc key it will go back to the main page.
document.addEventListener('keydown', function (event) {
    if (event.key === 'Escape' && formsubmitted) {
        window.location.href = '/';
    }
});

// --- Excel Download with UI Message ---
document.getElementById('download_excel_btn').addEventListener('click', function () {
    const messageDiv = document.getElementById('download-message');
    messageDiv.textContent = ''; // Clear any previous message
    messageDiv.style.display = 'none';
    messageDiv.classList.remove('error', 'success');

    fetch('/download_excel')
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
            }, 5000);
        });
});