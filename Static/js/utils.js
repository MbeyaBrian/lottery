function showPage(page) {
    $('.page').removeClass('active');
    $(`#${page}-page`).addClass('active');
    window.scrollTo(0, 0);
}

function formatCurrency(amount) {
    return amount.toLocaleString('en-KE', { style: 'currency', currency: 'KES' });
}

function showLoading(element) {
    $(element).show();
}

function hideLoading(element) {
    $(element).hide();
}

function showError(message, element) {
    $(element).text(message).show().delay(5000).fadeOut();
}