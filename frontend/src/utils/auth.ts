import Cookies from 'js-cookie'

const TokenKey = 'soc_access_token'
const RefreshTokenKey = 'soc_refresh_token'
const CSRFTokenKey = 'soc_csrf_token'

export function getToken(): string | undefined {
  return Cookies.get(TokenKey)
}

export function setToken(token: string): void {
  Cookies.set(TokenKey, token, { expires: 7 })
}

export function removeToken(): void {
  Cookies.remove(TokenKey)
  Cookies.remove(RefreshTokenKey)
}

export function getRefreshToken(): string | undefined {
  return Cookies.get(RefreshTokenKey)
}

export function setRefreshToken(token: string): void {
  Cookies.set(RefreshTokenKey, token, { expires: 30 })
}

// CSRF Token Management
export function getCsrfToken(): string | undefined {
  return Cookies.get(CSRFTokenKey)
}

export function setCsrfToken(token: string): void {
  Cookies.set(CSRFTokenKey, token, { expires: 1 }) // 1 day
}

export function removeCsrfToken(): void {
  Cookies.remove(CSRFTokenKey)
}

// Fetch CSRF token from backend
export async function fetchCsrfToken(): Promise<string | null> {
  try {
    const response = await fetch('/csrf-token', {
      method: 'GET',
      credentials: 'include'
    })

    if (response.ok) {
      // CSRF token is usually set in cookie or response header
      const csrfFromHeader = response.headers.get('X-CSRF-Token')
      const csrfFromCookie = Cookies.get('csrf_token') || Cookies.get('csrftoken')

      const token = csrfFromHeader || csrfFromCookie

      if (token) {
        setCsrfToken(token)
        return token
      }
    }
    return null
  } catch (error) {
    console.error('Failed to fetch CSRF token:', error)
    return null
  }
}