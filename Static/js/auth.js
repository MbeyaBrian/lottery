// Authentication functions
function checkAuthStatus() {
    $.get('/api/auth/status', function(response) {
        if (response.authenticated) {
            updateUserUI(response.user);
            showPage('home');
        }
    }).fail(showLoggedOutState);
}

function registerUser() {
    const formData = {
        username: $('#register-username').val(),
        phone: $('#register-phone').val(),
        password: $('#register-password').val(),
        confirm_password: $('#register-confirm').val()
    };

    if (formData.password !== formData.confirm_password) {
        showError('Passwords do not match', '#register-error');
        return;
    }

    $.post('/api/auth/register', formData, function(response) {
        if (response.success) {
            updateUserUI(response.user);
            showPage('home');
        } else {
            showError(response.message, '#register-error');
        }
    });
}

function loginUser() {
    const credentials = {
        phone: $('#login-phone').val(),
        password: $('#login-password').val()
    };

    $.post('/api/auth/login', credentials, function(response) {
        if (response.success) {
            updateUserUI(response.user);
            showPage('home');
        } else {
            showError(response.message, '#login-error');
        }
    });
}

function logoutUser() {
    $.post('/api/auth/logout', function() {
        showLoggedOutState();
        showPage('home');
    });
}

// UI Update functions
function updateUserUI(user) {
    $('#user-balance').text(user.balance + ' KES').show();
    $('#login-btn, #register-btn').hide();
    $('#logout-btn').show();
    gameState.userBalance = user.balance;
}

function showLoggedOutState() {
    $('#login-btn, #register-btn').show();
    $('#logout-btn, #user-balance').hide();
}

$(document).ready(function() {
    checkAuthStatus();
});