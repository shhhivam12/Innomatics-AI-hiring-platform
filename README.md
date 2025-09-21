# Hiring Portal - AI-Powered Recruitment Platform

A comprehensive hiring portal built with Flask, Supabase, and AI technologies for managing job applications, resume evaluation, and candidate communication.

## Features

### For Students
- Browse available job opportunities
- Upload resumes and apply to jobs
- Track application status
- Receive email notifications

### For Placement Department
- Create and manage job postings
- Review applications with AI-powered insights
- Natural language query interface for data analysis
- Send emails to candidates
- Track recruitment metrics

### AI-Powered Features
- Resume parsing and skill extraction
- Job-resume matching with relevance scoring
- Natural language to SQL queries
- Automated email notifications
- Candidate feedback generation

## Technology Stack

### Backend
- **Flask** - Web framework
- **Supabase** - Database and authentication
- **LangChain/LangGraph** - AI orchestration
- **Groq/Gemini** - Large Language Models
- **Sentence Transformers** - Text embeddings
- **PDFplumber** - Resume parsing

### Frontend
- **HTML/CSS/JavaScript** - Responsive web interface
- **Design System** - Consistent UI components
- **Mobile-first** - Responsive design

## Installation

### Prerequisites
- Python 3.10+
- Supabase account
- Groq or Gemini API key
- SMTP email configuration

### Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd hiring-portal
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   ```bash
   cp env.example .env
   # Edit .env with your configuration
   ```

4. **Set up Supabase**
   - Create a new Supabase project
   - Run the SQL schema (see Database Schema section)
   - Configure storage buckets
   - Set up Row Level Security policies

5. **Run the application**
   ```bash
   python backend/app.py
   ```

## Configuration

### Environment Variables

```env
# Flask Configuration
FLASK_ENV=development
FLASK_APP=backend/app.py
SECRET_KEY=your-secret-key-here

# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key-here
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key-here

# LLM Configuration
GROQ_API_KEY=your-groq-api-key-here
GEMINI_API_KEY=your-gemini-api-key-here
LLM_PROVIDER=groq
AI_EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

# Email Configuration
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASS=your-app-password
```

## Database Schema

### Supabase Tables

```sql
-- Students table
CREATE TABLE students (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id),
    full_name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    phone TEXT,
    college TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Jobs table
CREATE TABLE jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    location TEXT NOT NULL,
    department TEXT NOT NULL,
    created_by UUID REFERENCES auth.users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Applications table
CREATE TABLE applications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID REFERENCES students(id),
    job_id UUID REFERENCES jobs(id),
    resume_url TEXT,
    relevance_score INTEGER,
    verdict TEXT,
    strong_points TEXT[],
    weak_points TEXT[],
    skills TEXT[],
    key_projects TEXT[],
    certifications TEXT[],
    experience TEXT,
    summary TEXT,
    college TEXT,
    applied_for TEXT,
    status TEXT DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- AI Audit table
CREATE TABLE ai_audit (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    application_id UUID REFERENCES applications(id),
    raw_response JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### Storage Buckets

```sql
-- Create resumes bucket
INSERT INTO storage.buckets (id, name, public) VALUES ('resumes', 'resumes', false);

-- Set up RLS policies for resumes bucket
CREATE POLICY "Users can upload resumes" ON storage.objects
FOR INSERT WITH CHECK (bucket_id = 'resumes');

CREATE POLICY "Users can view resumes" ON storage.objects
FOR SELECT USING (bucket_id = 'resumes');
```

## API Endpoints

### Jobs API
- `POST /api/jobs` - Create job posting
- `GET /api/jobs` - List jobs with filtering
- `GET /api/jobs/{id}` - Get specific job
- `PUT /api/jobs/{id}` - Update job
- `DELETE /api/jobs/{id}` - Delete job

### Applications API
- `POST /api/applications` - Submit application
- `GET /api/applications` - List applications
- `GET /api/applications/{id}` - Get specific application
- `PATCH /api/applications/{id}` - Update application
- `DELETE /api/applications/{id}` - Delete application

### AI Evaluation API
- `POST /api/evaluate` - Evaluate application
- `POST /api/evaluate/batch` - Batch evaluation
- `POST /api/evaluate/relevance` - Calculate relevance score
- `POST /api/evaluate/feedback` - Generate feedback

### NLP to SQL API
- `POST /api/nlpsql` - Natural language queries
- `POST /api/nlpsql/validate` - Validate SQL queries
- `GET /api/nlpsql/schema` - Get database schema

### Email API
- `POST /api/email/send` - Send email
- `POST /api/email/confirmation` - Send confirmation
- `POST /api/email/status-update` - Send status update
- `POST /api/email/interview-invitation` - Send interview invite
- `POST /api/email/bulk` - Send bulk emails

## AI Pipeline

### Resume Evaluation Process

1. **Text Extraction** - Extract text from PDF/DOC files
2. **LLM Parsing** - Parse resume and job description
3. **Skill Matching** - Hard match required skills
4. **Semantic Matching** - Embed and compare text similarity
5. **Relevance Scoring** - Combine hard and semantic scores
6. **Feedback Generation** - Generate strong/weak points
7. **Database Update** - Store evaluation results

### NLP to SQL Safety

- Only SELECT queries allowed
- Validates table and column names
- Prevents SQL injection
- Uses parameterized queries
- Logs all queries for audit

## Security Features

- Row Level Security (RLS) in Supabase
- Input validation and sanitization
- File type validation for uploads
- SQL injection prevention
- CORS configuration
- Environment-based configuration

## Development

### Project Structure

```
hiring-portal/
├── backend/
│   ├── api/           # API endpoints
│   ├── lib/           # Core libraries
│   ├── app.py         # Main Flask app
│   └── config.py      # Configuration
├── templates/         # HTML templates
├── static/           # CSS, JS, images
├── requirements.txt  # Python dependencies
└── README.md        # This file
```

### Running in Development

```bash
# Set environment
export FLASK_ENV=development

# Run with auto-reload
python backend/app.py
```

### Testing

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=backend
```

## Deployment

### Production Setup

1. **Environment Configuration**
   - Set `FLASK_ENV=production`
   - Use production Supabase project
   - Configure production SMTP settings

2. **Database Setup**
   - Run migration scripts
   - Set up RLS policies
   - Configure storage buckets

3. **Server Deployment**
   - Use WSGI server (Gunicorn)
   - Set up reverse proxy (Nginx)
   - Configure SSL certificates

### Docker Deployment

```dockerfile
FROM python:3.10-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 5000

CMD ["python", "backend/app.py"]
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For support and questions:
- Create an issue in the repository
- Check the API documentation at `/api/docs`
- Review the configuration examples

## Roadmap

- [ ] User authentication system
- [ ] Advanced analytics dashboard
- [ ] Interview scheduling integration
- [ ] Mobile app development
- [ ] Multi-language support
- [ ] Advanced AI features
