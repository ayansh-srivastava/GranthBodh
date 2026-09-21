export type UserCreateRequest = {
  email: string
  password: string
}

export type UserLoginRequest = {
  email: string
  password: string
}

export type TokenResponse = {
  access_token: string
  refresh_token: string
  token_type: string
}

export type DocumentUploadResponse = {
  id: string
  filename: string
  content_type: string
  message: string
}


export type GetDocumentsResponse = {
  documents: {
    id: string
    filename: string
  }[]
  total_count: number
}

export type GetConversationsResponse = {
  conversations: {
    id: string
    title: string
    created_at: string
  }[]
  total_pages: number,
}

export type QueryRequest = {
  question: string
  conversation_id?: string
}

export type QueryResponse = {
  answer: MessageItem
  sources: Record<string, unknown>[]
  conversation_id: string
}

export type ConversationItem = {
  id: string
  title: string
  created_at: string
}

export type MessageItem = {
  id: string
  created_at: string
  conversation_id: string
  user_id: string

  role: 'user' | 'assistant'
  content: string
}

export type GetMessagesResponse = {
  messages: MessageItem[]
  total_pages: number
}