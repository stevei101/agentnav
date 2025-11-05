import { useState } from 'react'
import { supabase, getGoogleClientId } from '../lib/supabase'
import { LogIn } from 'lucide-react'

// Get Supabase URL for checking configuration
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

export default function Login() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  // Note: googleClientId is not required for signInWithOAuth
  // It's only needed if using Google's pre-built buttons (which we're not using)
  const googleClientId = getGoogleClientId()

  const handleGoogleLogin = async () => {
    try {
      setLoading(true)
      setError(null)

      // According to Supabase docs, signInWithOAuth doesn't require Client ID in frontend
      // The Client ID and Secret are configured in Supabase Dashboard
      const { data, error } = await supabase.auth.signInWithOAuth({
        provider: 'google',
        options: {
          redirectTo: `${window.location.origin}/`,
          queryParams: {
            access_type: 'offline',
            prompt: 'consent',
          },
        },
      })

      if (error) throw error
      // Note: For implicit flow, the user will be redirected automatically
      // No need to handle data here as redirect happens automatically
    } catch (error: any) {
      console.error('Login error:', error)
      setError(error.error_description || error.message || 'Failed to sign in. Please check your configuration.')
      setLoading(false)
    }
    // Note: Don't set loading to false on success - user will be redirected
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-900 via-blue-900 to-gray-900">
      <div className="max-w-md w-full mx-4">
        <div className="bg-white/10 backdrop-blur-lg rounded-2xl shadow-2xl p-8 border border-white/20">
          <div className="text-center mb-8">
            <div className="inline-flex items-center justify-center w-16 h-16 bg-blue-500 rounded-full mb-4">
              <LogIn className="w-8 h-8 text-white" />
            </div>
            <h1 className="text-3xl font-bold text-white mb-2">Prompt Vault</h1>
            <p className="text-gray-300">AI Prompt Management System</p>
          </div>

          <div className="space-y-4">
            {error && (
              <div className="bg-red-500/20 border border-red-500/50 rounded-lg p-4 text-red-200 text-sm">
                {error}
              </div>
            )}
            
            {!supabaseUrl || !supabaseAnonKey ? (
              <div className="bg-yellow-500/20 border border-yellow-500/50 rounded-lg p-4 text-yellow-200 text-sm space-y-2">
                <p className="font-semibold">⚠️ Configuration Required</p>
                <p>Please create a <code className="bg-yellow-900/50 px-1 rounded">.env.local</code> file in the frontend directory with:</p>
                <pre className="bg-black/30 p-2 rounded text-xs mt-2 overflow-x-auto">
{`VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your_anon_key
VITE_GOOGLE_CLIENT_ID=your_google_client_id`}
                </pre>
                <p className="text-xs mt-2">See <code className="bg-yellow-900/50 px-1 rounded">QUICK_START.md</code> for setup instructions.</p>
              </div>
            ) : (
              <button
                onClick={handleGoogleLogin}
                disabled={loading}
                className="w-full flex items-center justify-center gap-3 bg-white text-gray-900 px-6 py-3 rounded-lg font-semibold hover:bg-gray-100 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? (
                  <div className="w-5 h-5 border-2 border-gray-900 border-t-transparent rounded-full animate-spin" />
                ) : (
                  <>
                    <svg className="w-5 h-5" viewBox="0 0 24 24">
                      <path
                        fill="currentColor"
                        d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                      />
                      <path
                        fill="currentColor"
                        d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                      />
                      <path
                        fill="currentColor"
                        d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                      />
                      <path
                        fill="currentColor"
                        d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                      />
                    </svg>
                    Sign in with Google
                  </>
                )}
              </button>
            )}
          </div>

          <p className="mt-6 text-center text-sm text-gray-400">
            Secure authentication powered by Supabase
          </p>
        </div>
      </div>
    </div>
  )
}

