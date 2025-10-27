import { ref, computed } from 'vue'

// Theme state
const isDark = ref(false)

export function useTheme() {
  // Toggle theme
  const toggleTheme = () => {
    isDark.value = !isDark.value
    updateBodyClass()
  }

  // Set theme
  const setTheme = (dark: boolean) => {
    isDark.value = dark
    updateBodyClass()
  }

  // Update body class
  const updateBodyClass = () => {
    if (isDark.value) {
      document.body.classList.add('dark')
    } else {
      document.body.classList.remove('dark')
    }
  }

  // Theme class
  const themeClass = computed(() => isDark.value ? 'dark' : 'light')

  // Initialize theme from localStorage
  const initTheme = () => {
    const savedTheme = localStorage.getItem('theme')
    if (savedTheme === 'dark') {
      setTheme(true)
    } else {
      setTheme(false)
    }
  }

  // Save theme to localStorage
  const saveTheme = () => {
    localStorage.setItem('theme', isDark.value ? 'dark' : 'light')
  }

  return {
    isDark: computed(() => isDark.value),
    themeClass,
    toggleTheme,
    setTheme,
    initTheme,
    saveTheme
  }
}