import type { App } from 'vue'

export interface ErrorInfo {
  message: string
  stack?: string
  component?: string
  hook?: string
  timestamp: number
  url: string
  userAgent: string
  userId?: string
  level: 'error' | 'warn' | 'info'
  category: 'js' | 'vue' | 'promise' | 'resource' | 'xhr'
  extra?: Record<string, any>
}

export interface ErrorHandlerOptions {
  dsn?: string // Error reporting service URL
  environment?: string
  version?: string
  userId?: string
  sampleRate?: number // 0-1, percentage of errors to report
  beforeSend?: (errorInfo: ErrorInfo) => ErrorInfo | null
  onError?: (errorInfo: ErrorInfo) => void
}

class ErrorHandler {
  private options: ErrorHandlerOptions
  private errors: ErrorInfo[] = []
  private maxErrors = 100 // Maximum number of errors to keep in memory

  constructor(options: ErrorHandlerOptions = {}) {
    this.options = {
      environment: import.meta.env.MODE,
      version: import.meta.env.VITE_APP_VERSION || '1.0.0',
      sampleRate: 1.0,
      ...options
    }
  }

  // Install error handlers
  install(app: App) {
    // Vue error handler
    app.config.errorHandler = (err: unknown, instance, info) => {
      this.handleVueError(err, instance, info)
    }

    // Global JavaScript error handler
    window.addEventListener('error', (event) => {
      this.handleJsError(event)
    })

    // Unhandled promise rejection handler
    window.addEventListener('unhandledrejection', (event) => {
      this.handlePromiseRejection(event)
    })

    // Resource loading error handler
    window.addEventListener('error', (event) => {
      if (event.target !== window) {
        this.handleResourceError(event)
      }
    }, true)

    // XMLHttpRequest error handler
    this.interceptXHR()

    // Fetch error handler
    this.interceptFetch()
  }

  private handleVueError(err: unknown, instance: any, info: string) {
    const errorInfo: ErrorInfo = {
      message: err instanceof Error ? err.message : String(err),
      stack: err instanceof Error ? err.stack : undefined,
      component: instance?.$options.name || instance?.$options.__name || 'Unknown',
      hook: info,
      timestamp: Date.now(),
      url: window.location.href,
      userAgent: navigator.userAgent,
      userId: this.options.userId,
      level: 'error',
      category: 'vue'
    }

    this.reportError(errorInfo)
  }

  private handleJsError(event: ErrorEvent) {
    const errorInfo: ErrorInfo = {
      message: event.message,
      stack: event.error?.stack,
      timestamp: Date.now(),
      url: window.location.href,
      userAgent: navigator.userAgent,
      userId: this.options.userId,
      level: 'error',
      category: 'js',
      extra: {
        filename: event.filename,
        lineno: event.lineno,
        colno: event.colno
      }
    }

    this.reportError(errorInfo)
  }

  private handlePromiseRejection(event: PromiseRejectionEvent) {
    const errorInfo: ErrorInfo = {
      message: event.reason instanceof Error ? event.reason.message : String(event.reason),
      stack: event.reason instanceof Error ? event.reason.stack : undefined,
      timestamp: Date.now(),
      url: window.location.href,
      userAgent: navigator.userAgent,
      userId: this.options.userId,
      level: 'error',
      category: 'promise'
    }

    this.reportError(errorInfo)
  }

  private handleResourceError(event: Event) {
    const target = event.target as any
    if (!target) return

    const errorInfo: ErrorInfo = {
      message: `Resource loading failed: ${target.src || target.href}`,
      timestamp: Date.now(),
      url: window.location.href,
      userAgent: navigator.userAgent,
      userId: this.options.userId,
      level: 'error',
      category: 'resource',
      extra: {
        resourceUrl: target.src || target.href,
        tagName: target.tagName
      }
    }

    this.reportError(errorInfo)
  }

  private interceptXHR() {
    const originalXHR = window.XMLHttpRequest
    const self = this

    window.XMLHttpRequest = function(...args) {
      const xhr = new originalXHR(...args)
      const originalOpen = xhr.open
      const originalSend = xhr.send

      let requestUrl = ''
      let requestMethod = ''

      xhr.open = function(method: string, url: string, ...rest) {
        requestMethod = method
        requestUrl = url
        return originalOpen.call(this, method, url, ...rest)
      }

      xhr.send = function(...args) {
        xhr.addEventListener('error', () => {
          const errorInfo: ErrorInfo = {
            message: `XHR request failed: ${requestMethod} ${requestUrl}`,
            timestamp: Date.now(),
            url: window.location.href,
            userAgent: navigator.userAgent,
            userId: self.options.userId,
            level: 'error',
            category: 'xhr',
            extra: {
              method: requestMethod,
              requestUrl: requestUrl,
              status: xhr.status,
              statusText: xhr.statusText
            }
          }
          self.reportError(errorInfo)
        })

        return originalSend.call(this, ...args)
      }

      return xhr
    }
  }

  private interceptFetch() {
    const originalFetch = window.fetch
    const self = this

    window.fetch = async function(...args) {
      try {
        const response = await originalFetch.apply(this, args)

        if (!response.ok) {
          const url = typeof args[0] === 'string' ? args[0] : args[0].url
          const errorInfo: ErrorInfo = {
            message: `Fetch request failed: ${response.status} ${response.statusText}`,
            timestamp: Date.now(),
            url: window.location.href,
            userAgent: navigator.userAgent,
            userId: self.options.userId,
            level: 'error',
            category: 'xhr',
            extra: {
              requestUrl: url,
              status: response.status,
              statusText: response.statusText
            }
          }
          self.reportError(errorInfo)
        }

        return response
      } catch (error) {
        const url = typeof args[0] === 'string' ? args[0] : args[0].url
        const errorInfo: ErrorInfo = {
          message: `Fetch request error: ${error instanceof Error ? error.message : String(error)}`,
          stack: error instanceof Error ? error.stack : undefined,
          timestamp: Date.now(),
          url: window.location.href,
          userAgent: navigator.userAgent,
          userId: self.options.userId,
          level: 'error',
          category: 'xhr',
          extra: {
            requestUrl: url
          }
        }
        self.reportError(errorInfo)
        throw error
      }
    }
  }

  private shouldReport(): boolean {
    return Math.random() < (this.options.sampleRate || 1.0)
  }

  private reportError(errorInfo: ErrorInfo) {
    if (!this.shouldReport()) return

    // Apply beforeSend hook
    if (this.options.beforeSend) {
      const modifiedError = this.options.beforeSend(errorInfo)
      if (!modifiedError) return
      errorInfo = modifiedError
    }

    // Store error locally
    this.errors.push(errorInfo)
    if (this.errors.length > this.maxErrors) {
      this.errors.shift() // Remove oldest error
    }

    // Call onError hook
    if (this.options.onError) {
      this.options.onError(errorInfo)
    }

    // Send to external service
    if (this.options.dsn) {
      this.sendToService(errorInfo)
    }

    // Log to console in development
    if (import.meta.env.DEV) {
      console.group(`[Error Handler] ${errorInfo.category} error`)
      console.error(errorInfo.message)
      if (errorInfo.stack) {
        console.error(errorInfo.stack)
      }
      console.log('Error details:', errorInfo)
      console.groupEnd()
    }
  }

  private async sendToService(errorInfo: ErrorInfo) {
    try {
      await fetch(this.options.dsn!, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          ...errorInfo,
          environment: this.options.environment,
          version: this.options.version
        })
      })
    } catch (error) {
      console.warn('Failed to send error to reporting service:', error)
    }
  }

  // Public methods
  public captureException(error: Error, extra?: Record<string, any>) {
    const errorInfo: ErrorInfo = {
      message: error.message,
      stack: error.stack,
      timestamp: Date.now(),
      url: window.location.href,
      userAgent: navigator.userAgent,
      userId: this.options.userId,
      level: 'error',
      category: 'js',
      extra
    }

    this.reportError(errorInfo)
  }

  public captureMessage(message: string, level: 'error' | 'warn' | 'info' = 'info', extra?: Record<string, any>) {
    const errorInfo: ErrorInfo = {
      message,
      timestamp: Date.now(),
      url: window.location.href,
      userAgent: navigator.userAgent,
      userId: this.options.userId,
      level,
      category: 'js',
      extra
    }

    this.reportError(errorInfo)
  }

  public setUserId(userId: string) {
    this.options.userId = userId
  }

  public setExtra(key: string, value: any) {
    // This would be used for setting global extra data
    // Implementation depends on requirements
  }

  public getErrors(): ErrorInfo[] {
    return [...this.errors]
  }

  public clearErrors() {
    this.errors = []
  }
}

// Create singleton instance
export const errorHandler = new ErrorHandler({
  environment: import.meta.env.MODE,
  version: import.meta.env.VITE_APP_VERSION,
  sampleRate: import.meta.env.PROD ? 0.1 : 1.0, // 10% in production, 100% in development
  beforeSend: (errorInfo) => {
    // Filter out some known non-critical errors
    if (errorInfo.message.includes('Non-Error promise rejection captured')) {
      return null
    }
    if (errorInfo.message.includes('ResizeObserver loop limit exceeded')) {
      return null
    }
    return errorInfo
  }
})

// Vue plugin
export default {
  install(app: App, options?: ErrorHandlerOptions) {
    if (options) {
      Object.assign(errorHandler.options, options)
    }
    errorHandler.install(app)

    // Provide error handler to components
    app.provide('$errorHandler', errorHandler)
    app.config.globalProperties.$errorHandler = errorHandler
  }
}