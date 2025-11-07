import { createClient } from '@supabase/supabase-js';

// Get Supabase credentials from window (injected at runtime by Dockerfile)
// or from environment variables (for local development)
const getSupabaseUrl = (): string => {
  if (typeof window !== 'undefined' && (window as any).SUPABASE_URL) {
    return (window as any).SUPABASE_URL;
  }
  return import.meta.env.VITE_SUPABASE_URL || '';
};

const getSupabaseAnonKey = (): string => {
  if (typeof window !== 'undefined' && (window as any).SUPABASE_ANON_KEY) {
    return (window as any).SUPABASE_ANON_KEY;
  }
  return import.meta.env.VITE_SUPABASE_ANON_KEY || '';
};

const supabaseUrl = getSupabaseUrl();
const supabaseAnonKey = getSupabaseAnonKey();

// Fail fast if credentials are missing - prevents silent failures and security issues
if (!supabaseUrl || !supabaseAnonKey) {
  const errorMessage =
    '❌ Missing Supabase credentials. Please configure VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY in .env.local';
  console.error(errorMessage);
  // In development, throw error to make the issue immediately visible
  // In production (Cloud Run), this should never happen as secrets are injected
  if (import.meta.env.DEV) {
    throw new Error(errorMessage);
  }
}

export const supabase = createClient(supabaseUrl, supabaseAnonKey, {
  auth: {
    autoRefreshToken: true,
    persistSession: true,
    detectSessionInUrl: true,
  },
});

// Get Google OAuth Client ID for Supabase Sign-in
