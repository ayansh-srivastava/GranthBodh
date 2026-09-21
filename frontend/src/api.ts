import type {
  DocumentUploadResponse,
  GetDocumentsResponse,
  QueryResponse,
  TokenResponse,
  GetConversationsResponse,
  GetMessagesResponse,
} from './types'
import { getToken, clearSession, setAccessToken, getRefreshToken } from './utils.ts'

const API_BASE = (import.meta.env.VITE_API_URL as string | undefined) ?? ''

export class ApiError extends Error {
  status: number

  constructor(message: string, status: number) {
    super(message)
    this.status = status
  }
}

function parseDetail(body: unknown): string {
  if (body && typeof body === 'object' && 'detail' in body) {
    const detail = (body as { detail: unknown }).detail
    if (typeof detail === 'string') return detail
    if (Array.isArray(detail)) {
      return detail
        .map((item) =>
          typeof item === 'object' && item && 'msg' in item
            ? String((item as { msg: unknown }).msg)
            : String(item),
        )
        .join(', ')
    }
  }
  return 'Request failed'
}

async function request<T>(
  path: string,
  init: RequestInit = {},
  auth = true,
): Promise<T> {
  const headers = new Headers(init.headers)

  if (auth) {
    let token = getToken()

    if (!token) {
      try {
        token = await refreshAccessToken()
      } catch {
        clearSession()
        window.location.href = '/'
        throw new ApiError('Session expired', 401)
      }
    }

    headers.set('Authorization', `Bearer ${token}`)
  }

  let response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers,
  })

  if (auth && response.status === 401) {
    try {
      const newToken = await refreshAccessToken()

      headers.set('Authorization', `Bearer ${newToken}`)

      response = await fetch(`${API_BASE}${path}`, {
        ...init,
        headers,
      })
    } catch {
      clearSession()
      throw new ApiError('Session expired', 401)
    }
  }

  const raw = await response.text()

  let body: unknown = null

  if (raw) {
    try {
      body = JSON.parse(raw)
    } catch {
      body = raw
    }
  }

  if (!response.ok) {
    throw new ApiError(parseDetail(body), response.status)
  }

  return body as T
}

export async function login(email: string, password: string): Promise<TokenResponse> {
  return await request<TokenResponse>(
    '/api/v1/users/login',
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    },
    false,
  )
}

export async function signup(email: string, password: string): Promise<TokenResponse> {
  return await request<TokenResponse>(
    '/api/v1/users/signup',
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    },
    false,
  )
}

export async function uploadDocument(file: File): Promise<DocumentUploadResponse> {
  const form = new FormData()
  form.append('file', file)
  return await request<DocumentUploadResponse>('/api/v1/documents/upload', {
    method: 'POST',
    body: form,
  })
}

export async function getDocuments(page: number = 1): Promise<GetDocumentsResponse> {
  return await request<GetDocumentsResponse>(`/api/v1/documents?page=${page}`, {
    method: 'GET',
  })
}

export async function getConversations(page: number = 1): Promise<GetConversationsResponse> {
  return await request<GetConversationsResponse>(`/api/v1/rag/conversations?page=${page}`, {
    method: 'GET',
  })
}

export function getMessages(conversationId: string, page: number = 1): Promise<GetMessagesResponse> {
  return request<GetMessagesResponse>(`/api/v1/rag/messages?conversation_id=${conversationId}&page=${page}`, {
    method: 'GET',
  })
}

export function getAnswer(question: string, conversation_id: string | null): Promise<QueryResponse> {
  return request<QueryResponse>('/api/v1/rag/getAnswer', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question, conversation_id }),
  })
}

async function refreshAccessToken(): Promise<string> {
  const refreshToken = getRefreshToken()

  if (!refreshToken) {
    throw new ApiError('Session expired', 401)
  }

  const response = await fetch(`${API_BASE}/users/refresh`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      refreshToken,
    }),
  })

  if (!response.ok) {
    clearSession()
    throw new ApiError('Session expired', 401)
  }

  const data = await response.json()

  setAccessToken(data.accessToken)

  return data.accessToken
}
