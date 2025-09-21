from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_cors import CORS
import os
import json
import uuid
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
import io
import re
import tempfile
import shutil
from typing import Dict, List, Any, Optional
from groq import Groq
import numpy as np
import pdfplumber
from docx import Document
import psycopg2
import langchain
from psycopg2.extras import RealDictCursor
from supabase import create_client, Client

# Environment
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'your-secret-key-here')
CORS(app)

# Initialize Supabase client
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_ANON_KEY = os.getenv('SUPABASE_ANON_KEY')
# SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

# if not all([SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_SERVICE_ROLE_KEY]):
#     raise ValueError("Missing required Supabase environment variables")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

# Initialize AI models
LLM_PROVIDER = os.getenv('LLM_PROVIDER', 'groq')
GROQ_API_KEY = os.getenv('GROQ_API_KEY')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# Initialize LLM
if LLM_PROVIDER == 'groq' and GROQ_API_KEY:
    groq_client = Groq(api_key=GROQ_API_KEY)
    gemini_client = None
elif LLM_PROVIDER == 'gemini' and GEMINI_API_KEY:
    # import google.generativeai as genai
    # genai.configure(api_key=GEMINI_API_KEY)
    # gemini_client = genai.GenerativeModel('gemini-pro')
    groq_client = None
else:
    raise ValueError("Invalid LLM provider or missing API key")

# Initialize sentence transformer for embeddings
# sentence_model = SentenceTransformer('all-MiniLM-L6-v2')

# SMTP Configuration
SMTP_HOST = os.getenv('SMTP_HOST')
SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
SMTP_USER = os.getenv('SMTP_USER')
SMTP_PASS = os.getenv('SMTP_PASS')

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def supabase_upload(file_bytes: bytes, path: str, bucket: str = 'resume') -> str:
    """Upload file to Supabase storage bucket"""
    try:
        result = supabase.storage.from_(bucket).upload(path, file_bytes)
        if hasattr(result, 'error') and result.error:
            raise Exception(f"Upload failed: {result.error}")
        return path
    except Exception as e:
        raise Exception(f"Failed to upload file: {str(e)}")

def supabase_signed_url(path: str, expires_in: int = 3600, bucket: str = 'resume') -> str:
    """Generate signed URL for file access"""
    try:
        result = supabase.storage.from_(bucket).create_signed_url(path, expires_in)
        if hasattr(result, 'error') and result.error:
            raise Exception(f"Failed to create signed URL: {result.error}")
        return result['signedURL']
    except Exception as e:
        raise Exception(f"Failed to generate signed URL: {str(e)}")

def extract_text(file_bytes: bytes, filename: str) -> str:
    """Extract text from PDF or DOCX files"""
    try:
        if filename.lower().endswith('.pdf'):
            with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
                text = ""
                for page in pdf.pages:
                    text += page.extract_text() or ""
                return text.strip()
        
        elif filename.lower().endswith(('.docx', '.doc')):
            doc = Document(io.BytesIO(file_bytes))
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text.strip()
        
        else:
            raise ValueError("Unsupported file format. Please upload PDF or DOCX files.")
    
    except Exception as e:
        raise Exception(f"Failed to extract text from file: {str(e)}")

def evaluate_application(application_id: str, resume_text: str = None) -> Dict[str, Any]:
    """Run AI evaluation pipeline on application"""
    try:
        # Fetch application data
        app_result = supabase.table('applications').select('*').eq('id', application_id).execute()
        

        if not app_result.data:
            raise Exception("Application not found")
        
        application = app_result.data[0]
        
        # Fetch related job and student data separately
        job = {}
        student = {}
        
        if application.get('job_id'):
            job_result = supabase.table('jobs').select('*').eq('id', application['job_id']).execute()
            job = job_result.data[0] if job_result.data else {}
        
        if application.get('student_id'):
            student_result = supabase.table('students').select('*').eq('id', application['student_id']).execute()
            student = student_result.data[0] if student_result.data else {}
        
        # Use provided resume text or extract from Supabase if not provided
        if not resume_text:
            resume_path = application['resume_url']
            resume_bytes = supabase.storage.from_('resumes').download(resume_path)
            resume_text = extract_text(resume_bytes, resume_path)
        
        # Parse job requirements
        job_requirements = job.get('description', '') + ' ' + job.get('requirements', '')
        
        # Use LLM to analyze resume and job match
        analysis_prompt = f"""
        Analyze this resume against the job requirements and provide a comprehensive evaluation in JSON format.
        
        Job Title: {job.get('title', '')}
        Job Description: {job_requirements[:2000]}
        
        Resume Text: {resume_text[:3000]}
        
        Please provide a detailed analysis in the following JSON format:
        {{
            "skills": ["skill1", "skill2", "skill3"],
            "key_projects": ["project1", "project2", "project3"],
            "certifications": ["cert1", "cert2"],
            "experience": "X years of experience",
            "summary": "Brief 2-3 line summary of the candidate",
            "relevance_score": 85,
            "verdict": "High",
            "strong_points": ["point1", "point2", "point3"],
            "weak_points": ["point1", "point2", "point3"]
        }}
        
        Guidelines:
        - be useful and helpful, critically analyse the resume and the job requirements
        - be very critical and harsh in your analysis and giving relevance score
        - if you find skill mismatch/low/lower than expected experience/bad projects cgpa reduce points significantly
        - relevance_score: 0-100 based on overall match
        - verdict: "High" (75+), "Medium" (50-74), "Low" (<50)
        - Extract actual skills, projects, certifications from resume
        - Provide specific strong/weak points based on job requirements
        - Be objective and professional in analysis
        
        Return only valid JSON, no additional text.
        """
        
        # Use Groq client for LLM analysis
        if groq_client:
        
            response = groq_client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": "You are an expert HR analyst. Analyze resumes against job requirements and provide structured JSON output."},
                    {"role": "user", "content": analysis_prompt}
                ],
                temperature=0.1
            )
            analysis_text = response.choices[0].message.content.strip()
        else:
            raise Exception("LLM client not available")
        
        # Parse LLM response
        try:
            # Clean up the response to extract JSON
            analysis_text = analysis_text.replace('```json', '').replace('```', '').strip()
            analysis_data = json.loads(analysis_text)
        except json.JSONDecodeError as e:
            # Fallback parsing if JSON is malformed
            print(f"JSON parsing error: {e}")
            print(f"Raw response: {analysis_text}")
            analysis_data = {
                "skills": [],
                "key_projects": [],
                "certifications": [],
                "experience": "Unknown",
                "summary": "Unable to analyze resume",
                "relevance_score": 50,
                "verdict": "Medium",
                "strong_points": ["Resume submitted"],
                "weak_points": ["Unable to analyze"]
            }
        
        # Update application with AI analysis
        update_data = {
            'student_id': application['student_id'],
            'relevance_score': int(analysis_data.get('relevance_score', 50)),
            'verdict': analysis_data.get('verdict', 'Medium'),
            'strong_points': analysis_data.get('strong_points', []),
            'weak_points': analysis_data.get('weak_points', []),
            'skills': analysis_data.get('skills', []),
            'key_projects': analysis_data.get('key_projects', []),
            'certifications': analysis_data.get('certifications', []),
            'experience': analysis_data.get('experience', ''),
            'summary': analysis_data.get('summary', ''),
            'applied_for': job.get('title', '')
        }
        print(update_data)
        supabase.table('applications').update(update_data).eq('id', application_id).execute()
        
        return {
            'ok': True,
            'relevance_score': analysis_data.get('relevance_score', 50),
            'verdict': analysis_data.get('verdict', 'Medium')
        }
        
    except Exception as e:
        print(f"Error in evaluate_application: {str(e)}")
        return {
            'ok': False,
            'error': str(e)
        }

def translate_to_sql(nl_query: str) -> Dict[str, Any]:
    """Translate natural language to SQL using LLM"""
    try:
        prompt = f"""
        Translate this natural language query to SQL for a hiring portal database.
        
        Query: "{nl_query}"
        
        Available tables and columns:
        - students: id, user_id, full_name, email, phone, college, created_at
        - jobs: id, title, company, location, type, level, salary, description, requirements, benefits, deadline, status, posted_date, created_by, created_at
        - applications: id, student_id, job_id, resume_url, relevance_score, verdict, strong_points, weak_points, skills, key_projects, certifications, experience, summary, college, applied_for, created_at
        
        Rules:
        1. Only SELECT statements allowed
        2. No mutations (INSERT, UPDATE, DELETE)
        3. No dangerous keywords (DROP, ALTER, etc.)
        4. Single statement only
        5. Return only the SQL query
        6. dont use join statements
        7. dont send any additional text just the sql query
        
        SQL Query:
        """
        
        # Use Groq client for LLM analysis
        if groq_client:
        

            response = groq_client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": "You are an expert SQL developer. Translate this natural language query to SQL for a hiring portal database."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1
            )
            llm_response = response.choices[0].message.content.strip()
        else:
            raise Exception("LLM client not available")


        sql_query = llm_response.strip()
        print(sql_query)
        
        # Basic validation
        sql_query = sql_query.replace('```sql', '').replace('```', '').strip()
        
        if not sql_query.upper().startswith('SELECT'):
            raise Exception("Only SELECT statements are allowed")
        
        dangerous_keywords = ['DROP', 'DELETE', 'INSERT', 'UPDATE', 'ALTER', 'CREATE', 'TRUNCATE']
        if any(keyword in sql_query.upper() for keyword in dangerous_keywords):
            raise Exception("Dangerous SQL keywords detected")
        
        return {
            'ok': True,
            'sql': sql_query
        }
        
    except Exception as e:
        return {
            'ok': False,
            'error': str(e)
        }

def validate_and_execute_sql(sql_query: str) -> Dict[str, Any]:
    """Validate and execute SQL query safely"""
    try:
        # Additional validation
        allowed_tables = ['students', 'jobs', 'applications']
        sql_upper = sql_query.upper()
        
        # Check if query contains only allowed tables
        for table in allowed_tables:

            if f'FROM {table.upper()}' in sql_upper or f'JOIN {table.upper()}' in sql_upper:
                continue
        else:
            # If no allowed tables found, it might be a complex query
            if not any(table in sql_upper for table in [t.upper() for t in allowed_tables]):
                raise Exception("Query must reference allowed tables only")
        
        # Execute query using Supabase
        result = supabase.rpc('execute_sql', {'query': sql_query}).execute()
        print(result)

        
        if result.data:
            # Parse result
            columns = list(result.data[0].keys()) if result.data else []
            # rows = list(result.data[0].values()) if result.data else []
            rows = [list(row.values()) for row in result.data]
            print(rows)

            
            return {
                'ok': True,
                'columns': columns,
                'rows': rows
            }
        else:
            return {
                'ok': True,
                'columns': [],
                'rows': []
            }
            
    except Exception as e:
        return {
            'ok': False,
            'error': f"SQL execution failed: {str(e)}"
        }

def send_email(to_email: str, subject: str, body: str, from_alias: str = "Hiring Portal") -> Dict[str, Any]:
    """Send email using SMTP"""
    try:
        if not all([SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS]):
            raise Exception("SMTP configuration missing")
        
        msg = MIMEMultipart()
        msg['From'] = f"{from_alias} <{SMTP_USER}>"
        msg['To'] = to_email
        msg['Subject'] = subject
        
        msg.attach(MIMEText(body, 'html'))
        
        server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        
        text = msg.as_string()
        server.sendmail(SMTP_USER, to_email, text)
        server.quit()
        
        return {
            'ok': True,
            'message_id': f"sent_{datetime.now().timestamp()}"
        }
        
    except Exception as e:
        return {
            'ok': False,
            'error': str(e)
        }

# =============================================================================
# EXISTING ROUTES (Frontend)
# =============================================================================

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/student')
def student_dashboard():
    return render_template('student_dashboard.html')

@app.route('/placement')
def placement_dashboard():
    return render_template('placement_dashboard.html')

@app.route('/apply/<job_id>')
def apply_job(job_id):
    return render_template('apply_job.html', job_id=job_id)

@app.route('/placement/jobs')
def placement_jobs():
    return render_template('placement_jobs.html')

@app.route('/placement/applications')
def placement_applications():
    return render_template('placement_applications.html')

@app.route('/placement/analytics')
def placement_analytics():
    return render_template('placement_analytics.html')

# =============================================================================
# API ROUTES
# =============================================================================

# Job Routes
@app.route('/api/jobs', methods=['POST'])
def create_job():
    """Create a new job posting"""
    try:
        # Check if it's a form submission with file upload
        if request.content_type and 'multipart/form-data' in request.content_type:
            # Handle form data with file upload
            title = request.form.get('title')
            description = request.form.get('description')
            company = request.form.get('company')
            location = request.form.get('location')
            job_type = request.form.get('type')
            level = request.form.get('level')
            salary = request.form.get('salary')
            requirements = request.form.get('requirements')
            benefits = request.form.get('benefits')
            deadline = request.form.get('deadline')
            status = request.form.get('status', 'draft')
            created_by = request.form.get('created_by')
            
            # Handle JD PDF upload
            jd_pdf_url = None
            jd_file = request.files.get('jd_pdf')
            if jd_file and jd_file.filename:
                filename = f"jd_{uuid.uuid4().hex}.pdf"
                jd_path = f"jd_files/{filename}"
                file_bytes = jd_file.read()
                supabase_upload(file_bytes, jd_path, 'JD')
                jd_pdf_url = jd_path
            
            job_data = {
                'title': title,
                'company': company,
                'location': location,
                'type': job_type,
                'level': level,
                'salary': salary,
                'description': description,
                'requirements': requirements,
                'benefits': benefits,
                'deadline': deadline,
                'status': status,
                'created_by': created_by,
                'jd_pdf_url': jd_pdf_url,
                'posted_date': datetime.now().isoformat()
            }
        else:
            # Handle JSON data
            data = request.get_json()
            
            required_fields = ['title', 'description']
            for field in required_fields:
                if not data.get(field):
                    return jsonify({'ok': False, 'error': f'Missing required field: {field}'}), 400
            
            job_data = {
                'title': data['title'],
                'company': data.get('company'),
                'location': data.get('location'),
                'type': data.get('type'),
                'level': data.get('level'),
                'salary': data.get('salary'),
                'description': data['description'],
                'requirements': data.get('requirements'),
                'benefits': data.get('benefits'),
                'deadline': data.get('deadline'),
                'status': data.get('status', 'draft'),
                'created_by': data.get('created_by'),
                'jd_pdf_url': data.get('jd_pdf_url'),
                'posted_date': data.get('posted_date', datetime.now().isoformat())
            }
        
        result = supabase.table('jobs').insert(job_data).execute()
        
        if result.data:
            return jsonify({
                'ok': True,
                'job_id': result.data[0]['id'],
                'message': 'Job created successfully'
            })
        else:
            return jsonify({'ok': False, 'error': 'Failed to create job'}), 500
            
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500

@app.route('/api/jobs', methods=['GET'])
def get_jobs():
    """Get list of jobs with optional filtering"""
    try:
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))
        search = request.args.get('search', '')
        status = request.args.get('status', '')
        
        query = supabase.table('jobs').select('*')
        
        if search:
            query = query.or_(f'title.ilike.%{search}%,description.ilike.%{search}%,company.ilike.%{search}%')
        
        if status:
            query = query.eq('status', status)
        
        result = query.range(offset, offset + limit - 1).execute()
        
        return jsonify({
            'ok': True,
            'jobs': result.data,
            'total': len(result.data)
        })
        
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500

@app.route('/api/jobs/<job_id>', methods=['GET'])
def get_job(job_id):
    """Get a single job by ID"""
    try:
        result = supabase.table('jobs').select('*').eq('id', job_id).execute()
        
        if not result.data:
            return jsonify({'ok': False, 'error': 'Job not found'}), 404
        
        job = result.data[0]
        
        # Generate signed URL for JD PDF if it exists
        if job.get('jd_pdf_url'):
            try:
                job['jd_pdf_signed_url'] = supabase_signed_url(job['jd_pdf_url'], bucket='JD')
            except:
                job['jd_pdf_signed_url'] = None
        
        return jsonify({
            'ok': True,
            'job': job
        })
        
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500

@app.route('/api/jobs/<job_id>', methods=['PUT'])
def update_job(job_id):
    """Update a job posting"""
    try:
        # Check if it's a form submission with file upload
        if request.content_type and 'multipart/form-data' in request.content_type:
            # Handle form data with file upload
            update_data = {}
            allowed_fields = ['title', 'company', 'location', 'type', 'level', 'salary', 
                             'description', 'requirements', 'benefits', 'deadline', 'status']
            
            for field in allowed_fields:
                value = request.form.get(field)
                if value is not None:
                    update_data[field] = value
            
            # Handle JD PDF upload
            jd_file = request.files.get('jd_pdf')
            if jd_file and jd_file.filename:
                filename = f"jd_{uuid.uuid4().hex}.pdf"
                jd_path = f"jd_files/{filename}"
                file_bytes = jd_file.read()
                supabase_upload(file_bytes, jd_path, 'JD')
                update_data['jd_pdf_url'] = jd_path
            
            if not update_data:
                return jsonify({'ok': False, 'error': 'No valid fields to update'}), 400
        else:
            # Handle JSON data
            data = request.get_json()
            
            # Only update fields that are provided
            update_data = {}
            allowed_fields = ['title', 'company', 'location', 'type', 'level', 'salary', 
                             'description', 'requirements', 'benefits', 'deadline', 'status', 'jd_pdf_url']
            
            for field in allowed_fields:
                if field in data:
                    update_data[field] = data[field]
            
            if not update_data:
                return jsonify({'ok': False, 'error': 'No valid fields to update'}), 400
        
        result = supabase.table('jobs').update(update_data).eq('id', job_id).execute()
        
        if result.data:
            job = result.data[0]
            
            # Generate signed URL for JD PDF if it exists
            if job.get('jd_pdf_url'):
                try:
                    job['jd_pdf_signed_url'] = supabase_signed_url(job['jd_pdf_url'], bucket='JD')
                except:
                    job['jd_pdf_signed_url'] = None
            
            return jsonify({
                'ok': True,
                'job': job,
                'message': 'Job updated successfully'
            })
        else:
            return jsonify({'ok': False, 'error': 'Job not found or update failed'}), 404
            
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500

@app.route('/api/jobs/<job_id>', methods=['DELETE'])
def delete_job(job_id):
    """Delete a job posting"""
    try:
        result = supabase.table('jobs').delete().eq('id', job_id).execute()
        
        if result.data:
            return jsonify({
                'ok': True,
                'message': 'Job deleted successfully'
            })
        else:
            return jsonify({'ok': False, 'error': 'Job not found'}), 404
            
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500

# Application Routes
@app.route('/api/apply', methods=['POST'])
def apply_to_job():
    """Submit job application with resume upload"""
    try:
        # Get form data
        student_id = request.form.get('student_id')
        job_id = request.form.get('job_id')
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        college = request.form.get('college', '')
        file = request.files.get('file')
        
        if not all([job_id, name, email, phone, file]):
            return jsonify({'ok': False, 'error': 'Missing required fields'}), 400
        
        # Check if student already exists by email
        existing_student_result = supabase.table('students').select('*').eq('email', email).execute()
        
        if existing_student_result.data:
            # Use existing student
            student_id = existing_student_result.data[0]['id']
        else:
            # Create new student record
            student_data = {
                'full_name': name,
                'email': email,
                'phone': phone,
                'college': college,
                'created_at': datetime.now().isoformat()
            }
            
            student_result = supabase.table('students').insert(student_data).execute()
            
            if not student_result.data:
                return jsonify({'ok': False, 'error': 'Failed to create student record'}), 500
            
            student_id = student_result.data[0]['id']
        
        # Read file bytes and extract text
        file_bytes = file.read()
        resume_text = extract_text(file_bytes, file.filename)
        
        # Create temp folder and save extracted text
        temp_dir = tempfile.mkdtemp()
        temp_text_file = os.path.join(temp_dir, f"resume_text_{uuid.uuid4().hex}.txt")
        
        try:
            with open(temp_text_file, 'w', encoding='utf-8') as f:
                f.write(resume_text)
        except Exception as e:
            print(f"Error saving temp text file: {e}")
            # Continue without temp file if there's an issue
        
        # Upload resume to Supabase
        filename = f"{student_id}_{job_id}_{uuid.uuid4().hex}.pdf"
        resume_path = f"resumes/{filename}"
        supabase_upload(file_bytes, resume_path, 'resume')
        
        # Create application record with student_id
        application_data = {
            'student_id': student_id,
            'job_id': job_id,
            'resume_url': resume_path,
            'created_at': datetime.now().isoformat()
        }
        
        result = supabase.table('applications').insert(application_data).execute()
        
        if result.data:
            print(result.data)
            print(result.data[0]['id'])
            application_id = result.data[0]['id']
            
            # Trigger AI evaluation with extracted text
            evaluation_result = evaluate_application(application_id, resume_text)
            
            # Clean up temp directory
            try:
                shutil.rmtree(temp_dir)
            except Exception as e:
                print(f"Error cleaning up temp directory: {e}")
            
            return jsonify({
                'ok': True,
                'application_id': application_id,
                'evaluation': evaluation_result
            })
        else:
            return jsonify({'ok': False, 'error': 'Failed to create application'}), 500
            
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500

@app.route('/api/applications', methods=['GET'])
def get_applications():
    """Get applications - either for a specific job or all applications"""
    try:
        job_id = request.args.get('job_id')
        signed = request.args.get('signed', 'false').lower() == 'true'
        
        # Build query - fetch applications and related data separately to avoid relationship issues
        if job_id:
            # Get applications for specific job
            query = supabase.table('applications').select('*').eq('job_id', job_id)
        else:
            # Get all applications
            query = supabase.table('applications').select('*')
        
        result = query.execute()
        applications = result.data
        
        # Fetch related student and job data separately
        for app in applications:
            # Get student data
            if app.get('student_id'):
                student_result = supabase.table('students').select('*').eq('id', app['student_id']).execute()
                app['students'] = student_result.data[0] if student_result.data else {}
            
            # Get job data
            if app.get('job_id'):
                job_result = supabase.table('jobs').select('*').eq('id', app['job_id']).execute()
                app['jobs'] = job_result.data[0] if job_result.data else {}
        
        # Generate signed URLs if requested
        if signed:
            for app in applications:
                if app['resume_url']:
                    try:
                        app['resume_signed_url'] = supabase_signed_url(app['resume_url'])
                    except:
                        app['resume_signed_url'] = None
        
        return jsonify({
            'ok': True,
            'applications': applications
        })
        
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500

@app.route('/api/application/<application_id>', methods=['GET'])
def get_application(application_id):
    """Get full application details"""
    try:
        signed = request.args.get('signed', 'false').lower() == 'true'
        
        result = supabase.table('applications').select('*').eq('id', application_id).execute()
        
        if not result.data:
            return jsonify({'ok': False, 'error': 'Application not found'}), 404
        
        application = result.data[0]
        
        # Fetch related student and job data separately
        if application.get('student_id'):
            student_result = supabase.table('students').select('*').eq('id', application['student_id']).execute()
            application['students'] = student_result.data[0] if student_result.data else {}
        
        if application.get('job_id'):
            job_result = supabase.table('jobs').select('*').eq('id', application['job_id']).execute()
            application['jobs'] = job_result.data[0] if job_result.data else {}
        
        # Generate signed URL for resume if requested
        if signed and application.get('resume_url'):
            try:
                application['resume_signed_url'] = supabase_signed_url(application['resume_url'])
            except Exception as e:
                print(f"Error generating signed URL: {e}")
                application['resume_signed_url'] = None
        
        return jsonify({
            'ok': True,
            'application': application
        })
        
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500

@app.route('/api/applications/<application_id>', methods=['PATCH'])
def update_application(application_id):
    """Update application status or other fields"""
    try:
        data = request.get_json()
        
        # Only update fields that are provided
        update_data = {}
        allowed_fields = ['status', 'verdict', 'relevance_score', 'strong_points', 'weak_points']
        
        for field in allowed_fields:
            if field in data:
                update_data[field] = data[field]
        
        if not update_data:
            return jsonify({'ok': False, 'error': 'No valid fields to update'}), 400
        
        result = supabase.table('applications').update(update_data).eq('id', application_id).execute()
        
        if result.data:
            return jsonify({
                'ok': True,
                'application': result.data[0],
                'message': 'Application updated successfully'
            })
        else:
            return jsonify({'ok': False, 'error': 'Application not found or update failed'}), 404
            
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500

# AI Evaluation Route
@app.route('/api/evaluate', methods=['POST'])
def evaluate_application_route():
    """Trigger AI evaluation for an application"""
    try:
        data = request.get_json()
        application_id = data.get('application_id')
        
        if not application_id:
            return jsonify({'ok': False, 'error': 'application_id required'}), 400
        
        result = evaluate_application(application_id)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500

# NLP to SQL Route
@app.route('/api/nlpsql', methods=['POST'])
def nlp_to_sql():
    """Convert natural language query to SQL"""
    try:
        data = request.get_json()
        query = data.get('query')
        
        
        if not query:
            return jsonify({'ok': False, 'error': 'query required'}), 400
        
        # Translate to SQL
        sql_result = translate_to_sql(query)
        
        if not sql_result['ok']:
            return jsonify(sql_result), 400
        
        # Execute SQL
        execution_result = validate_and_execute_sql(sql_result['sql'])
        
        return jsonify(execution_result)
        
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500

# Email Route
@app.route('/api/email/send', methods=['POST'])
def send_email_route():
    """Send email to candidate"""
    try:
        data = request.get_json()
        application_id = data.get('application_id')
        subject = data.get('subject')
        body = data.get('body')
        from_alias = data.get('from_alias', 'Hiring Portal')
        
        if not all([application_id, subject, body]):
            return jsonify({'ok': False, 'error': 'Missing required fields'}), 400
        
        # Get application and student email
        result = supabase.table('applications').select('students(email)').eq('id', application_id).execute()
        
        if not result.data:
            return jsonify({'ok': False, 'error': 'Application not found'}), 404
        
        student_email = result.data[0]['students']['email']
        
        # Send email
        email_result = send_email(student_email, subject, body, from_alias)
        
        return jsonify(email_result)
        
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500

# =============================================================================
# ERROR HANDLERS
# =============================================================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({'ok': False, 'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'ok': False, 'error': 'Internal server error'}), 500

# =============================================================================
# MAIN
# =============================================================================

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)