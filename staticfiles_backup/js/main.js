// Enable tooltips
var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
    return new bootstrap.Tooltip(tooltipTriggerEl)
});

// Enable popovers
var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'))
var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
    return new bootstrap.Popover(popoverTriggerEl)
});

// Auto-hide alerts after 5 seconds
setTimeout(function() {
    var alerts = document.querySelectorAll('.alert');
    alerts.forEach(function(alert) {
        var bsAlert = new bootstrap.Alert(alert);
        bsAlert.close();
    });
}, 5000);

// Form validation
(function() {
    'use strict'
    var forms = document.querySelectorAll('.needs-validation')
    Array.prototype.slice.call(forms)
        .forEach(function(form) {
            form.addEventListener('submit', function(event) {
                if (!form.checkValidity()) {
                    event.preventDefault()
                    event.stopPropagation()
                }
                form.classList.add('was-validated')
            }, false)
        })
})()

// Search functionality
function searchTable(inputId, tableId) {
    var input = document.getElementById(inputId);
    var filter = input.value.toUpperCase();
    var table = document.getElementById(tableId);
    var tr = table.getElementsByTagName("tr");

    for (var i = 0; i < tr.length; i++) {
        var td = tr[i].getElementsByTagName("td");
        var found = false;
        for (var j = 0; j < td.length; j++) {
            if (td[j]) {
                var txtValue = td[j].textContent || td[j].innerText;
                if (txtValue.toUpperCase().indexOf(filter) > -1) {
                    found = true;
                    break;
                }
            }
        }
        if (found) {
            tr[i].style.display = "";
        } else {
            tr[i].style.display = "none";
        }
    }
}

// Export to Excel
function exportToExcel(tableId, filename) {
    var table = document.getElementById(tableId);
    var html = table.outerHTML;
    var url = 'data:application/vnd.ms-excel,' + escape(html);
    var link = document.createElement("a");
    link.download = filename + ".xls";
    link.href = url;
    link.click();
}

// Print function
function printTable(tableId) {
    var printContent = document.getElementById(tableId).outerHTML;
    var originalContent = document.body.innerHTML;
    document.body.innerHTML = printContent;
    window.print();
    document.body.innerHTML = originalContent;
    location.reload();
}

// Number formatting
function formatNumber(num) {
    return num.toString().replace(/(\d)(?=(\d{3})+(?!\d))/g, 'UGX1,')
}

// Date formatting
function formatDate(date) {
    var d = new Date(date),
        month = '' + (d.getMonth() + 1),
        day = '' + d.getDate(),
        year = d.getFullYear();

    if (month.length < 2) month = '0' + month;
    if (day.length < 2) day = '0' + day;

    return [year, month, day].join('-');
}

// Confirm action
function confirmAction(message) {
    return confirm(message || 'Are you sure?');
}

// Loading spinner
function showSpinner() {
    var spinner = document.createElement('div');
    spinner.className = 'spinner-overlay';
    spinner.innerHTML = '<div class="spinner-border text-primary" role="status"><span class="visually-hidden">Loading...</span></div>';
    document.body.appendChild(spinner);
}

function hideSpinner() {
    var spinner = document.querySelector('.spinner-overlay');
    if (spinner) {
        spinner.remove();
    }
}

// Add spinner CSS
var style = document.createElement('style');
style.innerHTML = `
    .spinner-overlay {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(255,255,255,0.8);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 9999;
    }
`;
document.head.appendChild(style);