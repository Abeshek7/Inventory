const form = document.getElementById('inventory_capture_2');
const inputs = form.querySelectorAll('input');
const stars = form.querySelectorAll('.required');
const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
let formsubmitted = 0;

const formMessageDiv = document.getElementById('form-message');

// Required and optional fields
const requiredFields = ['locn', 'sku', 'uom', 'qty'];
const optionalFields = ['lpn'];

// Validation regex patterns
const patterns = {
    alphanumeric: /^[a-zA-Z0-9-]{1,50}$/,         // locn, sku, lpn (optional)
    lettersOnly: /^[a-zA-Z]{1,50}$/,             // uom
    positiveInteger: /^[1-9]\d{0,49}$/,          // qty: positive integer (no leading zeros)
};

// Validation error messages
const validationMessages = {
    'locn': 'Location must contain only letters, numbers, and hyphens (max 50 characters)',
    'sku': 'SKU must contain only letters, numbers, and hyphens (max 50 characters)',
    'uom': 'Unit of Measure must contain only letters (max 50 characters)',
    'qty': 'Quantity must be a positive whole number (no letters, decimals, or leading zeros)',
    'lpn': 'LPN must contain only letters, numbers, and hyphens (max 50 characters)'
};

// Show validation message
function showValidationMessage(message, isError = true) {
    formMessageDiv.textContent = message;
    formMessageDiv.classList.remove(isError ? 'success' : 'error');
    formMessageDiv.classList.add(isError ? 'error' : 'success');
    formMessageDiv.style.display = 'block';
    
    // Clear message after 4 seconds
    setTimeout(() => {
        formMessageDiv.textContent = '';
        formMessageDiv.style.display = 'none';
        formMessageDiv.classList.remove('error', 'success');
    }, 4000);
}

// Validate field by name and value
function validateField(name, value) {
    // Check if required field is empty
    if (requiredFields.includes(name) && !value.trim()) {
        return {
            isValid: false,
            message: `${name.toUpperCase()} is required`
        };
    }
    
    // Skip validation for empty optional fields
    if (optionalFields.includes(name) && !value.trim()) {
        return { isValid: true };
    }
    
    // Pattern validation
    let isValid = false;
    switch (name) {
        case 'locn':
        case 'sku':
            isValid = patterns.alphanumeric.test(value);
            break;
        case 'uom':
            isValid = patterns.lettersOnly.test(value);
            break;
        case 'qty':
            // Special check for quantity - if it contains letters, show specific message
            if (/[a-zA-Z]/.test(value)) {
                return {
                    isValid: false,
                    message: 'Quantity cannot contain letters - only numbers allowed'
                };
            }
            isValid = patterns.positiveInteger.test(value);
            break;
        case 'lpn':
            isValid = value.trim() === '' || patterns.alphanumeric.test(value);
            break;
        default:
            isValid = true;
    }
    
    return {
        isValid: isValid,
        message: isValid ? '' : validationMessages[name]
    };
}

// Get star index for required fields
function getStarIndex(name) {
    return requiredFields.indexOf(name);
}

// Reset form to clean state but keep required asterisks visible
function resetForm() {
    form.reset();
    // Keep required field asterisks visible after reset
    requiredFields.forEach((fieldName, i) => {
        stars[i].classList.remove('hidden');
    });
    inputs.forEach(inp => inp.classList.remove('error-border'));
    inputs[0].focus();
}

inputs.forEach((input, index) => {
    input.addEventListener('keydown', (event) => {
        if (event.key === 'Enter') {
            event.preventDefault();

            const name = input.name;
            const val = input.value.trim();

            // For required fields, just check if empty and show star
            if (requiredFields.includes(name) && !val) {
                const starIndex = getStarIndex(name);
                if (starIndex >= 0) stars[starIndex].classList.remove('hidden');
                input.focus();
                return;
            } else if (requiredFields.includes(name)) {
                const starIndex = getStarIndex(name);
                if (starIndex >= 0) stars[starIndex].classList.add('hidden');
            }

            // If this is the last field, do complete validation and submit
            if (index === inputs.length - 1) {
                let allValid = true;
                let firstErrorMessage = '';
                let firstErrorInput = null;

                // Validate all required fields
                requiredFields.forEach((fieldName, i) => {
                    const fieldInput = form.querySelector(`input[name="${fieldName}"]`);
                    const value = fieldInput.value.trim();
                    const fieldValidation = validateField(fieldName, value);

                    if (!fieldValidation.isValid) {
                        stars[i].classList.remove('hidden');
                        fieldInput.classList.add('error-border');
                        if (allValid) {
                            firstErrorInput = fieldInput;
                            firstErrorMessage = fieldValidation.message;
                        }
                        allValid = false;
                    } else {
                        stars[i].classList.add('hidden');
                        fieldInput.classList.remove('error-border');
                    }
                });

                // Validate optional fields
                optionalFields.forEach((optName) => {
                    const optInput = form.querySelector(`input[name="${optName}"]`);
                    if (optInput && optInput.value.trim()) {
                        const optValidation = validateField(optName, optInput.value.trim());
                        if (!optValidation.isValid) {
                            optInput.classList.add('error-border');
                            if (allValid) {
                                firstErrorInput = optInput;
                                firstErrorMessage = optValidation.message;
                            }
                            allValid = false;
                        } else {
                            optInput.classList.remove('error-border');
                        }
                    }
                });

                if (!allValid) {
                    showValidationMessage(firstErrorMessage, true);
                    if (firstErrorInput) firstErrorInput.focus();
                    return;
                }

                // All validation passed - submit form
                 //formData -- js object that takes all input values from form and converts into key-value pair format.
                const formData = new FormData(form);

                 //method that take iterable from formdata.entries and converts into js object
                const formObject = Object.fromEntries(formData.entries());

                fetch('/second_form', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json',
                               'X-CSRFToken': csrfToken
                     },
                    body: JSON.stringify(formObject)
                })
                .then(response => response.json())
                .then(result => {
                    // Show success message
                    showValidationMessage(result.message || 'Data submitted successfully!', false);
                    
                    formsubmitted = 1;

                    // Reset form immediately after success
                    resetForm();
                })
                .catch(error => {
                    showValidationMessage(error.message || 'Error submitting data. Please try again.', true);
                });
            } else {
                // Move to next field
                inputs[index + 1].focus();
            }
        }
    });

    // Only handle empty required fields during input - no validation messages
    input.addEventListener('input', () => {
        const name = input.name;
        const val = input.value.trim();

        if (requiredFields.includes(name)) {
            const starIndex = getStarIndex(name);
            if (val) {
                stars[starIndex].classList.add('hidden');
            }
        }
    });
});

// ESC key redirect
document.addEventListener('keydown', function (event) {
    if (event.key === 'Escape') {
        window.location.href = '/firstpage';
    }
});