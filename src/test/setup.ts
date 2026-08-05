import '@testing-library/jest-dom/vitest'

// jsdom does not implement matchMedia. Several components check
// prefers-reduced-motion (src/features/investigation/ask/useReducedMotion.ts)
// — stub it to "no preference" so those checks don't throw in tests.
if (!window.matchMedia) {
  window.matchMedia = (query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: () => {},
    removeListener: () => {},
    addEventListener: () => {},
    removeEventListener: () => {},
    dispatchEvent: () => false,
  })
}
