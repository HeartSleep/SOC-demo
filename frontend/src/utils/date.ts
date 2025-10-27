/**
 * Format date to readable string
 */
export const formatDate = (date: string | Date, format: string = 'datetime'): string => {
  if (!date) return '-'

  const d = new Date(date)
  if (isNaN(d.getTime())) return '-'

  const now = new Date()
  const diff = now.getTime() - d.getTime()

  if (format === 'relative') {
    const seconds = Math.floor(diff / 1000)
    const minutes = Math.floor(seconds / 60)
    const hours = Math.floor(minutes / 60)
    const days = Math.floor(hours / 24)

    if (seconds < 60) return '刚刚'
    if (minutes < 60) return `${minutes}分钟前`
    if (hours < 24) return `${hours}小时前`
    if (days < 7) return `${days}天前`
  }

  const year = d.getFullYear()
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  const hour = String(d.getHours()).padStart(2, '0')
  const minute = String(d.getMinutes()).padStart(2, '0')
  const second = String(d.getSeconds()).padStart(2, '0')

  if (format === 'date') {
    return `${year}-${month}-${day}`
  }

  if (format === 'time') {
    return `${hour}:${minute}:${second}`
  }

  return `${year}-${month}-${day} ${hour}:${minute}:${second}`
}

/**
 * Format duration in milliseconds to readable string
 */
export const formatDuration = (duration: number): string => {
  if (!duration || duration < 0) return '-'

  const seconds = Math.floor(duration / 1000)
  const minutes = Math.floor(seconds / 60)
  const hours = Math.floor(minutes / 60)
  const days = Math.floor(hours / 24)

  if (days > 0) {
    return `${days}天${hours % 24}小时`
  }

  if (hours > 0) {
    return `${hours}小时${minutes % 60}分钟`
  }

  if (minutes > 0) {
    return `${minutes}分钟${seconds % 60}秒`
  }

  return `${seconds}秒`
}

/**
 * Get time ago string
 */
export const timeAgo = (date: string | Date): string => {
  return formatDate(date, 'relative')
}

/**
 * Check if date is today
 */
export const isToday = (date: string | Date): boolean => {
  const d = new Date(date)
  const today = new Date()
  return d.toDateString() === today.toDateString()
}

/**
 * Check if date is within last N days
 */
export const isWithinDays = (date: string | Date, days: number): boolean => {
  const d = new Date(date)
  const now = new Date()
  const diff = now.getTime() - d.getTime()
  const daysDiff = Math.floor(diff / (1000 * 60 * 60 * 24))
  return daysDiff <= days
}