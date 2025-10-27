# Frontend Testing Configuration

## Test Scripts
test = "vitest"
test:ui = "vitest --ui"
test:coverage = "vitest run --coverage"
test:e2e = "playwright test"
test:e2e:ui = "playwright test --ui"

# Dependencies for testing
@testing-library/vue = "^7.0.0"
@testing-library/jest-dom = "^6.1.4"
@vitejs/plugin-vue = "^4.4.0"
vitest = "^0.34.6"
jsdom = "^22.1.0"
@vue/test-utils = "^2.4.1"
happy-dom = "^12.10.3"
playwright = "^1.40.0"
@playwright/test = "^1.40.0"