// Performance monitoring utilities for SOC Platform
export interface PerformanceMetric {
  name: string
  value: number
  timestamp: number
  category: 'navigation' | 'resource' | 'paint' | 'layout' | 'custom'
  tags?: Record<string, string>
  extra?: Record<string, any>
}

export interface NavigationMetrics {
  dns: number
  tcp: number
  ssl: number
  ttfb: number // Time to First Byte
  domContentLoaded: number
  domInteractive: number
  domComplete: number
  loadComplete: number
  fcp: number // First Contentful Paint
  lcp: number // Largest Contentful Paint
  fid: number // First Input Delay
  cls: number // Cumulative Layout Shift
  tti: number // Time to Interactive
}

export interface ResourceMetrics {
  name: string
  type: string
  size: number
  duration: number
  startTime: number
  endTime: number
}

export interface CustomMetrics {
  apiResponseTime: Record<string, number[]>
  componentRenderTime: Record<string, number[]>
  routeChangeTime: Record<string, number[]>
  memoryUsage: number[]
  errorCount: number
  userInteractions: number
}

class PerformanceMonitor {
  private metrics: PerformanceMetric[] = []
  private customMetrics: CustomMetrics = {
    apiResponseTime: {},
    componentRenderTime: {},
    routeChangeTime: {},
    memoryUsage: [],
    errorCount: 0,
    userInteractions: 0
  }
  private observers: PerformanceObserver[] = []
  private isSupported = typeof window !== 'undefined' && 'performance' in window

  constructor() {
    if (this.isSupported) {
      this.initializeObservers()
      this.collectNavigationMetrics()
      this.collectResourceMetrics()
      this.collectWebVitals()
      this.monitorMemoryUsage()
    }
  }

  private initializeObservers() {
    try {
      // Long task observer
      if ('PerformanceObserver' in window) {
        const longTaskObserver = new PerformanceObserver((list) => {
          for (const entry of list.getEntries()) {
            this.addMetric({
              name: 'long-task',
              value: entry.duration,
              timestamp: Date.now(),
              category: 'custom',
              extra: {
                startTime: entry.startTime,
                name: entry.name
              }
            })
          }
        })

        try {
          longTaskObserver.observe({ entryTypes: ['longtask'] })
          this.observers.push(longTaskObserver)
        } catch (e) {
          console.warn('Long task observer not supported')
        }

        // Layout shift observer
        const layoutShiftObserver = new PerformanceObserver((list) => {
          let clsValue = 0
          for (const entry of list.getEntries()) {
            if (!entry.hadRecentInput) {
              clsValue += (entry as any).value
            }
          }
          if (clsValue > 0) {
            this.addMetric({
              name: 'cls',
              value: clsValue,
              timestamp: Date.now(),
              category: 'layout'
            })
          }
        })

        try {
          layoutShiftObserver.observe({ entryTypes: ['layout-shift'] })
          this.observers.push(layoutShiftObserver)
        } catch (e) {
          console.warn('Layout shift observer not supported')
        }

        // Paint observer
        const paintObserver = new PerformanceObserver((list) => {
          for (const entry of list.getEntries()) {
            this.addMetric({
              name: entry.name,
              value: entry.startTime,
              timestamp: Date.now(),
              category: 'paint'
            })
          }
        })

        try {
          paintObserver.observe({ entryTypes: ['paint'] })
          this.observers.push(paintObserver)
        } catch (e) {
          console.warn('Paint observer not supported')
        }
      }
    } catch (error) {
      console.warn('Failed to initialize performance observers:', error)
    }
  }

  private collectNavigationMetrics() {
    if (!this.isSupported || !performance.timing) return

    const timing = performance.timing
    const navigation = performance.navigation

    const metrics: Partial<NavigationMetrics> = {
      dns: timing.domainLookupEnd - timing.domainLookupStart,
      tcp: timing.connectEnd - timing.connectStart,
      ssl: timing.secureConnectionStart > 0 ? timing.connectEnd - timing.secureConnectionStart : 0,
      ttfb: timing.responseStart - timing.requestStart,
      domContentLoaded: timing.domContentLoadedEventEnd - timing.navigationStart,
      domInteractive: timing.domInteractive - timing.navigationStart,
      domComplete: timing.domComplete - timing.navigationStart,
      loadComplete: timing.loadEventEnd - timing.navigationStart
    }

    Object.entries(metrics).forEach(([key, value]) => {
      if (value >= 0) {
        this.addMetric({
          name: key,
          value,
          timestamp: Date.now(),
          category: 'navigation'
        })
      }
    })

    // Navigation type
    this.addMetric({
      name: 'navigation-type',
      value: navigation.type,
      timestamp: Date.now(),
      category: 'navigation'
    })
  }

  private collectResourceMetrics() {
    if (!this.isSupported) return

    const resources = performance.getEntriesByType('resource') as PerformanceResourceTiming[]
    resources.forEach((resource) => {
      this.addMetric({
        name: 'resource-load',
        value: resource.duration,
        timestamp: Date.now(),
        category: 'resource',
        tags: {
          name: resource.name,
          type: resource.initiatorType
        },
        extra: {
          size: resource.transferSize,
          startTime: resource.startTime,
          endTime: resource.responseEnd
        }
      })
    })
  }

  private collectWebVitals() {
    if (!this.isSupported) return

    // Largest Contentful Paint (LCP)
    this.observeWebVital('largest-contentful-paint', (entry) => {
      this.addMetric({
        name: 'lcp',
        value: entry.startTime,
        timestamp: Date.now(),
        category: 'paint'
      })
    })

    // First Input Delay (FID)
    this.observeWebVital('first-input', (entry) => {
      this.addMetric({
        name: 'fid',
        value: entry.processingStart - entry.startTime,
        timestamp: Date.now(),
        category: 'custom'
      })
    })

    // Time to Interactive (TTI)
    this.calculateTTI()
  }

  private observeWebVital(entryType: string, callback: (entry: PerformanceEntry) => void) {
    try {
      const observer = new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          callback(entry)
        }
      })
      observer.observe({ entryTypes: [entryType] })
      this.observers.push(observer)
    } catch (e) {
      console.warn(`Web vital observer for ${entryType} not supported`)
    }
  }

  private calculateTTI() {
    // Simplified TTI calculation
    setTimeout(() => {
      const longTasks = performance.getEntriesByType('longtask')
      const lastLongTask = longTasks[longTasks.length - 1]
      const tti = lastLongTask ? lastLongTask.startTime + lastLongTask.duration : performance.timing.domContentLoadedEventEnd

      this.addMetric({
        name: 'tti',
        value: tti,
        timestamp: Date.now(),
        category: 'custom'
      })
    }, 5000)
  }

  private monitorMemoryUsage() {
    if (!this.isSupported || !('memory' in performance)) return

    const collectMemory = () => {
      const memory = (performance as any).memory
      if (memory) {
        const usage = memory.usedJSHeapSize / memory.totalJSHeapSize * 100
        this.customMetrics.memoryUsage.push(usage)

        this.addMetric({
          name: 'memory-usage',
          value: usage,
          timestamp: Date.now(),
          category: 'custom',
          extra: {
            used: memory.usedJSHeapSize,
            total: memory.totalJSHeapSize,
            limit: memory.jsHeapSizeLimit
          }
        })
      }
    }

    // Collect memory usage every 30 seconds
    collectMemory()
    setInterval(collectMemory, 30000)
  }

  // Public methods
  public startTiming(name: string): () => void {
    const startTime = performance.now()
    const startMark = `${name}-start`

    if (this.isSupported) {
      performance.mark(startMark)
    }

    return () => {
      const endTime = performance.now()
      const endMark = `${name}-end`
      const measureName = `${name}-measure`

      if (this.isSupported) {
        performance.mark(endMark)
        performance.measure(measureName, startMark, endMark)
      }

      const duration = endTime - startTime
      this.addMetric({
        name,
        value: duration,
        timestamp: Date.now(),
        category: 'custom'
      })

      return duration
    }
  }

  public timeFunction<T extends (...args: any[]) => any>(fn: T, name?: string): T {
    const functionName = name || fn.name || 'anonymous'

    return ((...args: Parameters<T>) => {
      const endTiming = this.startTiming(`function-${functionName}`)
      try {
        const result = fn(...args)

        // Handle promises
        if (result && typeof result.then === 'function') {
          return result.finally(() => endTiming())
        }

        endTiming()
        return result
      } catch (error) {
        endTiming()
        throw error
      }
    }) as T
  }

  public measureApiCall(url: string, method: string = 'GET'): () => void {
    const startTime = performance.now()

    return () => {
      const duration = performance.now() - startTime
      const key = `${method} ${url}`

      if (!this.customMetrics.apiResponseTime[key]) {
        this.customMetrics.apiResponseTime[key] = []
      }
      this.customMetrics.apiResponseTime[key].push(duration)

      this.addMetric({
        name: 'api-response-time',
        value: duration,
        timestamp: Date.now(),
        category: 'custom',
        tags: {
          url,
          method
        }
      })
    }
  }

  public measureComponentRender(componentName: string): () => void {
    const startTime = performance.now()

    return () => {
      const duration = performance.now() - startTime

      if (!this.customMetrics.componentRenderTime[componentName]) {
        this.customMetrics.componentRenderTime[componentName] = []
      }
      this.customMetrics.componentRenderTime[componentName].push(duration)

      this.addMetric({
        name: 'component-render-time',
        value: duration,
        timestamp: Date.now(),
        category: 'custom',
        tags: {
          component: componentName
        }
      })
    }
  }

  public measureRouteChange(routeName: string): () => void {
    const startTime = performance.now()

    return () => {
      const duration = performance.now() - startTime

      if (!this.customMetrics.routeChangeTime[routeName]) {
        this.customMetrics.routeChangeTime[routeName] = []
      }
      this.customMetrics.routeChangeTime[routeName].push(duration)

      this.addMetric({
        name: 'route-change-time',
        value: duration,
        timestamp: Date.now(),
        category: 'custom',
        tags: {
          route: routeName
        }
      })
    }
  }

  public recordUserInteraction() {
    this.customMetrics.userInteractions++

    this.addMetric({
      name: 'user-interaction',
      value: this.customMetrics.userInteractions,
      timestamp: Date.now(),
      category: 'custom'
    })
  }

  public recordError() {
    this.customMetrics.errorCount++

    this.addMetric({
      name: 'error-count',
      value: this.customMetrics.errorCount,
      timestamp: Date.now(),
      category: 'custom'
    })
  }

  private addMetric(metric: PerformanceMetric) {
    this.metrics.push(metric)

    // Keep only recent metrics in memory
    if (this.metrics.length > 1000) {
      this.metrics = this.metrics.slice(-500)
    }
  }

  public getMetrics(category?: string): PerformanceMetric[] {
    if (category) {
      return this.metrics.filter(m => m.category === category)
    }
    return [...this.metrics]
  }

  public getCustomMetrics(): CustomMetrics {
    return { ...this.customMetrics }
  }

  public getSummary() {
    const navigation = this.getMetrics('navigation')
    const resources = this.getMetrics('resource')
    const paint = this.getMetrics('paint')
    const custom = this.getMetrics('custom')

    const summary = {
      navigation: this.summarizeMetrics(navigation),
      resources: {
        count: resources.length,
        avgDuration: this.calculateAverage(resources.map(m => m.value))
      },
      paint: this.summarizeMetrics(paint),
      custom: this.summarizeMetrics(custom),
      webVitals: {
        lcp: this.getLatestMetric('lcp')?.value,
        fid: this.getLatestMetric('fid')?.value,
        cls: this.getLatestMetric('cls')?.value,
        tti: this.getLatestMetric('tti')?.value
      },
      apiPerformance: this.summarizeApiCalls(),
      memoryUsage: {
        current: this.customMetrics.memoryUsage.slice(-1)[0],
        average: this.calculateAverage(this.customMetrics.memoryUsage),
        peak: Math.max(...this.customMetrics.memoryUsage)
      }
    }

    return summary
  }

  private summarizeMetrics(metrics: PerformanceMetric[]) {
    if (metrics.length === 0) return null

    const values = metrics.map(m => m.value)
    return {
      count: metrics.length,
      min: Math.min(...values),
      max: Math.max(...values),
      avg: this.calculateAverage(values),
      p95: this.calculatePercentile(values, 95)
    }
  }

  private summarizeApiCalls() {
    const summary: Record<string, any> = {}

    Object.entries(this.customMetrics.apiResponseTime).forEach(([key, times]) => {
      summary[key] = {
        count: times.length,
        avg: this.calculateAverage(times),
        min: Math.min(...times),
        max: Math.max(...times),
        p95: this.calculatePercentile(times, 95)
      }
    })

    return summary
  }

  private getLatestMetric(name: string): PerformanceMetric | undefined {
    const metrics = this.metrics.filter(m => m.name === name)
    return metrics.length > 0 ? metrics[metrics.length - 1] : undefined
  }

  private calculateAverage(numbers: number[]): number {
    if (numbers.length === 0) return 0
    return numbers.reduce((sum, num) => sum + num, 0) / numbers.length
  }

  private calculatePercentile(numbers: number[], percentile: number): number {
    if (numbers.length === 0) return 0

    const sorted = [...numbers].sort((a, b) => a - b)
    const index = Math.ceil((percentile / 100) * sorted.length) - 1
    return sorted[Math.max(0, index)]
  }

  public exportData(): string {
    return JSON.stringify({
      metrics: this.metrics,
      customMetrics: this.customMetrics,
      summary: this.getSummary(),
      timestamp: Date.now()
    }, null, 2)
  }

  public clearMetrics() {
    this.metrics = []
    this.customMetrics = {
      apiResponseTime: {},
      componentRenderTime: {},
      routeChangeTime: {},
      memoryUsage: [],
      errorCount: 0,
      userInteractions: 0
    }
  }

  public destroy() {
    this.observers.forEach(observer => observer.disconnect())
    this.observers = []
    this.clearMetrics()
  }
}

// Create singleton instance
export const performanceMonitor = new PerformanceMonitor()

// Vue plugin
export default {
  install(app: any) {
    app.provide('$performance', performanceMonitor)
    app.config.globalProperties.$performance = performanceMonitor

    // Monitor route changes
    const router = app.config.globalProperties.$router
    if (router) {
      router.beforeEach((to: any) => {
        const endTiming = performanceMonitor.measureRouteChange(to.name || to.path)
        router.afterEach(() => {
          setTimeout(endTiming, 0) // Ensure DOM is updated
        })
      })
    }
  }
}