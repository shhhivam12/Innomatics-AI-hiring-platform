-- Hiring Portal Database Schema for Supabase
-- Run this SQL in your Supabase SQL editor

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Students table
CREATE TABLE IF NOT EXISTS students (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    full_name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    phone TEXT,
    college TEXT,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
);

-- Jobs table
CREATE TABLE IF NOT EXISTS jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    location TEXT NOT NULL,
    department TEXT NOT NULL,
    company TEXT,
    type TEXT,
    level TEXT,
    salary TEXT,
    requirements TEXT,
    benefits TEXT,
    deadline DATE,
    status TEXT DEFAULT 'draft',
    jd_pdf_url TEXT,
    posted_date TIMESTAMP WITH TIME ZONE,
    created_by UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Applications table
CREATE TABLE IF NOT EXISTS applications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    student_id UUID REFERENCES students(id) ON DELETE CASCADE,
    job_id UUID REFERENCES jobs(id) ON DELETE CASCADE,
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
    applied_for TEXT,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
);

-- AI Audit table for tracking AI evaluations
CREATE TABLE IF NOT EXISTS ai_audit (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    application_id UUID REFERENCES applications(id) ON DELETE CASCADE,
    raw_response JSONB,
    evaluation_type TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_students_email ON students(email);
CREATE INDEX IF NOT EXISTS idx_students_user_id ON students(user_id);
CREATE INDEX IF NOT EXISTS idx_jobs_created_by ON jobs(created_by);
CREATE INDEX IF NOT EXISTS idx_jobs_created_at ON jobs(created_at);
CREATE INDEX IF NOT EXISTS idx_applications_student_id ON applications(student_id);
CREATE INDEX IF NOT EXISTS idx_applications_job_id ON applications(job_id);
CREATE INDEX IF NOT EXISTS idx_applications_relevance_score ON applications(relevance_score);
CREATE INDEX IF NOT EXISTS idx_applications_verdict ON applications(verdict);
CREATE INDEX IF NOT EXISTS idx_applications_status ON applications(status);
CREATE INDEX IF NOT EXISTS idx_ai_audit_application_id ON ai_audit(application_id);

-- Create storage bucket for resumes
INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
VALUES (
    'resumes', 
    'resumes', 
    false, 
    10485760, -- 10MB limit
    ARRAY['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']
) ON CONFLICT (id) DO NOTHING;

-- Create storage bucket for JD files
INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
VALUES (
    'JD', 
    'JD', 
    false, 
    10485760, -- 10MB limit
    ARRAY['application/pdf']
) ON CONFLICT (id) DO NOTHING;

-- Row Level Security (RLS) Policies

-- Enable RLS on all tables
ALTER TABLE students ENABLE ROW LEVEL SECURITY;
ALTER TABLE jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE applications ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_audit ENABLE ROW LEVEL SECURITY;

-- Students policies
CREATE POLICY "Students can view their own data" ON students
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Students can update their own data" ON students
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Students can insert their own data" ON students
    FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Jobs policies
CREATE POLICY "Anyone can view active jobs" ON jobs
    FOR SELECT USING (true);

CREATE POLICY "Authenticated users can create jobs" ON jobs
    FOR INSERT WITH CHECK (auth.uid() IS NOT NULL);

CREATE POLICY "Job creators can update their jobs" ON jobs
    FOR UPDATE USING (auth.uid() = created_by);

CREATE POLICY "Job creators can delete their jobs" ON jobs
    FOR DELETE USING (auth.uid() = created_by);

-- Applications policies
CREATE POLICY "Students can view their own applications" ON applications
    FOR SELECT USING (
        student_id IN (
            SELECT id FROM students WHERE user_id = auth.uid()
        )
    );

CREATE POLICY "Students can create applications" ON applications
    FOR INSERT WITH CHECK (
        student_id IN (
            SELECT id FROM students WHERE user_id = auth.uid()
        )
    );

CREATE POLICY "Job creators can view applications for their jobs" ON applications
    FOR SELECT USING (
        job_id IN (
            SELECT id FROM jobs WHERE created_by = auth.uid()
        )
    );

CREATE POLICY "Job creators can update applications for their jobs" ON applications
    FOR UPDATE USING (
        job_id IN (
            SELECT id FROM jobs WHERE created_by = auth.uid()
        )
    );

-- AI Audit policies
CREATE POLICY "Job creators can view AI audit for their applications" ON ai_audit
    FOR SELECT USING (
        application_id IN (
            SELECT a.id FROM applications a
            JOIN jobs j ON a.job_id = j.id
            WHERE j.created_by = auth.uid()
        )
    );

CREATE POLICY "System can insert AI audit records" ON ai_audit
    FOR INSERT WITH CHECK (true);

-- Storage policies for resumes bucket
CREATE POLICY "Users can upload resumes" ON storage.objects
    FOR INSERT WITH CHECK (
        bucket_id = 'resumes' AND
        auth.uid() IS NOT NULL
    );

CREATE POLICY "Users can view their own resumes" ON storage.objects
    FOR SELECT USING (
        bucket_id = 'resumes' AND
        auth.uid() IS NOT NULL
    );

CREATE POLICY "Job creators can view resumes for their applications" ON storage.objects
    FOR SELECT USING (
        bucket_id = 'resumes' AND
        EXISTS (
            SELECT 1 FROM applications a
            JOIN jobs j ON a.job_id = j.id
            WHERE a.resume_url = name AND j.created_by = auth.uid()
        )
    );

-- Storage policies for JD bucket
CREATE POLICY "Job creators can upload JD files" ON storage.objects
    FOR INSERT WITH CHECK (
        bucket_id = 'JD' AND
        auth.uid() IS NOT NULL
    );

CREATE POLICY "Anyone can view JD files" ON storage.objects
    FOR SELECT USING (
        bucket_id = 'JD'
    );

CREATE POLICY "Job creators can update their JD files" ON storage.objects
    FOR UPDATE USING (
        bucket_id = 'JD' AND
        EXISTS (
            SELECT 1 FROM jobs j
            WHERE j.jd_pdf_url = name AND j.created_by = auth.uid()
        )
    );

CREATE POLICY "Job creators can delete their JD files" ON storage.objects
    FOR DELETE USING (
        bucket_id = 'JD' AND
        EXISTS (
            SELECT 1 FROM jobs j
            WHERE j.jd_pdf_url = name AND j.created_by = auth.uid()
        )
    );

-- Functions for updated_at timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers for updated_at
CREATE TRIGGER update_students_updated_at BEFORE UPDATE ON students
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_jobs_updated_at BEFORE UPDATE ON jobs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_applications_updated_at BEFORE UPDATE ON applications
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function to execute SQL queries safely (for NLP to SQL feature)
CREATE OR REPLACE FUNCTION execute_sql(query_text TEXT)
RETURNS JSON AS $$
DECLARE
    result JSON;
BEGIN
    -- This function should be called with proper validation in the application
    -- For security, we'll implement basic checks here
    IF query_text ILIKE '%DROP%' OR 
       query_text ILIKE '%DELETE%' OR 
       query_text ILIKE '%INSERT%' OR 
       query_text ILIKE '%UPDATE%' OR 
       query_text ILIKE '%ALTER%' OR 
       query_text ILIKE '%CREATE%' OR 
       query_text ILIKE '%TRUNCATE%' THEN
        RETURN json_build_object('error', 'Unsafe SQL operation detected');
    END IF;
    
    -- Only allow SELECT statements
    IF NOT query_text ILIKE 'SELECT%' THEN
        RETURN json_build_object('error', 'Only SELECT statements are allowed');
    END IF;
    
    -- Execute the query (this is a simplified version)
    -- In production, you should implement more sophisticated validation
    EXECUTE query_text INTO result;
    
    RETURN result;
EXCEPTION
    WHEN OTHERS THEN
        RETURN json_build_object('error', SQLERRM);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Grant necessary permissions
GRANT USAGE ON SCHEMA public TO authenticated;
GRANT ALL ON ALL TABLES IN SCHEMA public TO authenticated;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO authenticated;
GRANT EXECUTE ON FUNCTION execute_sql(TEXT) TO authenticated;

-- Sample data (optional - for testing)
INSERT INTO students (full_name, email, phone, college) VALUES
('John Doe', 'john.doe@example.com', '+1234567890', 'Example University'),
('Jane Smith', 'jane.smith@example.com', '+1234567891', 'Example University'),
('Bob Johnson', 'bob.johnson@example.com', '+1234567892', 'Example University')
ON CONFLICT (email) DO NOTHING;

INSERT INTO jobs (title, description, location, department, created_by) VALUES
('Software Engineer', 'We are looking for a talented software engineer to join our team.', 'San Francisco', 'Engineering', NULL),
('Data Scientist', 'Join our data science team and work on exciting ML projects.', 'New York', 'Data Science', NULL),
('Product Manager', 'Drive product strategy and work with cross-functional teams.', 'Seattle', 'Product', NULL)
ON CONFLICT DO NOTHING;
