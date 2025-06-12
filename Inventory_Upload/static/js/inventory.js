 
 const form=document.getElementById('inventory_capture_2');
 const inputs = form.querySelectorAll('input');
 const Star = form.querySelectorAll('.required');

 let formsubmitted=0; 
 let firstEmptyField = null;

form.addEventListener('keydown',function(event){
            if(event.key ==='Enter'){
            event.preventDefault();

            
        let allValid = true;

        inputs.forEach((input, index) => {
            const value = input.value.trim();
            if (value === "") {
                Star[index].classList.add('visible');
                if (!firstEmptyField) {
            firstEmptyField = input;
            }
                allValid = false;
            } else {
                Star[index].classList.remove('visible');
            }
        });

        if (!allValid) {
            firstEmptyField.focus();
            return; // don't submit if any field is empty
        }

       const formData = new FormData(form); //formData -- js object that takes all input values from form and converts into key-value pair format.
        
       
       //method that take iterable from formdata.entries and converts into js object
        const formObject = Object.fromEntries(formData.entries());

        // console.log(formObject);
        fetch('/second_form', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formObject)
        })
        .then(response => response.json())
        .then(result => {
            alert(result.message);
            formsubmitted=1;  
            form.reset();

            Star.forEach(star => star.classList.remove('visible'));

        })
        .catch(error => {
            console.error('Error:', error);
        });
            }
        });

inputs.forEach((input, index) => {
    input.addEventListener('input', () => {
        if (input.value.trim() !== "") {
            Star[index].classList.remove('visible');
        }
    });
});

document.addEventListener('keydown',function(event)
{
     if(event.key ==='Escape' && formsubmitted){
        window.location.href='/'
     }
});


