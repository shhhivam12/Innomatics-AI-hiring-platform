// Backend API Integration for Hiring Portal
// This file contains functions to interact with the Flask backend APIs

// API Base URL
const API_BASE_URL = window.location.origin;

// Initialize Supabase client (if not already initialized)
if (typeof supabase === 'undefined') {
    // Fallback: Initialize a minimal supabase object for compatibility
    window.supabase = {
        auth: {
            getSession: async () => ({ data: { session: null }, error: null }),
            signIn: async () => ({ data: { user: null }, error: null }),
            signUp: async () => ({ data: { user: null }, error: null }),
            signOut: async () => ({ error: null })
        }
    };
}

// Helper function to make API requests
async function apiRequest(endpoint, options = {}) {
    try {
        const url = `${API_BASE_URL}${endpoint}`;
        const response = await fetch(url, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'API request failed');
        }
        
        return data;
    } catch (error) {
        console.error('API request error:', error);
        throw error;
    }
}

// Helper function to make form data requests
async function apiFormRequest(endpoint, formData) {
    try {
        const url = `${API_BASE_URL}${endpoint}`;
        const response = await fetch(url, {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'API request failed');
        }
        
        return data;
    } catch (error) {
        console.error('API form request error:', error);
        throw error;
    }
}

// Supabase Functions for Hiring Portal

// Authentication Functions
const AuthService = {
    // Sign in user
    async signIn(email, password) {
        try {
            const { data, error } = await supabase.auth.signIn({
                email,
                password
            });
            
            if (error) throw error;
            return { success: true, user: data.user };
        } catch (error) {
            console.error('Sign in error:', error);
            return { success: false, error: error.message };
        }
    },
    
    // Sign up user
    async signUp(email, password, userData = {}) {
        try {
            const { data, error } = await supabase.auth.signUp({
                email,
                password,
                options: {
                    data: userData
                }
            });
            
            if (error) throw error;
            return { success: true, user: data.user };
        } catch (error) {
            console.error('Sign up error:', error);
            return { success: false, error: error.message };
        }
    },
    
    // Sign out user
    async signOut() {
        try {
            const { error } = await supabase.auth.signOut();
            if (error) throw error;
            return { success: true };
        } catch (error) {
            console.error('Sign out error:', error);
            return { success: false, error: error.message };
        }
    },
    
    // Get current session
    async getCurrentSession() {
        try {
            const { data, error } = await supabase.auth.getSession();
            if (error) throw error;
            return { success: true, session: data.session };
        } catch (error) {
            console.error('Get session error:', error);
            return { success: false, error: error.message };
        }
    }
};

// Job Management Functions
const JobService = {
    // Fetch all jobs for student view
    async fetchJobs(params = {}) {
        try {
            const queryParams = new URLSearchParams();
            if (params.limit) queryParams.append('limit', params.limit);
            if (params.offset) queryParams.append('offset', params.offset);
            if (params.search) queryParams.append('search', params.search);
            
            const endpoint = `/api/jobs${queryParams.toString() ? '?' + queryParams.toString() : ''}`;
            const data = await apiRequest(endpoint);
            
            return { success: true, jobs: data.jobs };
        } catch (error) {
            console.error('Fetch jobs error:', error);
            return { success: false, error: error.message };
        }
    },
    
    // Fetch job by ID
    async fetchJobById(jobId) {
        try {
            const data = await apiRequest(`/api/jobs/${jobId}`);
            return { success: true, job: data.job };
        } catch (error) {
            console.error('Fetch job error:', error);
            return { success: false, error: error.message };
        }
    },
    
    // Create new job (Placement Department)
    async createJob(jobData) {
        try {
            const data = await apiRequest('/api/jobs', {
                method: 'POST',
                body: JSON.stringify(jobData)
            });
            
            return { success: true, job: data };
        } catch (error) {
            console.error('Create job error:', error);
            return { success: false, error: error.message };
        }
    },
    
    // Create new job with file upload (Placement Department)
    async createJobWithFile(formData) {
        try {
            const data = await apiFormRequest('/api/jobs', formData);
            return { success: true, job: data };
        } catch (error) {
            console.error('Create job with file error:', error);
            return { success: false, error: error.message };
        }
    },
    
    // Update job
    async updateJob(jobId, jobData) {
        try {
            const data = await apiRequest(`/api/jobs/${jobId}`, {
                method: 'PUT',
                body: JSON.stringify(jobData)
            });
            
            return { success: true, job: data };
        } catch (error) {
            console.error('Update job error:', error);
            return { success: false, error: error.message };
        }
    },
    
    // Update job with file upload
    async updateJobWithFile(jobId, formData) {
        try {
            const data = await apiFormRequest(`/api/jobs/${jobId}`, formData);
            return { success: true, job: data };
        } catch (error) {
            console.error('Update job with file error:', error);
            return { success: false, error: error.message };
        }
    },
    
    // Delete job
    async deleteJob(jobId) {
        try {
            await apiRequest(`/api/jobs/${jobId}`, {
                method: 'DELETE'
            });
            
            return { success: true };
        } catch (error) {
            console.error('Delete job error:', error);
            return { success: false, error: error.message };
        }
    }
};

// Application Management Functions
const ApplicationService = {
    // Submit job application (Student)
    async submitApplication(formData) {
        try {
            const data = await apiFormRequest('/api/apply', formData);
            return { success: true, application: data };
        } catch (error) {
            console.error('Submit application error:', error);
            return { success: false, error: error.message };
        }
    },
    
    // Fetch applications for placement department
    async fetchApplications(jobId = null, signed = false) {
        try {
            const queryParams = new URLSearchParams();
            if (jobId) queryParams.append('job_id', jobId);
            if (signed) queryParams.append('signed', 'true');
            
            const endpoint = `/api/applications${queryParams.toString() ? '?' + queryParams.toString() : ''}`;
            const data = await apiRequest(endpoint);
            
            return { success: true, applications: data.applications };
        } catch (error) {
            console.error('Fetch applications error:', error);
            return { success: false, error: error.message };
        }
    },
    
    // Fetch application by ID
    async fetchApplicationById(applicationId) {
        try {
            const data = await apiRequest(`/api/application/${applicationId}`);
            return { success: true, application: data.application };
        } catch (error) {
            console.error('Fetch application error:', error);
            return { success: false, error: error.message };
        }
    },
    
    // Trigger AI evaluation for application
    async evaluateApplication(applicationId) {
        try {
            const data = await apiRequest('/api/evaluate', {
                method: 'POST',
                body: JSON.stringify({ application_id: applicationId })
            });
            
            return { success: true, evaluation: data };
        } catch (error) {
            console.error('Evaluate application error:', error);
            return { success: false, error: error.message };
        }
    }
};

// AI and Analytics Functions
const AIService = {
    // Convert natural language to SQL
    async nlpToSql(query) {
        try {
            const data = await apiRequest('/api/nlpsql', {
                method: 'POST',
                body: JSON.stringify({ query })
            });
            
            return { success: true, result: data };
        } catch (error) {
            console.error('NLP to SQL error:', error);
            return { success: false, error: error.message };
        }
    }
};

// Email Functions
const EmailService = {
    // Send email to candidate
    async sendEmail(applicationId, subject, body, fromAlias = 'Hiring Portal') {
        try {
            const data = await apiRequest('/api/email/send', {
                method: 'POST',
                body: JSON.stringify({
                    application_id: applicationId,
                    subject,
                    body,
                    from_alias: fromAlias
                })
            });
            
            return { success: true, result: data };
        } catch (error) {
            console.error('Send email error:', error);
            return { success: false, error: error.message };
        }
    }
};

// Export services for use in other scripts
window.SupabaseServices = {
    AuthService,
    JobService,
    ApplicationService,
    AIService,
    EmailService
};

// Initialize Supabase when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('Supabase services initialized');
    
    // You can add initialization logic here
    // For example, checking if user is already logged in
    AuthService.getCurrentSession().then(result => {
        if (result.success && result.session) {
            console.log('User is logged in:', result.session.user);
        } else {
            console.log('No active session');
        }
    });
});
