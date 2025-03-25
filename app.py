from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
import os
import json
from datetime import datetime
from models import db, Candidate, JobPosting, Application, AnalyticsReport
from ai_processor import ResumeProcessor, JobMatcher
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', os.urandom(24))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///resume_screening.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize extensions
db.init_app(app)

# Initialize AI processors
resume_processor = ResumeProcessor()
job_matcher = JobMatcher()

# Allowed file extensions
ALLOWED_EXTENSIONS = {'pdf', 'docx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Here you would typically validate the login credentials
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    # Get statistics for dashboard
    stats = {
        'total_candidates': Candidate.query.count(),
        'new_applications': Application.query.filter_by(status='pending').count(),
        'active_jobs': JobPosting.query.filter_by(status='active').count(),
        'successful_matches': Application.query.filter_by(status='matched').count()
    }
    return render_template('dashboard.html', stats=stats)

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        if 'resume' not in request.files:
            flash('No file selected', 'error')
            return redirect(request.url)
        
        file = request.files['resume']
        if file.filename == '':
            flash('No file selected', 'error')
            return redirect(request.url)
        
        # Validate required fields
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        
        if not all([name, email, phone]):
            flash('Please fill in all required fields', 'error')
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            try:
                # Save the file
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                
                # Process the resume
                analysis = resume_processor.analyze_resume_sync(filepath)
                
                if analysis:
                    # Create new candidate
                    candidate = Candidate(
                        name=name,
                        email=email,
                        phone=phone,
                        resume_path=filepath,
                        skills=analysis.get('skills', []),
                        experience=analysis.get('experience', []),
                        education=analysis.get('education', [])
                    )
                    
                    # Check if email already exists
                    existing_candidate = Candidate.query.filter_by(email=email).first()
                    if existing_candidate:
                        flash('A candidate with this email already exists', 'error')
                        return redirect(request.url)

                    db.session.add(candidate)
                    db.session.commit()
                    
                    # Match with active job postings
                    active_jobs = JobPosting.query.filter_by(status='active').all()
                    matches = []
                    
                    for job in active_jobs:
                        match_score = job_matcher.calculate_match_score_sync(
                            analysis,
                            json.loads(job.requirements)
                        )
                        
                        application = Application(
                            candidate_id=candidate.id,
                            job_posting_id=job.id,
                            match_score=match_score['total_score'],
                            ai_feedback=match_score['ai_analysis'],
                            status='pending'
                        )
                        
                        db.session.add(application)
                        matches.append({
                            'job_title': job.title,
                            'match_score': match_score['total_score'],
                            'analysis': match_score['ai_analysis']
                        })
                    
                    db.session.commit()
                    
                    # Return JSON response for AJAX handling
                    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                        return jsonify({
                            'status': 'success',
                            'message': 'Resume uploaded and analyzed successfully',
                            'matches': matches
                        })
                    
                    flash('Resume uploaded and analyzed successfully', 'success')
                    return redirect(url_for('dashboard'))
                else:
                    flash('Failed to analyze resume', 'error')
            
            except Exception as e:
                app.logger.error(f'Error processing resume: {str(e)}')
                flash(f'Error processing resume: {str(e)}', 'error')
                return redirect(request.url)
        else:
            flash('Invalid file type. Please upload PDF or DOCX files only.', 'error')
            return redirect(request.url)
    
    return render_template('upload.html')

@app.route('/jobs')
def jobs():
    # Get all job postings with their match counts
    jobs = JobPosting.query.all()
    job_data = []
    
    for job in jobs:
        applications = Application.query.filter_by(job_posting_id=job.id).all()
        match_count = len(applications)
        avg_score = sum(app.match_score for app in applications) / match_count if match_count > 0 else 0
        
        job_data.append({
            'job': job,
            'match_count': match_count,
            'avg_score': avg_score
        })
    
    return render_template('jobs.html', jobs=job_data)

@app.route('/jobs/<int:job_id>/matches')
def job_matches(job_id):
    job = JobPosting.query.get_or_404(job_id)
    applications = Application.query.filter_by(job_posting_id=job_id)\
        .order_by(Application.match_score.desc()).all()
    
    matches = []
    for app in applications:
        candidate = Candidate.query.get(app.candidate_id)
        matches.append({
            'candidate': candidate,
            'match_score': app.match_score,
            'feedback': app.ai_feedback
        })
    
    return jsonify({
        'job': {
            'title': job.title,
            'department': job.department,
            'matches': matches
        }
    })

@app.route('/report')
def report():
    # Generate analytics report
    total_candidates = Candidate.query.count()
    total_jobs = JobPosting.query.count()
    total_applications = Application.query.count()
    
    # Skills distribution
    all_skills = []
    candidates = Candidate.query.all()
    for candidate in candidates:
        all_skills.extend(candidate.skills or [])
    
    skills_dist = {}
    for skill in all_skills:
        skills_dist[skill] = skills_dist.get(skill, 0) + 1
    
    # Department distribution
    dept_dist = {}
    jobs = JobPosting.query.all()
    for job in jobs:
        dept_dist[job.department] = dept_dist.get(job.department, 0) + 1
    
    report_data = {
        'total_candidates': total_candidates,
        'total_jobs': total_jobs,
        'total_applications': total_applications,
        'skills_distribution': skills_dist,
        'department_distribution': dept_dist
    }
    
    return render_template('report.html', report=report_data)

@app.route('/api/jobs', methods=['POST'])
def create_job():
    data = request.json
    
    job = JobPosting(
        title=data['title'],
        department=data['department'],
        location=data['location'],
        description=data['description'],
        requirements=data['requirements'],
        salary_range=data.get('salary_range', '')
    )
    
    db.session.add(job)
    db.session.commit()
    
    return jsonify({'message': 'Job posting created successfully', 'id': job.id})

@app.cli.command("init-db")
def init_db():
    """Initialize the database."""
    db.create_all()
    print('Database initialized.')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=8000, debug=True)