from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///voting_system.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Database Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    is_admin = db.Column(db.Boolean, default=False)
    is_super_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Voter(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(20), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    department = db.Column(db.String(50))
    academic_year = db.Column(db.String(4))
    has_voted = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Election(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    start_time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=False)
    is_finished = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    positions = db.relationship('Position', backref='election', lazy=True, cascade='all, delete-orphan')

class Position(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    max_votes = db.Column(db.Integer, default=1)
    election_id = db.Column(db.Integer, db.ForeignKey('election.id'), nullable=False)
    nominees = db.relationship('Nominee', backref='position', lazy=True, cascade='all, delete-orphan')

class Partylist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    color = db.Column(db.String(7), default='#007bff')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    nominees = db.relationship('Nominee', backref='partylist', lazy=True)

class Nominee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    motto = db.Column(db.String(200))
    image_url = db.Column(db.String(200))
    position_id = db.Column(db.Integer, db.ForeignKey('position.id'), nullable=False)
    partylist_id = db.Column(db.Integer, db.ForeignKey('partylist.id'))
    vote_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Vote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    voter_id = db.Column(db.Integer, db.ForeignKey('voter.id'), nullable=False)
    nominee_id = db.Column(db.Integer, db.ForeignKey('nominee.id'), nullable=False)
    position_id = db.Column(db.Integer, db.ForeignKey('position.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    # Check if it's a regular admin user
    user = User.query.get(int(user_id))
    if user:
        return user
    # Check if it's a voter
    return Voter.query.get(int(user_id))

# Main Routes
@app.route('/')
def index():
    active_election = Election.query.filter_by(is_active=True).first()
    total_voters = Voter.query.count()
    total_nominees = Nominee.query.count()
    total_positions = Position.query.count()
    
    return render_template('index.html', 
                         active_election=active_election,
                         total_voters=total_voters,
                         total_nominees=total_nominees,
                         total_positions=total_positions)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login_type = request.form.get('login_type')
        
        if login_type == 'admin':
            username = request.form.get('username')
            password = request.form.get('password')
            
            user = User.query.filter_by(username=username).first()
            if user and check_password_hash(user.password_hash, password):
                login_user(user)
                flash('Login successful!', 'success')
                return redirect(url_for('admin_dashboard'))
            flash('Invalid admin credentials', 'error')
            
        elif login_type == 'voter':
            student_id = request.form.get('student_id')
            voter = Voter.query.filter_by(student_id=student_id).first()
            
            if voter:
                login_user(voter)
                flash('Login successful!', 'success')
                return redirect(url_for('voter_dashboard'))
            flash('Invalid student ID', 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

# Admin Routes
@app.route('/admin')
@login_required
def admin_dashboard():
    if not hasattr(current_user, 'is_admin') or not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('index'))
    
    elections = Election.query.all()
    active_election = Election.query.filter_by(is_active=True).first()
    total_voters = Voter.query.count()
    total_nominees = Nominee.query.count()
    total_positions = Position.query.count()
    votes_cast = Vote.query.count()
    
    return render_template('admin_dashboard.html', 
                         elections=elections, 
                         active_election=active_election,
                         total_voters=total_voters,
                         total_nominees=total_nominees,
                         total_positions=total_positions,
                         votes_cast=votes_cast)

@app.route('/admin/positions')
@login_required
def manage_positions():
    if not current_user.is_admin:
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    
    positions = Position.query.all()
    elections = Election.query.all()
    return render_template('manage_positions.html', positions=positions, elections=elections)

@app.route('/admin/partylists')
@login_required
def manage_partylists():
    if not current_user.is_admin:
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    
    partylists = Partylist.query.all()
    return render_template('manage_partylists.html', partylists=partylists)

@app.route('/admin/voters')
@login_required
def manage_voters():
    if not current_user.is_admin:
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    
    voters = Voter.query.all()
    return render_template('manage_voters.html', voters=voters)

@app.route('/admin/nominees')
@login_required
def manage_nominees():
    if not current_user.is_admin:
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    
    nominees = Nominee.query.all()
    positions = Position.query.all()
    partylists = Partylist.query.all()
    return render_template('manage_nominees.html', 
                         nominees=nominees, 
                         positions=positions, 
                         partylists=partylists)

# Voter Routes
@app.route('/voter')
@login_required
def voter_dashboard():
    if not hasattr(current_user, 'student_id'):
        flash('Access denied. Student access required.', 'error')
        return redirect(url_for('index'))
    
    active_election = Election.query.filter_by(is_active=True).first()
    positions = []
    if active_election:
        positions = Position.query.filter_by(election_id=active_election.id).all()
    
    return render_template('voter_dashboard.html', 
                         active_election=active_election,
                         positions=positions,
                         has_voted=current_user.has_voted)

@app.route('/results')
def view_results():
    active_election = Election.query.filter_by(is_active=True).first()
    finished_election = Election.query.filter_by(is_finished=True).first()
    
    election = active_election or finished_election
    results = {}
    
    if election:
        positions = Position.query.filter_by(election_id=election.id).all()
        for position in positions:
            nominees = Nominee.query.filter_by(position_id=position.id).order_by(Nominee.vote_count.desc()).all()
            results[position.title] = nominees
    
    total_votes = Vote.query.count()
    total_voters = Voter.query.count()
    turnout = (total_votes / total_voters * 100) if total_voters > 0 else 0
    
    return render_template('results.html', 
                         results=results, 
                         election=election,
                         total_votes=total_votes,
                         total_voters=total_voters,
                         turnout=round(turnout, 1))

# Election Control Routes
@app.route('/admin/election/start/<int:election_id>')
@login_required
def start_election(election_id):
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Access denied'})
    
    # Stop any currently active elections
    Election.query.update({Election.is_active: False})
    
    # Start the selected election
    election = Election.query.get(election_id)
    if election:
        election.is_active = True
        election.start_time = datetime.utcnow()
        db.session.commit()
        return jsonify({'success': True, 'message': 'Election started successfully'})
    
    return jsonify({'success': False, 'message': 'Election not found'})

@app.route('/admin/election/stop/<int:election_id>')
@login_required
def stop_election(election_id):
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Access denied'})
    
    election = Election.query.get(election_id)
    if election:
        election.is_active = False
        election.is_finished = True
        election.end_time = datetime.utcnow()
        db.session.commit()
        return jsonify({'success': True, 'message': 'Election stopped successfully'})
    
    return jsonify({'success': False, 'message': 'Election not found'})

# Voting Route
@app.route('/vote', methods=['POST'])
@login_required
def cast_vote():
    if not hasattr(current_user, 'student_id') or current_user.has_voted:
        return jsonify({'success': False, 'message': 'Access denied or already voted'})
    
    active_election = Election.query.filter_by(is_active=True).first()
    if not active_election:
        return jsonify({'success': False, 'message': 'No active election'})
    
    votes_data = request.json.get('votes', {})
    
    try:
        for position_id, nominee_id in votes_data.items():
            if nominee_id:  # Skip empty votes
                vote = Vote(
                    voter_id=current_user.id,
                    nominee_id=int(nominee_id),
                    position_id=int(position_id)
                )
                db.session.add(vote)
                
                # Update nominee vote count
                nominee = Nominee.query.get(int(nominee_id))
                if nominee:
                    nominee.vote_count += 1
        
        # Mark voter as having voted
        current_user.has_voted = True
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Vote cast successfully'})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Error casting vote'})

# Election Management Routes
@app.route('/admin/elections')
@login_required
def manage_elections():
    if not current_user.is_admin:
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    
    elections = Election.query.order_by(Election.created_at.desc()).all()
    return render_template('manage_elections.html', elections=elections)

# API Routes for CRUD operations
@app.route('/api/elections', methods=['POST'])
@login_required
def create_election():
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Access denied'})
    
    data = request.json
    election = Election(
        title=data['title'],
        description=data.get('description', ''),
        is_active=False,
        is_finished=False
    )
    db.session.add(election)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Election created successfully', 'election_id': election.id})

@app.route('/api/nominees', methods=['POST'])
@login_required
def create_nominee():
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Access denied'})
    
    data = request.json
    nominee = Nominee(
        name=data['name'],
        description=data.get('description', ''),
        motto=data.get('motto', ''),
        position_id=data['position_id'],
        partylist_id=data.get('partylist_id'),
        image_url=data.get('image_url', '')
    )
    db.session.add(nominee)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Nominee created successfully'})

@app.route('/api/positions', methods=['POST'])
@login_required
def create_position():
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Access denied'})
    
    data = request.json
    # Get the first available election or create one
    election = Election.query.first()
    if not election:
        election = Election(title='Default Election', description='Main election')
        db.session.add(election)
        db.session.commit()
    
    position = Position(
        title=data['title'],
        description=data.get('description', ''),
        max_votes=data.get('max_votes', 1),
        election_id=election.id
    )
    db.session.add(position)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Position created successfully'})

@app.route('/api/partylists', methods=['POST'])
@login_required
def create_partylist():
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Access denied'})
    
    data = request.json
    partylist = Partylist(
        name=data['name'],
        description=data.get('description', ''),
        color=data.get('color', '#007bff')
    )
    db.session.add(partylist)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Partylist created successfully'})

@app.route('/api/voters', methods=['POST'])
@login_required
def create_voter():
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Access denied'})
    
    data = request.json
    voter = Voter(
        student_id=data['student_id'],
        name=data['name'],
        email=data['email'],
        department=data.get('department', ''),
        academic_year=data.get('academic_year', '')
    )
    db.session.add(voter)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Voter created successfully'})

# Utility Routes
@app.route('/api/stats')
@login_required
def get_stats():
    if not current_user.is_admin:
        return jsonify({'error': 'Access denied'})
    
    stats = {
        'total_voters': Voter.query.count(),
        'total_nominees': Nominee.query.count(),
        'total_votes': Vote.query.count(),
        'total_positions': Position.query.count(),
        'total_partylists': Partylist.query.count(),
        'voters_who_voted': Voter.query.filter_by(has_voted=True).count(),
        'turnout_percentage': 0
    }
    
    if stats['total_voters'] > 0:
        stats['turnout_percentage'] = round((stats['voters_who_voted'] / stats['total_voters']) * 100, 1)
    
    return jsonify(stats)

# Error Handlers
@app.errorhandler(404)
def not_found(error):
    return render_template('error.html', 
                         error_code=404, 
                         error_message="Page not found"), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('error.html', 
                         error_code=500, 
                         error_message="Internal server error"), 500

# Initialize database and create sample data
def init_db():
    with app.app_context():
        db.create_all()
        
        # Create super admin if not exists
        if not User.query.filter_by(username='admin').first():
            admin = User(
                username='admin',
                email='admin@voting.com',
                password_hash=generate_password_hash('admin123'),
                is_admin=True,
                is_super_admin=True
            )
            db.session.add(admin)
        
        # Create sample election
        if not Election.query.first():
            election = Election(
                title='Student Government Election 2025',
                description='Annual student government election for all positions'
            )
            db.session.add(election)
            db.session.commit()
            
            # Create sample positions
            positions_data = [
                {'title': 'President', 'description': 'Student Body President'},
                {'title': 'Vice President', 'description': 'Student Body Vice President'},
                {'title': 'Secretary', 'description': 'Student Government Secretary'},
                {'title': 'Treasurer', 'description': 'Student Government Treasurer'}
            ]
            
            for pos_data in positions_data:
                position = Position(
                    title=pos_data['title'],
                    description=pos_data['description'],
                    election_id=election.id
                )
                db.session.add(position)
            
            db.session.commit()
            
            # Create sample partylists
            if not Partylist.query.first():
                partylists = [
                    {'name': 'Progressive Party', 'description': 'Forward-thinking student leadership', 'color': '#667eea'},
                    {'name': 'Unity Coalition', 'description': 'Bringing students together', 'color': '#764ba2'},
                    {'name': 'Independent', 'description': 'Independent candidates', 'color': '#51cf66'}
                ]
                
                for party_data in partylists:
                    party = Partylist(
                        name=party_data['name'],
                        description=party_data['description'],
                        color=party_data['color']
                    )
                    db.session.add(party)
                
                db.session.commit()
            
            # Create sample nominees
            if not Nominee.query.first():
                positions = Position.query.all()
                partylists = Partylist.query.all()
                
                nominees_data = [
                    {
                        'name': 'Sarah Johnson',
                        'motto': 'Together we achieve more',
                        'description': 'Dedicated advocate for student rights with innovative ideas for campus improvement. Sarah has 3 years of experience in student government and has successfully led initiatives for mental health support and academic reform.',
                        'position': 'President',
                        'party': 'Progressive Party'
                    },
                    {
                        'name': 'John Smith',
                        'motto': 'Leading with integrity and vision',
                        'description': 'Experienced student leader with a passion for improving campus life and academic excellence. John focuses on infrastructure improvements, student safety, and creating more opportunities for student engagement.',
                        'position': 'President',
                        'party': 'Unity Coalition'
                    },
                    {
                        'name': 'Mike Davis',
                        'motto': 'Supporting excellence in everything',
                        'description': 'Committed to fostering collaboration and enhancing student services. Mike brings fresh perspectives on technology integration and student wellness programs to create a more connected campus community.',
                        'position': 'Vice President',
                        'party': 'Independent'
                    },
                    {
                        'name': 'Ania Wilson',
                        'motto': 'Bridging communities, building futures',
                        'description': 'Passionate about diversity and inclusion initiatives. Ania has organized multiple successful campus events and advocates for sustainable practices and environmental consciousness on campus.',
                        'position': 'Vice President',
                        'party': 'Progressive Party'
                    }
                ]
                
                for nominee_data in nominees_data:
                    position = next((p for p in positions if p.title == nominee_data['position']), None)
                    party = next((p for p in partylists if p.name == nominee_data['party']), None)
                    
                    if position:
                        nominee = Nominee(
                            name=nominee_data['name'],
                            motto=nominee_data['motto'],
                            description=nominee_data['description'],
                            position_id=position.id,
                            partylist_id=party.id if party else None
                        )
                        db.session.add(nominee)
                
                db.session.commit()
        
        # Create sample voters
        if not Voter.query.filter_by(student_id='2025001').first():
            voters_data = [
                {'student_id': '2025001', 'name': 'John Doe', 'email': 'john.doe@student.edu', 'department': 'CS', 'academic_year': '2025'},
                {'student_id': '2025002', 'name': 'Jane Smith', 'email': 'jane.smith@student.edu', 'department': 'ENG', 'academic_year': '2024'},
                {'student_id': '2025003', 'name': 'Bob Wilson', 'email': 'bob.wilson@student.edu', 'department': 'BUS', 'academic_year': '2023'}
            ]
            
            for voter_data in voters_data:
                voter = Voter(
                    student_id=voter_data['student_id'],
                    name=voter_data['name'],
                    email=voter_data['email'],
                    department=voter_data['department'],
                    academic_year=voter_data['academic_year']
                )
                db.session.add(voter)
            
            db.session.commit()

if __name__ == '__main__':
    init_db()
    print("🗳️  Electronic Voting System Starting...")
    print("📊 Admin Login: username='admin', password='admin123'")
    print("🎓 Student Login: student_id='2025001'")
    print("🌐 Access at: http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)