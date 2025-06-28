const gameState = {
    ticketsSold: 0,
    totalTickets: 50,
    ticketPrice: 50,
    userTickets: [],
    userBalance: 0
};

function fetchGameData() {
    $.get('/api/lottery/status', function(data) {
        gameState.ticketsSold = data.tickets_sold;
        gameState.userTickets = data.user_tickets || [];
        updateGameDisplay();
    });
}

function buyTickets(quantity) {
    if (!checkAuth()) return;

    $.post('/api/lottery/buy', { quantity: quantity }, function(response) {
        if (response.success) {
            if (response.game_completed) {
                showWinnerBanner(response.message);
                setTimeout(fetchGameData, 3000);
            } else {
                showSuccess(response.message);
                fetchGameData();
            }
        } else {
            showError(response.message);
        }
    });
}

function updateGameDisplay() {
    $('#tickets-sold').text(gameState.ticketsSold);
    $('#tickets-remaining').text(gameState.totalTickets - gameState.ticketsSold);
    $('#current-pot').text((gameState.ticketsSold * gameState.ticketPrice) + ' KES');
    
    const progressPercent = (gameState.ticketsSold / gameState.totalTickets) * 100;
    $('#tickets-progress').css('width', `${progressPercent}%`);
    
    updateTicketDisplay();
}

function updateTicketDisplay() {
    const container = $('#ticket-numbers');
    container.empty();
    
    if (gameState.userTickets.length > 0) {
        gameState.userTickets.forEach(ticket => {
            container.append(`<span class="ticket">${ticket}</span>`);
        });
    }
}

$(document).ready(fetchGameData);