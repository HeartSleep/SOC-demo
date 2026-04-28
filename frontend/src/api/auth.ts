import request from '@/utils/request'
import { removeToken } from '@/utils/auth'

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

/**
 * 登出函数 - JWT 无状态，客户端清除 token 即可
 * 后端无需实现 logout 接口
 */
export function logout() {
  // 清除本地存储的 token
  removeToken()
  // 如果后端有 token 黑名单需求，可以取消注释下面代码
  // return request({
  //   url: '/auth/logout',
  //   method: 'post'
  // })
  return Promise.resolve()
}

export function getUserInfo() {
  return request({
    url: '/auth/me',
    method: 'get'
  })
}