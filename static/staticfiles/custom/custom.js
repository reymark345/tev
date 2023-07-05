'use strict';

(function () {
    // Init custom option check
    window.Helpers.initCustomOptionCheck();


    // Fetch all the forms we want to apply custom Bootstrap validation styles to
    const bsValidationForms = document.querySelectorAll('.needs-validation');

    // Loop over them and prevent submission
    Array.prototype.slice.call(bsValidationForms).forEach(function (form) {
        form.addEventListener(
            'submit',
            function (event) {
                if (!form.checkValidity()) {
                    event.preventDefault();
                    event.stopPropagation();
                } else {
                    // Submit your form
                    alert('Submitted!!!');
                }

                form.classList.add('was-validated');
            },
            false
        );
    });

    // Form sticky actions
    var topSpacing;
    const stickyEl = $('.sticky-element');

    // Init custom option check
    window.Helpers.initCustomOptionCheck();

    // Set topSpacing if the navbar is fixed
    if (Helpers.isNavbarFixed()) {
        topSpacing = $('.layout-navbar').height() + 7;
    } else {
        topSpacing = 0;
    }

    // sticky element init (Sticky Layout)
    if (stickyEl.length) {
        stickyEl.sticky({
            topSpacing: topSpacing,
            zIndex: 9
        });
    }

})();

function dateToday() {
    var date = new Date();

    var day = date.getDate();
    var month = date.getMonth() + 1;
    var year = date.getFullYear();

    if (month < 10) month = "0" + month;
    if (day < 10) day = "0" + day;

    return year + "-" + month + "-" + day;
}

function currencyFormat(value) {
    // Create our number formatter.
    const formatter = new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'PHP',

        // These options are needed to round to whole numbers if that's what you want.
        //minimumFractionDigits: 0, // (this suffices for whole numbers, but will print 2500.10 as $2,500.1)
        //maximumFractionDigits: 0, // (causes 2500.99 to be printed as $2,501)
    });

    return formatter.format(value)
}
