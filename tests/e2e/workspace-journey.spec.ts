import { test, expect } from '@playwright/test'
import AxeBuilder from '@axe-core/playwright'

/**
 * Phase D0.3 coverage for the map-first workspace shell itself
 * (docs/decisions/ADR-002-map-first-workspace.md): panel keyboard resize/
 * collapse/reopen, the mobile bottom sheet, and accessibility — the
 * mechanics gate1-journey.spec.ts/keyboard-navigation.spec.ts cover for
 * Inspector instead (that UI didn't change).
 */

const VIENNA_SCENE_URL =
  '/investigations/blank-cheque-golden/scenes/scene-2-blank-cheque'

test('the panel divider resizes via keyboard and collapse/reopen preserves focus management', async ({
  page,
}) => {
  await page.goto(VIENNA_SCENE_URL)

  const separator = page.getByRole('separator', { name: /resize investigation panel/i })
  await separator.waitFor()
  const initialWidth = Number(await separator.getAttribute('aria-valuenow'))

  await separator.focus()
  await page.keyboard.press('ArrowLeft')
  await expect(separator).not.toHaveAttribute('aria-valuenow', String(initialWidth))

  const widerWidth = Number(await separator.getAttribute('aria-valuenow'))
  expect(widerWidth).toBeGreaterThan(initialWidth)

  // Enter collapses the panel and moves focus to the reopen button — not
  // stranding focus inside a now-hidden region.
  await page.keyboard.press('Enter')
  const reopenButton = page.getByRole('button', { name: /reopen investigation panel/i })
  await expect(reopenButton).toBeFocused()

  await reopenButton.click()
  await expect(page.getByRole('separator', { name: /resize investigation panel/i })).toBeVisible()
})

test('the lens selector switches the canvas and the choice persists across reload', async ({
  page,
}) => {
  await page.goto(VIENNA_SCENE_URL)

  const lensSelect = page.getByLabel('Lens')
  await lensSelect.selectOption('lens-uncertainty')
  await expect(page).toHaveURL(/lens=lens-uncertainty/)

  await page.reload()
  await expect(page.getByLabel('Lens')).toHaveValue('lens-uncertainty')
})

test('mobile viewport: the bottom sheet cycles collapsed/half/expanded and stays keyboard-operable', async ({
  page,
}) => {
  await page.setViewportSize({ width: 390, height: 844 })
  await page.goto(VIENNA_SCENE_URL)

  const handle = page.getByRole('button', { name: /investigation panel is/i })
  await handle.waitFor()
  await expect(handle).toHaveAccessibleName(/is half/i)

  await handle.click()
  await expect(handle).toHaveAccessibleName(/is expanded/i)
  await expect(page.getByRole('tab', { name: 'Explore' })).toBeVisible()

  await handle.click()
  await expect(handle).toHaveAccessibleName(/is collapsed/i)
})

test('the workspace has no detectable accessibility violations', async ({ page }) => {
  await page.goto(VIENNA_SCENE_URL)
  await page.getByLabel('Lens').waitFor()

  const results = await new AxeBuilder({ page }).analyze()
  expect(results.violations).toEqual([])
})
