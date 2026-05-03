// Main application JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Notification dropdown functionality
    const notificationBtn = document.getElementById('notificationBtn');
    const notificationDropdown = document.getElementById('notificationDropdown');

    if (notificationBtn && notificationDropdown) {
        notificationBtn.addEventListener('click', function(e) {
            e.stopPropagation();
            notificationDropdown.classList.toggle('active');
        });

        // Close dropdown when clicking outside
        document.addEventListener('click', function() {
            notificationDropdown.classList.remove('active');
        });

        // Prevent close when clicking inside dropdown
        notificationDropdown.addEventListener('click', function(e) {
            e.stopPropagation();
        });
    }

    // Auto-hide alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            alert.style.transition = 'opacity 0.5s';
            alert.style.opacity = '0';
            setTimeout(function() {
                alert.remove();
            }, 500);
        }, 5000);
    });

    // Form validation enhancements
    const forms = document.querySelectorAll('form');
    forms.forEach(function(form) {
        form.addEventListener('submit', function(e) {
            const requiredFields = form.querySelectorAll('[required]');
            let isValid = true;

            requiredFields.forEach(function(field) {
                if (!field.value.trim()) {
                    isValid = false;
                    field.classList.add('is-invalid');
                    field.addEventListener('input', function() {
                        field.classList.remove('is-invalid');
                    }, { once: true });
                }
            });

            if (!isValid) {
                e.preventDefault();
                flashMessage('Proszę wypełnić wszystkie wymagane pola.', 'error');
            }
        });
    });

    // Quick status buttons (confirm before marking as completed)
    const statusButtons = document.querySelectorAll('.status-btn-complete');
    statusButtons.forEach(function(btn) {
        btn.addEventListener('click', function(e) {
            if (!confirm('Czy na pewno chcesz oznaczyć to zadanie jako zakończone?')) {
                e.preventDefault();
                e.stopPropagation();
            }
        });
    });

    // Enhanced date inputs
    const dateInputs = document.querySelectorAll('input[type="date"]');
    dateInputs.forEach(function(input) {
        // Set max date to today for due_date fields
        if (input.name === 'due_date' || input.id === 'due_date') {
            const today = new Date().toISOString().split('T')[0];
            input.min = today;
        }
    });

    // Skills grid color coding
    const skillCheckboxes = document.querySelectorAll('.skill-checkbox input[type="checkbox"]');
    skillCheckboxes.forEach(function(checkbox) {
        const label = checkbox.nextElementSibling;
        if (checkbox.checked) {
            label.style.fontWeight = 'bold';
            label.style.color = '#2c3e50';
        }

        checkbox.addEventListener('change', function() {
            if (this.checked) {
                label.style.fontWeight = 'bold';
                label.style.color = '#2c3e50';
            } else {
                label.style.fontWeight = 'normal';
                label.style.color = '';
            }
        });
    });

    // Mobile menu toggle (if needed in future)
    const navBrand = document.querySelector('.nav-brand');
    if (navBrand) {
        navBrand.addEventListener('click', function(e) {
            // Could be expanded for mobile menu
        });
    }

    // Progress bar animations
    const progressBars = document.querySelectorAll('.progress-fill');
    progressBars.forEach(function(bar) {
        const width = bar.style.width;
        bar.style.width = '0';
        setTimeout(function() {
            bar.style.transition = 'width 1s ease-out';
            bar.style.width = width;
        }, 100);
    });

    // Table row hover effects for actions
    const tableRows = document.querySelectorAll('.table tbody tr');
    tableRows.forEach(function(row) {
        const actionsCell = row.querySelector('td:last-child');
        if (actionsCell) {
            row.addEventListener('mouseenter', function() {
                actionsCell.querySelectorAll('.btn').forEach(function(btn) {
                    btn.style.opacity = '1';
                });
            });

            row.addEventListener('mouseleave', function() {
                actionsCell.querySelectorAll('.btn').forEach(function(btn) {
                    btn.style.opacity = '0.7';
                });
            });
        }
    });

    // Real-time search (debounced)
    const searchInput = document.querySelector('input[name="search"]');
    if (searchInput) {
        let timeout;
        searchInput.addEventListener('input', function(e) {
            clearTimeout(timeout);
            timeout = setTimeout(function() {
                if (searchInput.value.length > 2 || searchInput.value.length === 0) {
                    e.target.form.submit();
                }
            }, 500);
        });
    }

    console.log('KIT Application initialized');
});

// Helper function to show flash messages programmatically
function flashMessage(message, category = 'info') {
    const alertsContainer = document.querySelector('.main-content');
    if (!alertsContainer) return;

    const alert = document.createElement('div');
    alert.className = `alert alert-${category}`;
    alert.textContent = message;
    alert.style.cssText = 'position: fixed; top: 70px; right: 20px; z-index: 9999; min-width: 300px;';

    alertsContainer.insertBefore(alert, alertsContainer.firstChild);

    setTimeout(function() {
        alert.style.transition = 'opacity 0.5s';
        alert.style.opacity = '0';
        setTimeout(function() { alert.remove(); }, 500);
    }, 3000);
}

// Utility function to format dates
function formatDate(dateString) {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleDateString('pl-PL');
}

// Export for use in other scripts if needed
window.KIT = {
    flashMessage: flashMessage,
    formatDate: formatDate
};