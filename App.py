import os
import logging
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import random
from datetime import datetime

# Initialize Flask app
app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')  # Change in production
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', '').replace(
    'postgres://', 'postgresql://') or 'sqlite:///lottery.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['PREFERRED_URL_SCHEME'] = 'https'  # Force HTTPS in production

# Initialize database
db = SQLAlchemy(app)

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    phone = db.Column(db.String(20), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    balance = db.Column(db.Integer, default=0)
    tickets = db.relationship('Ticket', backref='user', lazy=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Ticket(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    number = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    lottery_id = db.Column(db.Integer, db.ForeignKey('lottery.id'))
    purchased_at = db.Column(db.DateTime, default=datetime.utcnow)

class Lottery(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    is_active = db.Column(db.Boolean, default=True)
    winning_number = db.Column(db.Integer)
    winner_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    prize_pool = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    tickets = db.relationship('Ticket', backref='lottery', lazy=True)

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    amount = db.Column(db.Integer)
    transaction_type = db.Column(db.String(20))  # 'deposit' or 'withdrawal'
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Helper Functions
def get_current_lottery():
    lottery = Lottery.query.filter_by(is_active=True).first()
    if not lottery:
        lottery = Lottery(is_active=True)
        db.session.add(lottery)
        db.session.commit()
    return lottery

def check_tickets_available():
    return 50 - Ticket.query.filter_by(lottery_id=get_current_lottery().id).count()

def draw_winner():
    lottery = get_current_lottery()
    winning_number = random.randint(1, 50)
    lottery.winning_number = winning_number
    
    winning_ticket = Ticket.query.filter_by(
        number=winning_number, 
        lottery_id=lottery.id
    ).first()
    
    if winning_ticket:
        winner = User.query.get(winning_ticket.user_id)
        winner_prize = int(lottery.prize_pool * 0.9)
        winner.balance += winner_prize
        lottery.winner_id = winner.id
        lottery.is_active = False
        lottery.completed_at = datetime.utcnow()
        db.session.commit()
        
        # Start new lottery
        new_lottery = Lottery(is_active=True)
        db.session.add(new_lottery)
        db.session.commit()
        
        return {
            'winner': winner.username,
            'ticket_number': winning_number,
            'prize': winner_prize
        }
    return None

# API Endpoints
@app.route('/api/auth/status')
def auth_status():
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        return jsonify({
            'authenticated': True,
            'user': {
                'id': user.id,
                'username': user.username,
                'phone': user.phone,
                'balance': user.balance
            }
        })
    return jsonify({'authenticated': False})

@app.route('/api/auth/register', methods=['POST'])
def api_register():
    data = request.get_json()
    required_fields = ['username', 'phone', 'password']
    if not all(field in data for field in required_fields):
        return jsonify({'success': False, 'message': 'Missing required fields'}), 400
    
    if User.query.filter((User.username == data['username']) | (User.phone == data['phone'])).first():
        return jsonify({'success': False, 'message': 'Username or phone already exists'}), 400
    
    hashed_password = generate_password_hash(data['password'])
    new_user = User(
        username=data['username'],
        phone=data['phone'],
        password_hash=hashed_password
    )
    db.session.add(new_user)
    db.session.commit()
    
    session['user_id'] = new_user.id
    return jsonify({
        'success': True,
        'user': {
            'id': new_user.id,
            'username': new_user.username,
            'balance': new_user.balance
        }
    })

@app.route('/api/auth/login', methods=['POST'])
def api_login():
    data = request.get_json()
    if not all(field in data for field in ['phone', 'password']):
        return jsonify({'success': False, 'message': 'Missing phone or password'}), 400
    
    user = User.query.filter_by(phone=data['phone']).first()
    if user and check_password_hash(user.password_hash, data['password']):
        session['user_id'] = user.id
        return jsonify({
            'success': True,
            'user': {
                'id': user.id,
                'username': user.username,
                'balance': user.balance
            }
        })
    return jsonify({'success': False, 'message': 'Invalid credentials'}), 401

@app.route('/api/auth/logout', methods=['POST'])
def api_logout():
    session.pop('user_id', None)
    return jsonify({'success': True})

@app.route('/api/lottery/status')
def lottery_status():
    lottery = get_current_lottery()
    tickets_sold = Ticket.query.filter_by(lottery_id=lottery.id).count()
    user_tickets = []
    
    if 'user_id' in session:
        user_tickets = [t.number for t in Ticket.query.filter_by(
            user_id=session['user_id'],
            lottery_id=lottery.id
        )]
    
    return jsonify({
        'tickets_sold': tickets_sold,
        'tickets_available': 50 - tickets_sold,
        'prize_pool': lottery.prize_pool,
        'user_tickets': user_tickets,
        'is_active': lottery.is_active,
        'winning_number': lottery.winning_number,
        'winner_id': lottery.winner_id
    })

@app.route('/api/lottery/buy', methods=['POST'])
def api_buy_tickets():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not authenticated'}), 401
    
    data = request.get_json()
    quantity = data.get('quantity', 1)
    user = User.query.get(session['user_id'])
    lottery = get_current_lottery()
    
    # Validation checks
    if quantity < 1 or quantity > 3:
        return jsonify({'success': False, 'message': 'Invalid quantity (1-3 only)'}), 400
    
    if user.balance < quantity * 50:
        return jsonify({'success': False, 'message': 'Insufficient funds'}), 400
    
    user_tickets = Ticket.query.filter_by(user_id=user.id, lottery_id=lottery.id).count()
    if user_tickets + quantity > 3:
        return jsonify({'success': False, 'message': 'Maximum 3 tickets per user'}), 400
    
    available_tickets = 50 - Ticket.query.filter_by(lottery_id=lottery.id).count()
    if quantity > available_tickets:
        return jsonify({'success': False, 'message': 'Not enough tickets remaining'}), 400
    
    # Process purchase
    user.balance -= quantity * 50
    lottery.prize_pool += quantity * 50
    
    # Assign tickets
    available_numbers = set(range(1, 51)) - {t.number for t in lottery.tickets}
    ticket_numbers = []
    for _ in range(quantity):
        number = available_numbers.pop()
        ticket_numbers.append(number)
        db.session.add(Ticket(
            number=number,
            user_id=user.id,
            lottery_id=lottery.id
        ))
    
    db.session.commit()
    
    # Check if lottery should end
    if Ticket.query.filter_by(lottery_id=lottery.id).count() >= 50:
        result = draw_winner()
        return jsonify({
            'success': True,
            'message': f"Lottery complete! Winner: {result['winner']} (Ticket #{result['ticket_number']})" if result else 'No winner this round',
            'ticket_numbers': ticket_numbers,
            'game_completed': True
        })
    
    return jsonify({
        'success': True,
        'message': 'Tickets purchased successfully',
        'ticket_numbers': ticket_numbers
    })

# Template Routes
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/<path>')
def serve_page(path):
    valid_pages = {
        'login': 'auth/login.html',
        'register': 'auth/register.html',
        'buy': 'lottery/buy.html',
        'my_tickets': 'lottery/my_tickets.html',
        'withdraw': 'lottery/withdraw.html'
    }
    if path in valid_pages:
        return render_template(valid_pages[path])
    return redirect(url_for('home'))

# Database initialization
@app.before_first_request
def initialize_database():
    db.create_all()
    if not Lottery.query.first():
        db.session.add(Lottery(is_active=True))
        db.session.commit()

# Configure logging
if __name__ != '__main__':
    gunicorn_logger = logging.getLogger('gunicorn.error')
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)

if __name__ == '__main__':
    app.run(debug=os.environ.get('FLASK_DEBUG', 'False') == 'True')