import request from '@/utils/request'

export interface LoginParams {
  username: string
  password: string
}

export interface LoginResponse {
  access_token: string
  token_type: string
  expires_in: number
  user: {
    id: string
    username: string
    email: string
    full_name: string
    role: string
    permissions: string[]
  }
}

export function login(data: LoginParams) {
  // Backend expects JSON format with UserLogin schema
  return request({
    url: '/auth/login',
    method: 'post',
    data: {
      username: data.username,
      password: data.password
    }
  })
}

export function logout() {
  return request({
    url: '/auth/logout',
    method: 'post'
  })
}

export function getUserInfo() {
  return request({
    url: '/auth/me',
    method: 'get'
  })
}