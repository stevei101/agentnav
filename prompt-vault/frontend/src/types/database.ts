// Database types for Prompt Vault
export interface Prompt {
  id: string
  title: string
  content: string
  description?: string
  category?: string
  tags?: string[]
  created_at: string
  updated_at: string
  user_id: string
  is_public?: boolean
}

export interface PromptInsert {
  title: string
  content: string
  description?: string
  category?: string
  tags?: string[]
  is_public?: boolean
}

export interface PromptUpdate {
  title?: string
  content?: string
  description?: string
  category?: string
  tags?: string[]
  is_public?: boolean
}

