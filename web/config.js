// Derive backend URL from current origin to avoid Private Network Access/CORS issues
// when front-end is served at an IP/domain different from localhost.
window.APP_CONFIG = {
  BACKEND_URL: (typeof window !== 'undefined' && window.location && window.location.origin) ? window.location.origin : 'http://localhost:8000',
  SUPABASE_URL: 'https://wjxfmxsertvxtuuugqsq.supabase.co',
  SUPABASE_ANON_KEY: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6IndqeGZteHNlcnR2eHR1dXVncXNxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjE2MjM0MDcsImV4cCI6MjA3NzE5OTQwN30.8jvp4tjg80V0TEzT00n4V_kO_C2EgRC-6mJk9iFUddw',
};
