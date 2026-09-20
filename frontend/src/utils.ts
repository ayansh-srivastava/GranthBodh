import type {
  TokenResponse,
} from './types'

export function getToken(): string | null {
  return localStorage.getItem('access_token')
}

export function getRefreshToken(): string | null {
  return localStorage.getItem('refresh_token')
}

export function setSession(tokens: TokenResponse): void {
  localStorage.setItem('access_token', tokens.access_token)
  localStorage.setItem('refresh_token', tokens.refresh_token)
}

export function setAccessToken(token: string): void {
  localStorage.setItem('access_token', token)
}

export function clearSession(): void {
  localStorage.removeItem('access_token')
  localStorage.removeItem('refresh_token')
}

export function isLoggedIn(): boolean {
  return Boolean(getToken())
}
