let clicked_id = 0;
let status_val =0;
let formattedDates = ''
let employeeList = [];
let remarks_date = [];
let selectedRemarks = [];
let selectedCb = [];

$(document).ready(function () {

    $('#f-employee-name').on('select2:open', function() {
        $('.select2-search__field').keydown(function(e) {
            if (e.keyCode === 9) { // Check if Tab key is pressed
            var selectedValue = $('#f-employee-name').val();
            if (selectedValue) {
                // Assuming the option value is "reymark"
                $('#f-employee-name').val(['2']).trigger('change.select2');
            }
            }
        });
    });


    employeelist();
    $('#loading-screen').hide();
    var dateField = $('#dateField').flatpickr({
        mode: 'multiple',
        allowInput: true,
        dateFormat: 'd-m-Y',
        locale: {
            'firstDayOfWeek': 1 // start week on Monday
        },
    });
    var fdateField = $('#f-dateField').flatpickr({
        mode: 'multiple',
        allowInput: true,
        dateFormat: 'd-m-Y',
        locale: {
            'firstDayOfWeek': 1 // start week on Monday
        },
    });

    $('#fileInput').change(function() {
        var fileName = $(this).val().split('\\').pop(); // Get the selected file name
        $('#selectedFileName').text(fileName);
    });

    $("#dateField").on("change", function() {
        if(DateTravel.val()){
            $(".rangeTravel").prop("disabled", true);
        }
        else{
            $(".rangeTravel").prop("disabled", false);
        } 
        });

    $(".rangeTravel").on("change", function() {
        
        if(RangeTravel.val()){
            $("#dateField").prop("disabled", true);
        }
        else{
            $("#dateField").prop("disabled", false);
        } 
    });
    // $(".remarks-list").on("change", function() {
    //     $("#dynamic-input-container").empty();
    //     selectedRemarks = $(this).val();
    //     if (selectedRemarks) {
    //         for (var i = 0; i < selectedRemarks.length; i++) {
    //             var inputId = "date-remarks-" + selectedRemarks[i];
    //             var selectedText = $(this).find('option[value="' + selectedRemarks[i] + '"]').text();
    //             var inputValue = remarks_date[i] || "";
    //             var inputElement = '<label class="form-label">Date for <b>' + selectedText + '</b></label> <input type="date" id="' + inputId + '" name="DateRemarks" class="form-control" value="' + inputValue + '" /><br>';
    //             $("#dynamic-input-container").append(inputElement);
    //         }
    //     }
    // })

    
    const table = $('#tbl-items')
    const ItemFormValidation = document.getElementById('item-form'),
        AdvancedFilter = document.getElementById('advanced-filter-list'),
        EmployeeName = jQuery(document.querySelector('[name="EmployeeName"]')),
        FEmployeeName = jQuery(document.querySelector('[name="FEmployeeName"]')),
        FIdNumber= jQuery(document.querySelector('[name="FIdNumber"]')),
        FTransactionCode= jQuery(document.querySelector('[name="FTransactionCode"]')),
        FDateTravel= jQuery(document.querySelector('[name="FDateTravel"]')),
        FIncomingIn= jQuery(document.querySelector('[name="FIncomingIn"]')),
        DateRemarks = jQuery(document.querySelector('[name="DateRemarks"]')),
        // FSLashedOut= jQuery(document.querySelector('[name="FSLashedOut"]')),
        FOriginalAmount= jQuery(document.querySelector('[name="FOriginalAmount"]')),
        FFinalAmount= jQuery(document.querySelector('[name="FFinalAmount"]')),
        FAccountNumber= jQuery(document.querySelector('[name="FAccountNumber"]')),
        FStatus= jQuery(document.querySelector('[name="FStatus"]')),
        FCreatedBy= jQuery(document.querySelector('[name="FCreatedBy"]')),
        FFirstName= jQuery(document.querySelector('[name="FFirstName"]')),
        FMiddleName= jQuery(document.querySelector('[name="FMiddleName"]')),
        FLastName= jQuery(document.querySelector('[name="FLastName"]')),
        FAdvancedFilter= jQuery(document.querySelector('[name="FAdvancedFilter"]')),
        OriginalAmount = jQuery(document.querySelector('[name="OriginalAmount"]')),
        DateReceived = jQuery(document.querySelector('[name="DateReceived"]')),
        DateTravel = jQuery(document.querySelector('[name="DateTravel"]')),
        HDateTravel = jQuery(document.querySelector('[name="HDateTravel"]')),
        RangeTravel = jQuery(document.querySelector('[name="RangeTravel"]')),
        IdNumber = jQuery(document.querySelector('[name="IdNumber"]')),
        DivisionUser = jQuery(document.querySelector('[name="DivisionUser"]')),
        SectionUser = jQuery(document.querySelector('[name="SectionUser"]')),
        ContactNo = jQuery(document.querySelector('[name="ContactNo"]')),
        AccountNumber = jQuery(document.querySelector('[name="AccountNumber"]')),
        EmpName = jQuery(document.querySelector('[name="EmpName"]')),
        EmpMiddle = jQuery(document.querySelector('[name="EmpMiddle"]')),
        EmpLastname = jQuery(document.querySelector('[name="EmpLastname"]')),
        RemarksList= jQuery(document.querySelector('[name="RemarksList"]')),
        offCanvasElement = document.querySelector('#add-new-record'),
        search_advance_filter = $('#search-advance-filter'),
        reset_advance_filter = $('#reset-advance-filter'),
        clear_advance_filter = $('#clear-advance-filter')
    const offCanvasEl = new bootstrap.Offcanvas(offCanvasElement)
    const toast_options = (toastr.options = {
        maxOpened: 1,
        autoDismiss: true,
        closeButton: true,
        newestOnTop: true,
        progressBar: true,
        positionClass: 'toast-top-right',
        rtl: isRtl,
    });
    let ItemID = $('#item-id')

    let dataTable = table.DataTable({
        processing: true,
        serverSide: true,
        ajax: {
            url: itemLoadUrl,
            data: function (d) {
                d.FAdvancedFilter = FAdvancedFilter.val()
                d.FIdNumber = FIdNumber.val()
                d.FTransactionCode = FTransactionCode.val()
                d.FDateTravel = FDateTravel.val()
                d.FIncomingIn = FIncomingIn.val()
                d.FOriginalAmount = FOriginalAmount.val()
                d.FFinalAmount = FFinalAmount.val()
                d.FAccountNumber = FAccountNumber.val()
                d.FStatus = FStatus.val()
                d.FCreatedBy = FCreatedBy.val()
                d.FFirstName = FFirstName.val()
                d.FMiddleName = FMiddleName.val()
                d.FLastName = FLastName.val()
                d.EmployeeList = employeeList
            },
        },
        columns: [
            {
                data: 'id', status: 'status',
                orderable: false, 
                render: function (data, type, row) {
                    let isChecked = selectedCb.includes(data.toString());
                    var status = row.status;
                    var status = row.status;
                    if (status == 3) {
                        return '<input type="checkbox" disabled="disabled" class="dt-checkboxes form-check-input">';
                    } else {
                        return `<input type="checkbox" class="dt-checkboxes form-check-input checkbox-items" value="${data}" id ="checkbox_data" ${isChecked ? 'checked' : ''}>`;
                    }

                }
            },
            { data: 'id_no' },
            { data: 'name' },
            { data: 'original_amount'},
            { data: 'final_amount'},
            { data: 'date_travel'},
            { data: 'status' },
            { data: 'incoming_in' },
            { data: 'slashed_out' },
            { data: 'remarks' },
            { data: 'lacking' },
            { data: 'user_id' },
            { data: 'id'},
        ],
        columnDefs: [
            {
                targets: 1,
                render: function(data) {
                    if (data){
                        return '<span class="badge bg-label-primary">' + data + '</span>';
                    }
                    else {
                        return ''
                    }
                },
            },
            {
                targets: 3,
                render: function(data) {
                    var floatValue = parseFloat(data);
                    if (floatValue !== 0) {
                        var formattedValue = floatValue.toLocaleString('en-US', {
                            minimumFractionDigits: 2,
                            maximumFractionDigits: 2
                        });
                        return '<span class="badge bg-label-primary"> ' +formattedValue+'</span>';
                    } else {
                        return "";
                    }
                },
            },  
            {
                targets: 4,
                render: function(data) {
                    var floatValue = parseFloat(data);
                    if (floatValue !== 0) {
                        var formattedValue = floatValue.toLocaleString('en-US', {
                            minimumFractionDigits: 2,
                            maximumFractionDigits: 2
                        });
                        return '<span class="badge bg-label-primary"> ' +formattedValue+'</span>';
                    } else {
                        return "";
                    }
                },
            },  
            {
                targets: 5,
                render: function(data) {
                    var splitValues = data.split(','); 
                    var result = '';
                    
                    splitValues.forEach(function(value, index) {
                        if (index !== 0) {
                            result += '  '; 
                        }
                        var dateParts = value.split('-');
                        var monthNames = ["Jan.", "Feb.", "Mar.", "Apr.", "May", "Jun.", "Jul.", "Aug.", "Sep.", "Oct.", "Nov.", "Dec."];
                        var formattedDate = monthNames[parseInt(dateParts[1], 10) - 1] + ' ' + parseInt(dateParts[0], 10) + ', ' + dateParts[2];
                        
                        result += '<span class="badge bg-label-primary">' + formattedDate + '</span>';
                    });
                    
                    return result;
                },
            },

            
            {
                targets: 6,
                render: function (data) {
                    if (data==1){
                    return '<span class="badge bg-label-warning">Pending</span>'
                    }
                    else if(data==2){
                    return '<span class="badge bg-label-warning">For checking</span>'
                    }
                    else if(data==3){
                    return '<span class="badge bg-label-danger">Returned</span>'
                    }
                    else{
                    return '<span class="badge bg-label-success">For payroll</span>'
                    }

                },
            },
            {
                targets: -6,
                render: function (data) {
                    return (data == null) ? '' : moment(data).format('LLL');
                },
            },
            {
                targets: -5,
                render: function (data) {
                    return (data == null) ? '' : moment(data).format('LLL');
                },
            },
            {
                targets: -4,
                render: function (data) {
                    return data;
                    // if (data === null || data === undefined || data === "") {
                    //     return ''; // Return an empty string if data is null, undefined, or empty
                    // } 
                    // else {
                    //     return '<span class="badge bg-label-danger">' + data + '</span>';
                    // }
                },
            },
            {
                targets: -3,
                render: function (data) {
                    if (data === null || data === undefined || data === "") {
                        return ''; // Return an empty string if data is null, undefined, or empty
                    } 
                    else {
                        return data;
                        // return '<span class="badge bg-label-danger">' + data + '</span>';
                    }
                },
            },
            {
                targets: -2,
                render: function (data) {
                    if (data === null || data === undefined || data === "") {
                        return ''; 
                    } 
                    else {
                        return '<span class="badge bg-label-primary">' + data + '</span>';
                    }
                },
            },
            {
                targets: -1,
                title: 'Action',
                orderable: false,
                searchable: false,
                render: function (data) {
                return (
                    '<a href="javascript:;" data-id="' + data + '" class="item-edit text-body"><i class="text-primary ti ti-pencil"></i></a>' +
                    '<a href="javascript:;" data-id="' + data + '" class="item-delete text-body"><i class="text-primary ti ti-trash"></i></a>'
                )
                },
            },
        ],
        dom: '<"card-header flex-column flex-md-row"<"head-label text-center"><"dt-action-buttons text-end pt-3 pt-md-0"B>><"row"<"col-sm-12 col-md-6"l><"col-sm-12 col-md-6 d-flex justify-content-center justify-content-md-end"f>>t<"row"<"col-sm-12 col-md-6"i><"col-sm-12 col-md-6"p>>',
        buttons: [
            {
                className: 'btn btn-label-primary me-2',
                text: '<i class="ti ti-file-search me-sm-1"></i> <span class="d-none d-sm-inline-block">Advance Filter</span>',
                action: function () {
                    employeeList = [];
                    const $selectElement = $('#f-employee-name');
                    $selectElement.empty();
                    fetchEmployee($selectElement);
                    FEmployeeName.val('').trigger('change');
                    setTimeout(function() {
                        if (FEmployeeName.length) {
                            FEmployeeName.wrap('<div class="position-relative"></div>')
                            FEmployeeName.select2({
                                placeholder: 'Choose employee',
                                dropdownParent: FEmployeeName.parent(),
                                allowClear: true,
                            })
                        }
                    }, 300);
                    clear_advfilter();
                    $("#advance-filter").modal("show");
                }

            },
            // {
            //     className: 'btn btn-label-primary me-2',
            //     text: '<i class="ti ti-file-export me-sm-1"></i> <span class="d-none d-sm-inline-block">Forward</span>',
            //     action: function () {
            //         // Get the IDs of checked items
            //         if(selectedCb.length ===0){
            //             toastr.error('Select item first', 'Invalid', toast_options);
            //         }
            //         else{
            //             incoming_out();
            //         }
            //     }
            // },

            // {
            //     className: 'btn btn-label-success me-2 waves-effect',
            //     text: '<i class="ti ti-file-import me-sm-1"></i> <span class="d-none d-sm-inline-block">Import xlsx</span>',
            //     action: function () {
            //         $("#import-excel").modal("show");              
            //     }
            // },


            {
                text: '<i class="ti ti-plus me-sm-1"></i> <span class="d-none d-sm-inline-block">Add New Record</span>',
                className: 'create-new btn btn-primary',
            },
        ],
        drawCallback: function (settings) {
            $('.item-edit').on('click', function () {
                let id = $(this).data('id')
                $('.title-name').text('Update TEV Record');
                $.ajax({
                    type: 'GET',
                    url: "{% url 'preview-received' %}?id=" + id,
                    dataType: 'json',
                }).done(function (data) {
                    let arraydetails = [];
                    let lacking_ = data.lacking;
                    let date_remarks_ = data.date_remarks;
                    let d_received = data.incoming_in;
                    $('.rows-container').empty();
                    let dateObj = new Date(d_received);
                    let year = dateObj.getFullYear();
                    let month = String(dateObj.getMonth() + 1).padStart(2, '0'); // Adding 1 because months are zero-indexed
                    let day = String(dateObj.getDate()).padStart(2, '0');
                    let hours = String(dateObj.getHours()).padStart(2, '0');
                    let minutes = String(dateObj.getMinutes()).padStart(2, '0');
                    let date_received = `${year}-${month}-${day} ${hours}:${minutes}`;
                    if (lacking_){
                        lacking_ = lacking_.split(',').map(Number);
                        date_remarks_ = date_remarks_.split(", ")

                        for (let i = 0; i < lacking_.length; i++) {                            
                            var newRow = $('<div class="row mt-2">' +
                                '<div class="col-5">' +
                                '<select class="form-select select-remarks" id="remarks-select-'+i+'">' +
                                '<option></option>' +
                                '{% for row in remarks_list %}' +
                                '<option value="{{ row.id }}">{{ row.name }}</option>' +
                                '{% endfor %}' +
                                '</select>' +
                                '</div>' +
                                '<div class="col-5">' +
                                '<input type="date" id="date-remarks" name="DateRemarks" class="form-control input-date" value="' + date_remarks_[i] + '" />' +
                                '</div>' +
                                '<div class="col-2">' +
                                '<button type="button" class="btn btn-warning delete-row">-</button>' +
                                '</div>' +
                                '</div>');
                            $('.rows-container').append(newRow);

                            $(`#remarks-select-${i}`).val(lacking_[i]).trigger('change');

                            item_entry = {
                                'remarks': lacking_[i],
                                'date': date_remarks_[i]
                            }
                            arraydetails.push(item_entry);
                        }
                    }
                    const $selectElement1 = $('#employee-name');
                    $selectElement1.empty();
                    fetchEmployee($selectElement1);
                    if (EmployeeName.length) {
                        EmployeeName.wrap('<div class="position-relative"></div>')
                        EmployeeName.select2({
                        placeholder: 'Choose employee',
                        dropdownParent: EmployeeName.parent(),
                        allowClear: true,
                        })
                    }

                    if (RemarksList.length) {
                        RemarksList.wrap('<div class="position-relative"></div>')
                        RemarksList.select2({
                        placeholder: 'Choose remarks',
                        dropdownParent: RemarksList.parent(),
                        allowClear: true,
                        })
                    }

                    let pk = data.id
                    let employee_name = $('#employee-name');
                    let floatvalue = parseFloat(data.final_amount);
                    let convertedAmount = 0;
                    let date_travel = data.date_travel;
                    formattedDates = date_travel.split(',').map(date => date.trim()).join(', ');

                    status_val = data.status_id;
                    let fullname = data.first_name + " " + data.middle_name + " " + data.last_name
                    let id_no = data.id_no;
                    let date_remarks = data.date_remarks;
                    let lacking = data.lacking;
                    
                    
                    if (date_remarks){
                        date_remarks = date_remarks.split(", ")
                        remarks_date = date_remarks;
                    }

                    if(status_val ===3){
                        EmployeeName.val(id_no).trigger('change').prop("disabled", true);
                        convertedAmount = floatvalue.toFixed(2);
                        OriginalAmount.prop("disabled", true);
                        DateTravel.prop("disabled", true);
                        RangeTravel.prop("disabled", true);
                    }
                    else{
                        EmployeeName.val(id_no).trigger('change').prop("disabled", false);
                        let original_amt = parseFloat(data.original_amount)
                        convertedAmount = original_amt.toFixed(2);
                        OriginalAmount.prop("disabled", false);
                        DateTravel.prop("disabled", false);
                        RangeTravel.prop("disabled", false);
                    }

                    if (DateTravel){
                        RangeTravel.prop("disabled", true);
                    }
                    else if(RangeTravel){
                        DateTravel.prop("disabled", true);
                    }
                    HDateTravel.val(formattedDates)
                    OriginalAmount.val(convertedAmount);
                    DateReceived.val(date_received);

                    DateTravel.val(formattedDates);
                    ItemID.val(pk);
                    updateSelectedDates();
                    offCanvasEl.show()
                    
                })
            }),

            $('.item-delete').on('click', function () {
                let id = $(this).data('id');

                Swal.fire({
                title: 'Delete?',
                text: "You won't be able to revert this!",
                icon: 'warning',
                showCancelButton: true,
                confirmButtonText: 'Yes, Remove it!',
                customClass: {
                    confirmButton: 'btn btn-primary me-3',
                    cancelButton: 'btn btn-label-secondary',
                },
                buttonsStyling: false,
            }).then(function (result) {
                if (result.value) {
                    $.ajax({
                        type: 'POST',
                        url: "{% url 'delete-entry' %}",
                        data:{
                            item_id: id
                        }
                    }).done(function (data) {
                        if (data.data == 'success') {
                            selectedCb = [];
                            Swal.fire({
                                icon: 'success',
                                title: 'Successfully deleted!',
                                text: 'Item has been deleted.',
                                customClass: {
                                    confirmButton: 'btn btn-success',
                                },
                            })

                            dateField.clear();
                            dataTable.ajax.reload()
                        } else {
                            Swal.fire({
                                icon: 'error',
                                title: 'Error saving!',
                                text: data.error,
                                customClass: {
                                    confirmButton: 'btn btn-success',
                                },
                            })
                        }
                    })
                }
            })   
                
            }),

            $('.item-delete-off').on('click', function () {
                toastr.error('This item cannot delete!', 'Invalid', toast_options);
            }),

            $('#tbl-items').on('click', '.dt-checkboxes', function () {
                var id = $(this).val();
                if ($(this).prop('checked')) {
                    if (selectedCb.indexOf(id) === -1) {
                        selectedCb.push(id);
                    }
                    $(this).data('checked', true); 
                } else {

                    let index = selectedCb.indexOf(id);
                    if (index !== -1) {
                        selectedCb.splice(index, 1);
                    }
                    $(this).data('checked', false); 
                }
            });

            $('#check-all').change(function () {
                var isChecked = $(this).is(':checked');
                $('#tbl-items tbody input[type="checkbox"][class="dt-checkboxes form-check-input checkbox-items"]').prop('checked', isChecked);
                if (isChecked) {
                    // Add all IDs to the array
                    $('#tbl-items tbody input[type="checkbox"][class="dt-checkboxes form-check-input checkbox-items"]').each(function () {
                        var id = $(this).val();
                        if (selectedCb.indexOf(id) === -1) {
                            selectedCb.push(id);
                        }
                    });
                } else {
                    // Remove all IDs from the array
                    $('#tbl-items tbody input[type="checkbox"][class="dt-checkboxes form-check-input checkbox-items"]').each(function () {
                        var id = $(this).val();
                        let index = selectedCb.indexOf(id);
                        if (index !== -1) {
                            selectedCb.splice(index, 1);
                        }
                    });
                }

                // Log or perform further actions with the selectedCb array
            });

            $('.item-details').on('click', function () {
                clicked_id = $(this).data('id');
                $.ajax({
                    type: 'POST',
                    url: "{% url 'tev-details' %}",
                    data:{
                        tev_id: clicked_id
                    }
                }).done(function (data) {
                    let value = data.data.remarks;
                    let final_amount = data.data.final_amount;
                    let floatvalue = parseFloat(final_amount);
                    let convertedAmount = floatvalue.toFixed(2);
                    if (convertedAmount === "0.00") {convertedAmount =""} 
                    $("#final_amount").val(convertedAmount);
                    $("#correctness_remarks").val(value);
                })
            });
        },
    })
    // $('div.head-label').html('<h5 class="card-title mb-0">Items</h5>')
    $('div.head-label').html('<h5 class="card-title mb-0 d-flex align-items-center">'+
    '<button type="submit" id="forward" class="btn btn-primary">Forward</button>' +
    '</h5>');

    const newRecord = document.querySelector('.create-new')
        if (newRecord) {
            newRecord.addEventListener('click', function () {
                const $selectElement1 = $('#employee-name');
                $selectElement1.empty();
                fetchEmployee($selectElement1);
                if (EmployeeName.length) {
                    EmployeeName.wrap('<div class="position-relative"></div>')
                    EmployeeName.select2({
                        placeholder: 'Choose employee',
                        dropdownParent: EmployeeName.parent(),
                        allowClear: true,
                    })
                }

                if (RemarksList.length) {
                    RemarksList.wrap('<div class="position-relative"></div>')
                    RemarksList.select2({
                    placeholder: 'Choose remarks',
                    dropdownParent: RemarksList.parent(),
                    allowClear: true,
                    })
                }
                ItemID.val(0);
                $('.rows-container').empty();
                $("#dateField").prop("disabled", false);
                $(".rangeTravel").prop("disabled", false);
                OriginalAmount.prop("disabled", false);
                $('.title-name').text('Add Travel Data');
                status_val = 0;
                EmployeeName.val('').trigger('change').prop("disabled", false);
                $('.form-control').val('');
                updateSelectedDates();
                offCanvasEl.show()
            })
        }
    const fv = FormValidation.formValidation(ItemFormValidation, {
        fields: {
            EmployeeName: {
                validators: {
                    notEmpty: {
                        message: 'Please Select Employee',
                    },
                },
            },
            OriginalAmount: {
                validators: {
                    notEmpty: {
                        message: 'Please Select Amount',
                    },
                },
            },
            

        },
        plugins: {
            trigger: new FormValidation.plugins.Trigger(),
            bootstrap5: new FormValidation.plugins.Bootstrap5(),
            submitButton: new FormValidation.plugins.SubmitButton(),
            autoFocus: new FormValidation.plugins.AutoFocus(),
        },
        init: (instance) => {
            instance.on('plugins.message.placed', function (e) {
                if (e.element.parentElement.classList.contains('input-group')) {
                    e.element.parentElement.insertAdjacentElement('afterend', e.messageElement)
                }
            })
        },
    }).on('core.form.valid', function () {
        let selectedIDs = [];
        let selectedDate = [];
        if (DateTravel.val() && RangeTravel.val() ){
            toastr.error('Duplicate Travel Date : Select only one', 'Invalid', toast_options);
        }
        else if (!DateTravel.val() && !RangeTravel.val()){
            toastr.error('Please: Select one Date Travel', 'Invalid', toast_options);
        }
        else {
            let dateValues = [];
            let isValidationError = 0;
            // let selectedValues = $(".remarks-list").val();
            // $("input[type='date']").each(function() {
            //     if ($(this).val() !== "") {
            //         dateValues.push($(this).val());
            //     }
            // });
            // $("input[type='date']").each(function() {
            //     var dateValue = $(this).val();

            //     // Check if the value is not empty before adding to the array
            //     if (dateValue !== "") {
            //         isValidationError-1;
            //         dateValues.push(dateValue);
            //         $(this).next(".error-message").remove();
            //     }
            //     else if (selectedValues.length === 0){
            //         isValidationError = 0;
            //     } else {
            //         isValidationError++;
            //         $(this).next(".error-message").remove(); // Remove existing error messages
            //         $(this).after('<div class="error-message">Required!</div>');
            //     }
            // });


            $('.rows-container .row').each(function() {
                let selectElement = $(this).find('.select-remarks');
                let selectElementDate = $(this).find('.select-remarks');
                let selectedValue = selectElement.val();
                let selectErrorLabel = selectElement.siblings(".error-label");

                let inputElement = $(this).find('.input-date');
                let inputValue = inputElement.val();
                let inputErrorLabel = inputElement.siblings(".error-label-date");

                if (selectedValue !== "") {
                    selectedIDs.push(selectedValue);
                    selectElement.removeClass('has-error');
                    selectErrorLabel.hide();
                } else {
                    isValidationError++;
                    selectElement.addClass('has-error');
                    selectErrorLabel.show();
                }
                if (inputValue !== "") {
                    selectedDate.push(inputValue);
                    inputElement.removeClass('has-error');
                    inputErrorLabel.hide();
                } else {
                    isValidationError++;
                    inputElement.addClass('has-error');
                    inputErrorLabel.show();
                }
            });
            if (isValidationError == 0) {
                let amount = OriginalAmount.val();
                let date_travel = DateTravel.val();
                let range_travel = RangeTravel.val();
                let id_no = IdNumber.val();
                let acct_no = AccountNumber.val();
                let name = EmpName.val();
                let middle = EmpMiddle.val();
                let lname = EmpLastname.val();
                let hdate_travel = HDateTravel.val();
                let division = DivisionUser.val();
                let section = SectionUser.val();
                let contact = ContactNo.val();
                let date_received = DateReceived.val();
                let post_url = (status_val == 3)? "{% url 'item-returned' %}": (ItemID.val() !== '0')? "{% url 'item-update' %}": "{% url 'item-add' %}";
                let form_data = $('#item-form').serialize()
                $.ajax({
                    type: 'POST',
                    url: post_url,
                    data: {
                        DateTravel: date_travel,
                        RangeTravel: range_travel,
                        AccountNumber: acct_no,
                        IdNumber: id_no,
                        EmpName: name,
                        EmpMiddle: middle,
                        EmpLastname: lname,
                        OriginalAmount: amount,
                        form_data: form_data,
                        dateValues: dateValues,
                        HDateTravel: hdate_travel,
                        Division: division,
                        Section: section,
                        Contact: contact,
                        ItemID:ItemID.val(),
                        selectedRemarks: selectedIDs,
                        selectedDate: selectedDate,
                        DateReceived: date_received
                    }
                }).done(function (data) {                
                    function formatDate(dateString) {
                        const [day, month, year] = dateString.split("-");
                        const months = ["Jan.", "Feb.", "Mar.", "Apr.", "May", "Jun.", "Jul.", "Aug.", "Sep.", "Oct.", "Nov.", "Dec."];
                        const monthName = months[parseInt(month, 10) - 1];
                        return `${monthName} ${day}, ${year}`;
                    }
                    if (data.data == 'success') {
                        dateField.clear();
                        $('.rows-container').empty();
                        let code = data.g_code;
                        if (code){
                            toastr.success('Save Successfully', 'Success', toast_options);
                        }
                        else{
                            offCanvasEl.hide()
                            Swal.fire({
                                icon: 'success',
                                title: 'Update Successfully!',
                                html:
                                'Successfully <b>Save!</b>',
                                customClass: {
                                    confirmButton: 'btn btn-success',
                                },
                            })
                        }
                        EmployeeName.val("").trigger('change');
                        RemarksList.val([]).trigger("change");
                        OriginalAmount.val("");
                        DateReceived.val("");
                        DateTravel.val("");
                        RangeTravel.val("");
                        $("#dateField").prop("disabled", false);
                        $(".rangeTravel").prop("disabled", false);
                        dataTable.ajax.reload();
                    } else {
                        if (status_val== 0){
                            dateField.clear();
                            EmployeeName.val("").trigger('change');
                            RemarksList.val([]).trigger("change");
                            OriginalAmount.val("");
                            DateReceived.val("");
                            DateTravel.val("");
                            RangeTravel.val("");
                        }
                        let formattedDates = data.message.map(date => formatDate(date)).join(" | ");
                        $("#dateField").prop("disabled", false);
                        $(".rangeTravel").prop("disabled", false);
                        dataTable.ajax.reload();
                        Swal.fire({
                            icon: 'error',
                            title: 'Duplicate Travel!',
                            html:"Date: <br><b>"+formattedDates+"</b>",
                            customClass: {
                                confirmButton: 'btn btn-success',
                            },
                        })
                    }
                })
            }
        }
    });



    
    // Form validation for Add new record
    const adv = FormValidation.formValidation(AdvancedFilter, {
        fields: {
        },
        plugins: {
            trigger: new FormValidation.plugins.Trigger(),
            bootstrap5: new FormValidation.plugins.Bootstrap5(),
            submitButton: new FormValidation.plugins.SubmitButton(),
            autoFocus: new FormValidation.plugins.AutoFocus(),
        },
        init: (instance) => {
            instance.on('plugins.message.placed', function (e) {
                if (e.element.parentElement.classList.contains('input-group')) {
                    e.element.parentElement.insertAdjacentElement('afterend', e.messageElement)
                }
            })
        },
    }).on('core.form.valid', function () {
        var form_data = $('#advanced-filter-list').serialize();
        var form_data = $('#item-form').serialize()
        $.ajax({
            type: 'POST',
            url: "{% url 'search-list' %}",
            data: form_data,
        }).done(function (data) {
            if (data.data == 'success') {

            } else {

            }
        });

    });


function fetchEmployee($selectElement) {
    const employees = JSON.parse(localStorage.getItem('employees'));
    if (employees) {
        $.each(employees, function (index, employee) {
            const optionText = `${employee.firstName} ${employee.middleInitial} ${employee.lastName}`;
            const $option = $('<option>', {
                value: employee.idNumber,
                text: optionText,
                id: employee.idNumber
            });
            $selectElement.append($option);
        });
    } else {
        console.log("No employee data found in local storage.");
    }
}

function updateSelectedDates() {
    var inputFieldValue = $('#dateField').val();
    if (inputFieldValue) {
        var inputDates = inputFieldValue.split(', ');
        var selectedDates = inputDates.map(function(dateString) {
            return dateString;
        });
        dateField.setDate(selectedDates);
    } else {
        dateField.clear();
    }
}

function employeelist(){
    $.ajax({
        type: 'GET',
        url: "{% url 'receive-api' %}",
        dataType: 'json',
    }).done(function (data) {
        let fields = data.data;
        let employees = [];
        $.each(fields, function (index, employee) {
            let firstName = employee.first_name;
            let middleName = employee.middle_name;
            let middleInitial = middleName.charAt(0);
            let lastName = employee.last_name;
            let idNumber = employee.id_number;
            let accNumber = employee.account_number;
            let division = employee.division;
            let position = employee.position;
            let gender = employee.gender;
            let section = employee.section;
            let image_path = employee.image_path;
            let contact = employee.contact;
    
            let employeeObj = {
                firstName: firstName,
                middleInitial: middleInitial,
                lastName: lastName,
                idNumber: idNumber,
                accNumber: accNumber,
                division: division,
                position: position,
                gender: gender,
                section: section,
                image: image_path,
                contact_no: contact
            };
            employees.push(employeeObj);
        });
        localStorage.setItem('employees', JSON.stringify(employees));
    });
    
}

function incoming_out(){
    selectedCb = $.grep(selectedCb, function(value) {
        return value !== 'on';
    });

    Swal.fire({
        title: 'Forward?',
        text: "You won't be able to revert this!",
        icon: 'warning',
        showCancelButton: true,
        confirmButtonText: 'Yes, Forward it!',
        customClass: {
            confirmButton: 'btn btn-primary me-3',
            cancelButton: 'btn btn-label-secondary',
        },
        buttonsStyling: false,
    }).then(function (result) {
        if (result.value) {
            $.ajax({
                type: 'POST',
                url: "{% url 'out-pending-tev' %}",
                data:{
                    out_list: selectedCb
                }
            }).done(function (data) {
                if (data.data == 'success') {
                    selectedCb = [];
                    Swal.fire({
                        icon: 'success',
                        title: 'Successfully save!',
                        text: 'Item has been added.',
                        customClass: {
                            confirmButton: 'btn btn-success',
                        },
                    })

                    dateField.clear();
                    dataTable.ajax.reload()
                } else {
                    Swal.fire({
                        icon: 'error',
                        title: 'Error saving!',
                        text: data.message,
                        customClass: {
                            confirmButton: 'btn btn-success',
                        },
                    })
                }
            })
        }
    })

}
$('#forward').on('click', function(){
    if(selectedCb.length ===0){
        toastr.error('Selected item first', 'Invalid', toast_options);
    }
    else{
        incoming_out();
    }
});

$('#add_remarks').click(function () {     
    var newRow = $('<div class="row mt-2">' +
        '<div class="col-5">' +
        '<select class="form-select select-remarks" id="select_remarks">' +
            '<option></option>'+
            '{% for row in remarks_list %}'+
            '<option value="{{ row.id }}">{{ row.name }}</option>'+
            '{% endfor %}'+
        '</select>' +
        '<span class="error-label">Required</span>'+
        '</div>' +
        '<div class="col-5">' +
        '<input type="date" id="date-remarks" name="DateRemarks" class="form-control input-date" value="" />'+
        '<span class="error-label-date">Required</span>'+
        '</div>' +
        '<div class="col-2">' +
        '<button type="button" class="btn btn-warning delete-row">-</button>' +
        '</div>' +
        '</div>');
        newRow.find('.error-label, .error-label-date').hide();
    $('.rows-container').append(newRow);
});
$('.container').on('click', '.delete-row', function () {
    $(this).closest('.row').remove();
});
$(document).on('click', '.delete-row', function () {
    $(this).closest('.row').remove();
});

$('.container').on('click', '.delete-row', function () {
        $(this).closest('.row').remove();
});

$('#uploadButton').on('click', function(event) {
    if ($('#fileInput').get(0).files.length === 0) {
        toastr.error('No Excel File Selected', 'Invalid', toast_options);
    } 
    else {
        $("#import-excel").modal("hide");
        $('#loading-screen').show();
        event.preventDefault();
        let LStorage = JSON.parse(localStorage.getItem('employees'));
        var formData = new FormData();
        formData.append('ExcelData', $('input[name=ExcelData]')[0].files[0]);
        formData.append('employees', JSON.stringify(LStorage));
        $.ajax({
            type: "POST",
            url: "{% url 'upload-tev' %}",
            data: formData,
            contentType: false,
            processData: false,
            }).done(function(data){
            if (data.data == 'success') {
                $('#fileInput').val('');
                $('#selectedFileName').text('');

                $('#loading-screen').hide();

                if (data.id_no && data.id_no.length){
                    Swal.fire({
                        title: '<strong>ID NUMBER NOT FOUND!</strong> <br><h5><u>'+data.id_no+'<h5></u>',
                        icon: 'error',
                        html:
                        'Excel <b>NOT SAVE!</b>',
                        showCloseButton: true,
                        showCancelButton: false,
                        focusConfirm: false,
                        confirmButtonText: '<i class="ti ti-thumb-up"></i> Done!',
                        confirmButtonAriaLabel: 'Thumbs up, great!',
                        customClass: {
                        confirmButton: 'btn btn-danger me-3'
                        },
                        buttonsStyling: false
                    });
                    toastr.error('Invalid', 'Error', toast_options);
                }
                else if (data.duplicate_excel_dates){
                    let duplicate = data.duplicate_excel_dates;
                    let tableRows = duplicate.map(item => {
                        return `<tr>
                                    <td style="border: 1px solid black;">${item.id_no}</td>
                                    <td style="border: 1px solid black;">${item.duplicate_travel}</td>
                                </tr>`;
                    });

                    Swal.fire({
                        title: '<strong>Excel File Duplication Date!</strong>',
                        icon: 'error',
                        html:
                        'Excel <b>NOT SAVE!</b> Please <b>reupload</b> the file!' +
                        '<table style="width:100%;">' +
                        '<tr>' +
                        '<th style="border: 1px solid black;"><b>ID number</b></th>' +
                        '<th style="border: 1px solid black;"><b>Duplicate date</b> <small>(dd-mm-yyyy)</small></th>' +
                        '</tr>' +
                        `${tableRows.join('')}` + // Join the rows and insert them into the table
                        '</table>',
                        showCloseButton: true,
                        showCancelButton: false,
                        focusConfirm: false,
                        allowOutsideClick: false,
                        confirmButtonText: '<i class="ti ti-thumb-up"></i> Done!',
                        confirmButtonAriaLabel: 'Thumbs up, great!',
                        customClass: {
                        confirmButton: 'btn btn-danger me-3'
                        },
                        buttonsStyling: false
                    });
                    toastr.error('Invalid', 'Error', toast_options);

                }
                else if(data.duplicate_travel){
                    let duplicate = data.duplicate_travel;
                    let tableRows = duplicate.map(item => {
                        return `<tr>
                                    <td style="border: 1px solid black;">${item.id_no}</td>
                                    <td style="border: 1px solid black;">${item.duplicate_travel}</td>
                                </tr>`;
                    });

                    Swal.fire({
                        title: '<strong>Duplicate TRAVEL, Added already in System!</strong>',
                        icon: 'error',
                        html:
                        'Excel <b>NOT SAVE!</b> Please <b>reupload</b> the file!' +
                        '<table style="width:100%;">' +
                        '<tr>' +
                        '<th style="border: 1px solid black;"><b>ID number</b></th>' +
                        '<th style="border: 1px solid black;"><b>Duplicate date</b> <small>(dd-mm-yyyy)</small></th>' +
                        '</tr>' +
                        `${tableRows.join('')}` + // Join the rows and insert them into the table
                        '</table>',
                        showCloseButton: true,
                        showCancelButton: false,
                        focusConfirm: false,
                        allowOutsideClick: false,
                        confirmButtonText: '<i class="ti ti-thumb-up"></i> Done!',
                        confirmButtonAriaLabel: 'Thumbs up, great!',
                        customClass: {
                        confirmButton: 'btn btn-danger me-3'
                        },
                        buttonsStyling: false
                    });
                    toastr.error('Invalid', 'Error', toast_options);
                    

                }
                else{
                    toastr.success('Successfully save', 'Success', toast_options);
                }

                $("#import-excel").modal("hide");
                dataTable.ajax.reload();

            } 
            else if (data.data == 'empty'){
                $("#import-excel").modal("hide");
                $('#loading-screen').hide();
                Swal.fire({
                        title: '<strong>Excel File: Empty column!</strong>',
                        icon: 'error',
                        html:
                        'Excel <b>NOT SAVE! Please Review and Reupload</b> the file!',
                        showCloseButton: true,
                        showCancelButton: false,
                        focusConfirm: false,
                        confirmButtonText: '<i class="ti ti-thumb-up"></i> Done!',
                        confirmButtonAriaLabel: 'Thumbs up, great!',
                        customClass: {
                        confirmButton: 'btn btn-danger me-3'
                        },
                        buttonsStyling: false
                    });
                toastr.error('Invalid', 'Error', toast_options);
                
            }
            else {
                toastr.error('Data not saved Please Contact Administrator', 'Danger', toast_options);
            }
    });

    }

});

search_advance_filter.on('click', function () {
    FAdvancedFilter.val("true");
    $('#f-employee-name').empty();
    $("#advance-filter").modal("hide");
    dataTable.ajax.reload();
    toastr.success('Search successfully', 'Success', toast_options);
});

reset_advance_filter.on('click', function () {
    FAdvancedFilter.val('');
    $('#f-employee-name').empty();
    $("#advance-filter").modal("hide");
    dataTable.ajax.reload();
    toastr.success('Data has been reset', 'Success', toast_options);
});

clear_advance_filter.on('click', function () {
    clear_advfilter();
    toastr.success('Clear successfully', 'Success', toast_options);
});

function clear_advfilter(){
    FIdNumber.val('');
    FTransactionCode.val('');
    FOriginalAmount.val('');
    FFinalAmount.val('');
    FAccountNumber.val('');
    FIncomingIn.val('');
    fdateField.clear();
    FEmployeeName.val('').trigger('change');
    FStatus.val('').trigger('change');
    FCreatedBy.val('').trigger('change');
}

$('#approved').click(function() {
    let final_amount = $("#final_amount").val().trim();
    let correctness_remarks = $("#correctness_remarks").val().trim();
    let status = 4; 
        if (final_amount === "") {  
        $("#amount_error").text("Please enter Amount");
        $("#remarks_error").text("");
        $(".input-group").addClass("has-error");
        event.preventDefault();
        } else {
        $("#amount_error").text("");
        $("#remarks_error").text("");
        $(".input-group").removeClass("has-error");
        tev_details(final_amount,correctness_remarks,status,clicked_id);
        }
    });



$('#employee-name').change(function() {
    var selectedOption = $(this).find('option:selected');
    var optionText = selectedOption.attr('id');
    if (optionText) {
        const employees = JSON.parse(localStorage.getItem('employees'));
        if (employees) {
            const selectedEmployeeId = selectedOption.attr('id');
            const selectedEmployee = employees.find(employee => employee.idNumber === selectedEmployeeId);
            if (selectedEmployee) {
                $('#id-number').val(selectedEmployee.idNumber);
                $('#acct-number').val(selectedEmployee.accNumber);
                $('#emp-name').val(selectedEmployee.firstName);
                $('#emp-middle').val(selectedEmployee.middleInitial);
                $('#emp-lastname').val(selectedEmployee.lastName);
                $('#division-user').val(selectedEmployee.division);
                $('#section-user').val(selectedEmployee.section);
                $('#contact-no').val(selectedEmployee.contact_no);
            }
        } else {
            console.log("No employee data found in local storage.");
        }
    }
});

$('#f-employee-name').change(function() {
    var selectedOptions = $(this).find('option:selected');
    selectedOptions.each(function() {
        var optionValue = $(this).val();
        if (employeeList.indexOf(optionValue) === -1) {
        employeeList.push(optionValue);
        }
    });
    $(this).find('option:not(:selected)').each(function() {
        var optionValue = $(this).val();
        var index = employeeList.indexOf(optionValue);
        if (index !== -1) {
        employeeList.splice(index, 1);
        }
    });

});
    
$('#returned').click(function() {
let final_amount = $("#final_amount").val().trim();
let correctness_remarks = $("#correctness_remarks").val().trim();
let status = 3;
    if (correctness_remarks === "") {
    $("#amount_error").text("");
    $("#remarks_error").text("Please enter Remarks for returned.");
    $(".input-group").addClass("has-error");
    event.preventDefault();
    } else {
    $("#remarks_error").text("");
    $(".input-group").removeClass("has-error");
    tev_details(final_amount,correctness_remarks,status,clicked_id);
    }
    
});

function tev_details(amount,remarks,status,emp_id){
    $.ajax({
        type: "POST",
        url: "{% url 'add-tev-details' %}",
        data:{
            final_amount: amount,
            remarks: remarks,
            status : status,
            transaction_id : emp_id
        }
        }).done(function(data){
        if (data.data == 'success') {
            $('#tevDetails').modal('hide');
            toastr.success('Successfully save', 'Success', toast_options);
            offCanvasEl.hide()
            dataTable.ajax.reload()
        } else {
            toastr.danger('Data not saved', 'Danger', toast_options);
        }
    });
}

//select 2
if (EmployeeName.length) {
    EmployeeName.wrap('<div class="position-relative"></div>')
    EmployeeName.select2({
        placeholder: 'Choose employee',
        dropdownParent: EmployeeName.parent(),
        allowClear: true,
    })
}

if (FEmployeeName.length) {
    FEmployeeName.wrap('<div class="position-relative"></div>')
    FEmployeeName.select2({
        placeholder: 'Choose employee',
        dropdownParent: FEmployeeName.parent(),
        allowClear: true,
    })
}

if (FStatus.length) {
    FStatus.wrap('<div class="position-relative"></div>')
    FStatus.select2({
        placeholder: 'Choose Status',
        dropdownParent: FStatus.parent(),
        allowClear: true,
    })
}

if (FCreatedBy.length) {
    FCreatedBy.wrap('<div class="position-relative"></div>')
    FCreatedBy.select2({
        placeholder: 'Choose Name',
        dropdownParent: FCreatedBy.parent(),
        allowClear: true,
    })
}
    
    //end select2

})
