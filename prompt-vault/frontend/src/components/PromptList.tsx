import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { supabase } from '../lib/supabase'
import { Prompt } from '../types/database'
import { Plus, Edit, Trash2, Search, Filter, Grid, List, Tag, Calendar, Eye, EyeOff, FileText } from 'lucide-react'

export default function PromptList() {
  const [prompts, setPrompts] = useState<Prompt[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null)
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid')

  useEffect(() => {
    loadPrompts()
  }, [])

  const loadPrompts = async () => {
    try {
      const { data: { user } } = await supabase.auth.getUser()
      if (!user) return

      const { data, error } = await supabase
        .from('prompts')
        .select('*')
        .eq('user_id', user.id)
        .order('updated_at', { ascending: false })

      if (error) throw error
      setPrompts(data || [])
    } catch (error: any) {
      console.error('Error loading prompts:', error)
      setError('Failed to load prompts: ' + (error.message || 'Unknown error'))
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to delete this prompt?')) return

    try {
      const { error } = await supabase
        .from('prompts')
        .delete()
        .eq('id', id)

      if (error) throw error
      loadPrompts()
    } catch (error: any) {
      console.error('Error deleting prompt:', error)
      setError('Failed to delete prompt: ' + (error.message || 'Unknown error'))
    }
  }

  // Get unique categories for filter
  const categories = Array.from(new Set(prompts.map(p => p.category).filter(Boolean))) as string[]

  const filteredPrompts = prompts.filter((prompt) => {
    const matchesSearch = 
      prompt.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      prompt.content.toLowerCase().includes(searchQuery.toLowerCase()) ||
      prompt.description?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      prompt.tags?.some(tag => tag.toLowerCase().includes(searchQuery.toLowerCase()))
    
    const matchesCategory = !selectedCategory || prompt.category === selectedCategory
    
    return matchesSearch && matchesCategory
  })

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-400">Loading prompts...</div>
      </div>
    )
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold text-white">My Prompts</h1>
          <p className="text-gray-400 text-sm mt-1">
            {filteredPrompts.length} {filteredPrompts.length === 1 ? 'prompt' : 'prompts'}
            {selectedCategory && ` in ${selectedCategory}`}
          </p>
        </div>
        <Link
          to="/prompts/new"
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
        >
          <Plus className="w-5 h-5" />
          New Prompt
        </Link>
      </div>

      {error && (
        <div className="mb-4 p-4 bg-red-900/20 border border-red-500/50 rounded-lg text-red-200">
          <p className="font-semibold">Error</p>
          <p className="text-sm">{error}</p>
          <button
            onClick={() => setError(null)}
            className="mt-2 text-xs underline hover:no-underline"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Search and Filters */}
      <div className="mb-6 space-y-4">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
          <input
            type="text"
            placeholder="Search prompts by title, content, description, or tags..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
        </div>

        {/* Category Filter and View Toggle */}
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-gray-400" />
            <span className="text-sm text-gray-400">Category:</span>
          </div>
          <button
            onClick={() => setSelectedCategory(null)}
            className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
              !selectedCategory
                ? 'bg-blue-600 text-white'
                : 'bg-gray-800 text-gray-300 hover:bg-gray-700'
            }`}
          >
            All
          </button>
          {categories.map((category) => (
            <button
              key={category}
              onClick={() => setSelectedCategory(category)}
              className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                selectedCategory === category
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-800 text-gray-300 hover:bg-gray-700'
              }`}
            >
              {category}
            </button>
          ))}
          
          <div className="ml-auto flex items-center gap-2 bg-gray-800 rounded-lg p-1 border border-gray-700">
            <button
              onClick={() => setViewMode('grid')}
              className={`p-2 rounded transition-colors ${
                viewMode === 'grid' ? 'bg-blue-600 text-white' : 'text-gray-400 hover:text-white'
              }`}
              title="Grid view"
            >
              <Grid className="w-4 h-4" />
            </button>
            <button
              onClick={() => setViewMode('list')}
              className={`p-2 rounded transition-colors ${
                viewMode === 'list' ? 'bg-blue-600 text-white' : 'text-gray-400 hover:text-white'
              }`}
              title="List view"
            >
              <List className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {filteredPrompts.length === 0 ? (
        <div className="text-center py-16 bg-gray-800 rounded-xl border border-gray-700">
          <div className="max-w-md mx-auto">
            <FileText className="w-16 h-16 text-gray-600 mx-auto mb-4" />
            <p className="text-gray-400 mb-2 text-lg">
              {searchQuery || selectedCategory ? 'No prompts match your filters.' : "You haven't created any prompts yet."}
            </p>
            <p className="text-gray-500 text-sm mb-6">
              {searchQuery || selectedCategory 
                ? 'Try adjusting your search or filters.' 
                : 'Get started by creating your first prompt template.'}
            </p>
            {!searchQuery && !selectedCategory && (
              <Link
                to="/prompts/new"
                className="inline-flex items-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
              >
                <Plus className="w-5 h-5" />
                Create Your First Prompt
              </Link>
            )}
          </div>
        </div>
      ) : viewMode === 'grid' ? (
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {filteredPrompts.map((prompt) => (
            <div
              key={prompt.id}
              className="group bg-gray-800 rounded-xl border border-gray-700 p-6 hover:border-blue-500/50 hover:shadow-lg hover:shadow-blue-500/10 transition-all duration-200 flex flex-col"
            >
              <div className="flex items-start justify-between mb-3">
                <div className="flex-1 min-w-0">
                  <h3 className="text-lg font-semibold text-white mb-1 truncate group-hover:text-blue-400 transition-colors">
                    {prompt.title}
                  </h3>
                  {prompt.category && (
                    <span className="inline-flex items-center gap-1 px-2.5 py-1 bg-blue-900/30 text-blue-300 text-xs rounded-full border border-blue-700/30">
                      <Tag className="w-3 h-3" />
                      {prompt.category}
                    </span>
                  )}
                </div>
                <div className="flex items-center gap-1 ml-2">
                  {prompt.is_public ? (
                    <Eye className="w-4 h-4 text-green-400" title="Public" />
                  ) : (
                    <EyeOff className="w-4 h-4 text-gray-500" title="Private" />
                  )}
                </div>
              </div>
              
              {prompt.description && (
                <p className="text-gray-400 text-sm mb-3 line-clamp-2">
                  {prompt.description}
                </p>
              )}
              
              <p className="text-gray-500 text-xs mb-4 line-clamp-3 flex-1 font-mono bg-gray-900/50 p-2 rounded">
                {prompt.content}
              </p>
              
              {prompt.tags && prompt.tags.length > 0 && (
                <div className="flex flex-wrap gap-1.5 mb-4">
                  {prompt.tags.slice(0, 3).map((tag, idx) => (
                    <span
                      key={idx}
                      className="px-2 py-0.5 bg-gray-700/50 text-gray-300 text-xs rounded border border-gray-600/50"
                    >
                      {tag}
                    </span>
                  ))}
                  {prompt.tags.length > 3 && (
                    <span className="px-2 py-0.5 text-gray-500 text-xs">
                      +{prompt.tags.length - 3}
                    </span>
                  )}
                </div>
              )}
              
              <div className="flex justify-between items-center mt-auto pt-4 border-t border-gray-700">
                <div className="flex items-center gap-2 text-xs text-gray-500">
                  <Calendar className="w-3.5 h-3.5" />
                  <span>{new Date(prompt.updated_at).toLocaleDateString()}</span>
                </div>
                <div className="flex gap-1">
                  <Link
                    to={`/prompts/${prompt.id}`}
                    className="p-2 text-gray-400 hover:text-blue-400 hover:bg-blue-500/10 rounded-lg transition-colors"
                    title="Edit"
                  >
                    <Edit className="w-4 h-4" />
                  </Link>
                  <button
                    onClick={() => handleDelete(prompt.id)}
                    className="p-2 text-gray-400 hover:text-red-400 hover:bg-red-500/10 rounded-lg transition-colors"
                    title="Delete"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="space-y-3">
          {filteredPrompts.map((prompt) => (
            <div
              key={prompt.id}
              className="group bg-gray-800 rounded-lg border border-gray-700 p-4 hover:border-blue-500/50 transition-all duration-200"
            >
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-3 mb-2">
                    <h3 className="text-lg font-semibold text-white group-hover:text-blue-400 transition-colors">
                      {prompt.title}
                    </h3>
                    {prompt.category && (
                      <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-blue-900/30 text-blue-300 text-xs rounded-full">
                        <Tag className="w-3 h-3" />
                        {prompt.category}
                      </span>
                    )}
                    {prompt.is_public ? (
                      <Eye className="w-4 h-4 text-green-400" title="Public" />
                    ) : (
                      <EyeOff className="w-4 h-4 text-gray-500" title="Private" />
                    )}
                  </div>
                  {prompt.description && (
                    <p className="text-gray-400 text-sm mb-2">
                      {prompt.description}
                    </p>
                  )}
                  <p className="text-gray-500 text-xs mb-2 line-clamp-2 font-mono bg-gray-900/50 p-2 rounded">
                    {prompt.content}
                  </p>
                  <div className="flex items-center gap-4 text-xs text-gray-500">
                    <div className="flex items-center gap-1">
                      <Calendar className="w-3.5 h-3.5" />
                      {new Date(prompt.updated_at).toLocaleDateString()}
                    </div>
                    {prompt.tags && prompt.tags.length > 0 && (
                      <div className="flex items-center gap-1.5">
                        {prompt.tags.slice(0, 3).map((tag, idx) => (
                          <span key={idx} className="px-1.5 py-0.5 bg-gray-700/50 text-gray-400 rounded text-xs">
                            {tag}
                          </span>
                        ))}
                        {prompt.tags.length > 3 && (
                          <span className="text-gray-500">+{prompt.tags.length - 3}</span>
                        )}
                      </div>
                    )}
                  </div>
                </div>
                <div className="flex gap-1">
                  <Link
                    to={`/prompts/${prompt.id}`}
                    className="p-2 text-gray-400 hover:text-blue-400 hover:bg-blue-500/10 rounded-lg transition-colors"
                    title="Edit"
                  >
                    <Edit className="w-4 h-4" />
                  </Link>
                  <button
                    onClick={() => handleDelete(prompt.id)}
                    className="p-2 text-gray-400 hover:text-red-400 hover:bg-red-500/10 rounded-lg transition-colors"
                    title="Delete"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

