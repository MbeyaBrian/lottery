function addFunds(amount) {
    if (!checkAuth()) return;

    $.post('/api/payments/deposit', { amount: amount }, function(response) {
        if (response.success) {
            updateUserBalance(response.new_balance);
            showSuccess('Funds added successfully');
        } else {
            showError(response.message);
        }
    });
}

function withdrawFunds() {
    const amount = $('#withdraw-amount').val();
    const phone = $('#withdraw-phone').val();

    if (!validateMpesaNumber(phone)) {
        showError('Invalid M-Pesa number', '#withdraw-error');
        return;
    }

    $.post('/api/payments/withdraw', { 
        amount: amount,
        phone: phone 
    }, function(response) {
        if (response.success) {
            updateUserBalance(response.new_balance);
            showSuccess('Withdrawal processing');
        } else {
            showError(response.message, '#withdraw-error');
        }
    });
}

function validateMpesaNumber(phone) {
    return /^254\d{9}$/.test(phone);
}

// Utility functions
function showSuccess(message) {
    alert(message); // Replace with toast notification
}

function showError(message, element = null) {
    if (element) {
        $(element).text(message).show();
    } else {
        alert(message); // Replace with toast notification
    }
}

function checkAuth() {
    if (!gameState.user) {
        showPage('login');
        return false;
    }
    return true;
}