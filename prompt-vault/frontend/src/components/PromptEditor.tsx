import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { supabase } from '../lib/supabase'
import { Prompt, PromptInsert, PromptUpdate } from '../types/database'
import { Save, ArrowLeft } from 'lucide-react'

export default function PromptEditor() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const isNew = !id

  const [loading, setLoading] = useState(!isNew)
  const [saving, setSaving] = useState(false)
  const [prompt, setPrompt] = useState<PromptInsert>({
    title: '',
    content: '',
    description: '',
    category: '',
    tags: [],
    is_public: false,
  })

  useEffect(() => {
    if (id) {
      loadPrompt(id)
    }
  }, [id])

  const loadPrompt = async (promptId: string) => {
    try {
      const { data: { user } } = await supabase.auth.getUser()
      if (!user) return

      const { data, error } = await supabase
        .from('prompts')
        .select('*')
        .eq('id', promptId)
        .eq('user_id', user.id)
        .single()

      if (error) throw error

      if (data) {
        setPrompt({
          title: data.title || '',
          content: data.content || '',
          description: data.description || '',
          category: data.category || '',
          tags: data.tags || [],
          is_public: data.is_public || false,
        })
      }
    } catch (error: any) {
      console.error('Error loading prompt:', error)
      alert('Failed to load prompt: ' + error.message)
      navigate('/prompts')
    } finally {
      setLoading(false)
    }
  }

  const handleSave = async () => {
    if (!prompt.title.trim() || !prompt.content.trim()) {
      alert('Please fill in both title and content.')
      return
    }

    try {
      setSaving(true)
      const { data: { user } } = await supabase.auth.getUser()
      if (!user) {
        alert('You must be logged in to save prompts.')
        return
      }

      if (isNew) {
        const { error } = await supabase
          .from('prompts')
          .insert({
            ...prompt,
            user_id: user.id,
          })

        if (error) throw error
        navigate('/prompts')
      } else {
        const { error } = await supabase
          .from('prompts')
          .update(prompt as PromptUpdate)
          .eq('id', id!)
          .eq('user_id', user.id)

        if (error) throw error
        navigate('/prompts')
      }
    } catch (error: any) {
      console.error('Error saving prompt:', error)
      alert('Failed to save prompt: ' + error.message)
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-400">Loading prompt...</div>
      </div>
    )
  }

  return (
    <div>
      <div className="flex items-center gap-4 mb-6">
        <button
          onClick={() => navigate('/prompts')}
          className="p-2 text-gray-400 hover:text-white hover:bg-gray-800 rounded transition-colors"
        >
          <ArrowLeft className="w-5 h-5" />
        </button>
        <h1 className="text-3xl font-bold text-white">
          {isNew ? 'Create New Prompt' : 'Edit Prompt'}
        </h1>
      </div>

      <div className="bg-gray-800 rounded-lg border border-gray-700 p-6 space-y-6">
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">
            Title *
          </label>
          <input
            type="text"
            value={prompt.title}
            onChange={(e) => setPrompt({ ...prompt, title: e.target.value })}
            className="w-full px-4 py-2 bg-gray-900 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="Enter prompt title..."
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">
            Description
          </label>
          <input
            type="text"
            value={prompt.description}
            onChange={(e) => setPrompt({ ...prompt, description: e.target.value })}
            className="w-full px-4 py-2 bg-gray-900 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="Brief description of the prompt..."
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Category
            </label>
            <input
              type="text"
              value={prompt.category}
              onChange={(e) => setPrompt({ ...prompt, category: e.target.value })}
              className="w-full px-4 py-2 bg-gray-900 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="e.g., Code Generation, Content Writing..."
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Tags (comma-separated)
            </label>
            <input
              type="text"
              value={prompt.tags?.join(', ') || ''}
              onChange={(e) =>
                setPrompt({
                  ...prompt,
                  tags: e.target.value.split(',').map((t) => t.trim()).filter(Boolean),
                })
              }
              className="w-full px-4 py-2 bg-gray-900 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="tag1, tag2, tag3..."
            />
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">
            Prompt Content *
          </label>
          <textarea
            value={prompt.content}
            onChange={(e) => setPrompt({ ...prompt, content: e.target.value })}
            rows={15}
            className="w-full px-4 py-2 bg-gray-900 border border-gray-700 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-sm"
            placeholder="Enter your prompt content here..."
          />
        </div>

        <div className="flex items-center gap-4">
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={prompt.is_public}
              onChange={(e) => setPrompt({ ...prompt, is_public: e.target.checked })}
              className="w-4 h-4 text-blue-600 bg-gray-900 border-gray-700 rounded focus:ring-blue-500"
            />
            <span className="text-sm text-gray-300">Make this prompt public</span>
          </label>
        </div>

        <div className="flex justify-end gap-4 pt-4 border-t border-gray-700">
          <button
            onClick={() => navigate('/prompts')}
            className="px-4 py-2 text-gray-300 hover:text-white transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            disabled={saving || !prompt.title.trim() || !prompt.content.trim()}
            className="flex items-center gap-2 px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {saving ? (
              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
            ) : (
              <Save className="w-4 h-4" />
            )}
            {saving ? 'Saving...' : 'Save Prompt'}
          </button>
        </div>
      </div>
    </div>
  )
}

