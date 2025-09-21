# Hiring Portal API Documentation

## Overview

The Hiring Portal API provides endpoints for managing jobs, applications, AI-powered resume evaluation, natural language queries, and email communications.

## Base URL

```
http://localhost:5000
```

## Authentication

Currently, the API uses basic authentication. In production, implement proper JWT or OAuth2 authentication.

## API Endpoints

### Jobs API

#### Create Job
```http
POST /api/jobs
Content-Type: application/json

{
  "title": "Software Engineer",
  "description": "We are looking for a talented software engineer...",
  "location": "San Francisco",
  "department": "Engineering",
  "created_by": "user-id"
}
```

**Response:**
```json
{
  "ok": true,
  "job_id": "uuid",
  "message": "Job created successfully"
}
```

#### Get Jobs
```http
GET /api/jobs?limit=10&offset=0&search=engineer
```

**Query Parameters:**
- `limit` (optional): Number of jobs to return (default: 50)
- `offset` (optional): Number of jobs to skip (default: 0)
- `search` (optional): Search term for job title/description

**Response:**
```json
{
  "ok": true,
  "jobs": [
    {
      "id": "uuid",
      "title": "Software Engineer",
      "description": "...",
      "location": "San Francisco",
      "department": "Engineering",
      "created_by": "user-id",
      "created_at": "2024-01-15T10:30:00Z"
    }
  ],
  "total": 1
}
```

### Applications API

#### Submit Application
```http
POST /api/apply
Content-Type: multipart/form-data

student_id: uuid
job_id: uuid
name: John Doe
email: john@example.com
phone: +1234567890
file: [resume.pdf]
```

**Response:**
```json
{
  "ok": true,
  "application_id": "uuid",
  "evaluation": {
    "ok": true,
    "relevance_score": 85.5,
    "verdict": "High"
  }
}
```

#### Get Applications
```http
GET /api/applications?job_id=uuid&signed=true
```

**Query Parameters:**
- `job_id` (required): Job ID to filter applications
- `signed` (optional): Include signed URLs for resumes (default: false)

**Response:**
```json
{
  "ok": true,
  "applications": [
    {
      "id": "uuid",
      "student_id": "uuid",
      "job_id": "uuid",
      "resume_url": "resumes/file.pdf",
      "resume_signed_url": "https://signed-url...",
      "relevance_score": 85.5,
      "verdict": "High",
      "strong_points": ["Strong technical skills", "Relevant experience"],
      "weak_points": ["Limited leadership experience"],
      "skills": ["Python", "React", "AWS"],
      "key_projects": ["E-commerce platform", "ML model"],
      "certifications": ["AWS Certified"],
      "experience": "3 years",
      "summary": "Experienced software engineer...",
      "college": "University of Technology",
      "applied_for": "Software Engineer",
      "created_at": "2024-01-15T10:30:00Z",
      "students": {
        "full_name": "John Doe",
        "email": "john@example.com",
        "phone": "+1234567890",
        "college": "University of Technology"
      },
      "jobs": {
        "title": "Software Engineer",
        "description": "...",
        "location": "San Francisco"
      }
    }
  ]
}
```

#### Get Application Details
```http
GET /api/application/{application_id}
```

**Response:**
```json
{
  "ok": true,
  "application": {
    "id": "uuid",
    "student_id": "uuid",
    "job_id": "uuid",
    "resume_url": "resumes/file.pdf",
    "resume_signed_url": "https://signed-url...",
    "relevance_score": 85.5,
    "verdict": "High",
    "strong_points": ["Strong technical skills"],
    "weak_points": ["Limited leadership experience"],
    "skills": ["Python", "React"],
    "key_projects": ["E-commerce platform"],
    "certifications": ["AWS Certified"],
    "experience": "3 years",
    "summary": "Experienced software engineer...",
    "college": "University of Technology",
    "applied_for": "Software Engineer",
    "created_at": "2024-01-15T10:30:00Z",
    "students": {
      "full_name": "John Doe",
      "email": "john@example.com"
    },
    "jobs": {
      "title": "Software Engineer",
      "description": "..."
    }
  }
}
```

### AI Evaluation API

#### Evaluate Application
```http
POST /api/evaluate
Content-Type: application/json

{
  "application_id": "uuid"
}
```

**Response:**
```json
{
  "ok": true,
  "relevance_score": 85.5,
  "verdict": "High"
}
```

### NLP to SQL API

#### Natural Language Query
```http
POST /api/nlpsql
Content-Type: application/json

{
  "query": "Show me all applications with high relevance scores"
}
```

**Response:**
```json
{
  "ok": true,
  "columns": ["id", "student_name", "relevance_score", "verdict"],
  "rows": [
    ["uuid1", "John Doe", 85.5, "High"],
    ["uuid2", "Jane Smith", 78.2, "High"]
  ]
}
```

**Example Queries:**
- "Show me all applications for software engineer positions"
- "Find students with Python skills"
- "List applications with relevance score above 80"
- "Show me all jobs in San Francisco"
- "Find applications from students at University of Technology"

### Email API

#### Send Email
```http
POST /api/email/send
Content-Type: application/json

{
  "application_id": "uuid",
  "subject": "Interview Invitation",
  "body": "<h1>Congratulations!</h1><p>We would like to invite you for an interview...</p>",
  "from_alias": "HR Team"
}
```

**Response:**
```json
{
  "ok": true,
  "message_id": "sent_1705312200.123"
}
```

## Error Responses

All endpoints return errors in the following format:

```json
{
  "ok": false,
  "error": "Error message description"
}
```

**Common HTTP Status Codes:**
- `200` - Success
- `400` - Bad Request (missing required fields, invalid data)
- `404` - Not Found (resource doesn't exist)
- `500` - Internal Server Error

## Rate Limiting

Currently, no rate limiting is implemented. In production, implement rate limiting to prevent abuse.

## File Upload Limits

- Maximum file size: 10MB
- Allowed file types: PDF, DOC, DOCX
- Files are stored in Supabase storage bucket

## AI Model Configuration

The system supports two LLM providers:

### Groq (Recommended)
```env
LLM_PROVIDER=groq
GROQ_API_KEY=your-groq-api-key
```

### Google Gemini
```env
LLM_PROVIDER=gemini
GEMINI_API_KEY=your-gemini-api-key
```

## Database Schema

### Tables

#### students
- `id` (UUID, Primary Key)
- `user_id` (UUID, Foreign Key to auth.users)
- `full_name` (TEXT)
- `email` (TEXT, Unique)
- `phone` (TEXT)
- `college` (TEXT)
- `created_at` (TIMESTAMP)
- `updated_at` (TIMESTAMP)

#### jobs
- `id` (UUID, Primary Key)
- `title` (TEXT)
- `description` (TEXT)
- `location` (TEXT)
- `department` (TEXT)
- `created_by` (UUID, Foreign Key to auth.users)
- `created_at` (TIMESTAMP)
- `updated_at` (TIMESTAMP)

#### applications
- `id` (UUID, Primary Key)
- `student_id` (UUID, Foreign Key to students)
- `job_id` (UUID, Foreign Key to jobs)
- `resume_url` (TEXT)
- `relevance_score` (DECIMAL)
- `verdict` (TEXT: 'High', 'Medium', 'Low')
- `strong_points` (TEXT[])
- `weak_points` (TEXT[])
- `skills` (TEXT[])
- `key_projects` (TEXT[])
- `certifications` (TEXT[])
- `experience` (TEXT)
- `summary` (TEXT)
- `college` (TEXT)
- `applied_for` (TEXT)
- `status` (TEXT: 'pending', 'reviewed', 'shortlisted', 'rejected', 'hired')
- `created_at` (TIMESTAMP)
- `updated_at` (TIMESTAMP)

#### ai_audit
- `id` (UUID, Primary Key)
- `application_id` (UUID, Foreign Key to applications)
- `raw_response` (JSONB)
- `evaluation_type` (TEXT)
- `created_at` (TIMESTAMP)

## Security Considerations

1. **Input Validation**: All inputs are validated and sanitized
2. **SQL Injection Prevention**: Uses parameterized queries
3. **File Upload Security**: Validates file types and sizes
4. **Row Level Security**: Implemented in Supabase
5. **CORS Configuration**: Configured for cross-origin requests

## Testing

### Using curl

#### Create a job:
```bash
curl -X POST http://localhost:5000/api/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Software Engineer",
    "description": "We are looking for a talented software engineer...",
    "location": "San Francisco",
    "department": "Engineering"
  }'
```

#### Submit an application:
```bash
curl -X POST http://localhost:5000/api/apply \
  -F "student_id=uuid" \
  -F "job_id=uuid" \
  -F "name=John Doe" \
  -F "email=john@example.com" \
  -F "phone=+1234567890" \
  -F "file=@resume.pdf"
```

#### Natural language query:
```bash
curl -X POST http://localhost:5000/api/nlpsql \
  -H "Content-Type: application/json" \
  -d '{"query": "Show me all high-scoring applications"}'
```

## Production Deployment

1. Set `FLASK_ENV=production`
2. Use a production WSGI server (Gunicorn)
3. Set up reverse proxy (Nginx)
4. Configure SSL certificates
5. Set up monitoring and logging
6. Implement proper authentication
7. Configure rate limiting
8. Set up database backups

## Support

For API support and questions:
- Check the error messages in responses
- Review the database schema
- Ensure all required environment variables are set
- Check the application logs for detailed error information
