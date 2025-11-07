import { ReactNode } from 'react';
import { Session } from '@supabase/supabase-js';
import { Link, useLocation } from 'react-router-dom';
import { supabase } from '../lib/supabase';
import { Plus, LogOut, FileText } from 'lucide-react';

interface LayoutProps {
  children: ReactNode;
  session: Session;
}

export default function Layout({ children, session }: LayoutProps) {
  const location = useLocation();

  const handleLogout = async () => {
    await supabase.auth.signOut();
  };

  return (
    <div className="min-h-screen bg-gray-900">
      <nav className="bg-gray-800 border-b border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <Link
                to="/"
                className="flex items-center gap-2 text-white font-bold text-xl"
              >
                <FileText className="w-6 h-6" />
                Prompt Vault
              </Link>
              <div className="ml-10 flex items-baseline space-x-4">
                <Link
                  to="/prompts"
                  className={`px-3 py-2 rounded-md text-sm font-medium ${
                    location.pathname === '/prompts' ||
                    location.pathname === '/'
                      ? 'bg-gray-900 text-white'
                      : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                  }`}
                >
                  My Prompts
                </Link>
              </div>
            </div>
            <div className="flex items-center gap-4">
              <Link
                to="/prompts/new"
                className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
              >
                <Plus className="w-4 h-4" />
                New Prompt
              </Link>
              <div className="flex items-center gap-3">
                <span className="text-sm text-gray-300">
                  {session.user.email}
                </span>
                <button
                  onClick={handleLogout}
                  className="flex items-center gap-2 px-3 py-2 text-gray-300 hover:text-white hover:bg-gray-700 rounded-md transition-colors"
                >
                  <LogOut className="w-4 h-4" />
                  Logout
                </button>
              </div>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {children}
      </main>
    </div>
  );
}
