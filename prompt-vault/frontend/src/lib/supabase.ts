import { createClient } from '@supabase/supabase-js'

// Get Supabase credentials from window (injected at runtime by Dockerfile)
// or from environment variables (for local development)
const getSupabaseUrl = (): string => {
  if (typeof window !== 'undefined' && (window as any).SUPABASE_URL) {
    return (window as any).SUPABASE_URL
  }
  return import.meta.env.VITE_SUPABASE_URL || ''
}

const getSupabaseAnonKey = (): string => {
  if (typeof window !== 'undefined' && (window as any).SUPABASE_ANON_KEY) {
    return (window as any).SUPABASE_ANON_KEY
  }
  return import.meta.env.VITE_SUPABASE_ANON_KEY || ''
}

const supabaseUrl = getSupabaseUrl()
const supabaseAnonKey = getSupabaseAnonKey()

// Use placeholder values if credentials are missing to prevent app crash
const safeSupabaseUrl = supabaseUrl || 'https://placeholder.supabase.co'
const safeSupabaseAnonKey = supabaseAnonKey || 'placeholder-key'

if (!supabaseUrl || !supabaseAnonKey) {
  console.warn('⚠️ Missing Supabase credentials. Please configure VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY in .env.local')
  console.warn('   App will run but authentication will not work.')
}

export const supabase = createClient(safeSupabaseUrl, safeSupabaseAnonKey, {
  auth: {
    autoRefreshToken: true,
    persistSession: true,
    detectSessionInUrl: true,
  },
})

// Get Google OAuth Client ID for Supabase Sign-in
export const getGoogleClientId = (): string | undefined => {
  if (typeof window !== 'undefined' && (window as any).NEXT_PUBLIC_GOOGLE_CLIENT_ID) {
    return (window as any).NEXT_PUBLIC_GOOGLE_CLIENT_ID
  }
  return import.meta.env.VITE_GOOGLE_CLIENT_ID
}

