import { test, expect } from '@playwright/test'

/**
 * Plan 5 requirement: keyboard-accessible timeline, location list,
 * relationship list, evidence controls, and visible focus states
 * (docs/design/accessibility.md). This is not a substitute for the manual
 * keyboard/screen-reader pass Plan 5 also calls for — see
 * docs/delivery/validation/phase-1-gate-1-template.md for what remains
 * manual — but it does guard against the most common regression: an
 * interactive element that's mouse-only.
 */

test('a timeline event is reachable and activatable by keyboard alone', async ({ page }) => {
  await page.goto('/')
  const eventButton = page.getByRole('button', {
    name: /vienna's ultimatum deliberations/i,
  })
  await eventButton.waitFor()

  await eventButton.focus()
  await expect(eventButton).toBeFocused()

  await page.keyboard.press('Enter')
  await expect(eventButton).toHaveAttribute('aria-current', 'true')
})

test('the map/graph toggle supports arrow-key navigation per the ARIA tabs pattern', async ({
  page,
}) => {
  await page.goto('/')
  const mapTab = page.getByRole('tab', { name: 'Map' })
  const graphTab = page.getByRole('tab', { name: 'Relationships' })
  await mapTab.waitFor()

  await mapTab.focus()
  await expect(mapTab).toHaveAttribute('tabindex', '0')
  await expect(graphTab).toHaveAttribute('tabindex', '-1')

  await page.keyboard.press('ArrowRight')
  await expect(graphTab).toBeFocused()
  await expect(graphTab).toHaveAttribute('aria-selected', 'true')

  await page.keyboard.press('ArrowLeft')
  await expect(mapTab).toBeFocused()
  await expect(mapTab).toHaveAttribute('aria-selected', 'true')
})

test('keyboard focus is visibly indicated', async ({ page }) => {
  await page.goto('/')
  const firstNarrativeButton = page.getByRole('button', {
    name: /szögyény met with wilhelm/i,
  })
  await firstNarrativeButton.waitFor()
  await firstNarrativeButton.focus()

  const outlineWidth = await firstNarrativeButton.evaluate(
    (el) => getComputedStyle(el).outlineWidth,
  )
  expect(outlineWidth).not.toBe('0px')
})
