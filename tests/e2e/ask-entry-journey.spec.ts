import { test, expect } from '@playwright/test'
import AxeBuilder from '@axe-core/playwright'

/**
 * Phase D0.5 coverage for the Ask entry surface
 * (docs/product/map-first-workspace-instructions.md §4-6,
 * docs/decisions/ADR-002-map-first-workspace.md): asking a matched question
 * walks through scope review and the mock generation-progress checklist into
 * the real matched workspace; an unmatched question gets an honest "not
 * available" message rather than a silent wrong guess (there is no live
 * generation pipeline behind this prototype — see
 * src/features/investigation/ask/topicMatch.ts).
 */

test('asking a matched question walks through scope review and generation into the real workspace', async ({
  page,
}) => {
  await page.goto('/')

  await expect(page.getByRole('heading', { level: 1, name: 'Chronicle' })).toBeVisible()

  await page.getByLabel(/ask a historical question/i).fill(
    'How did the Concert of Europe respond to revolutionary intervention at Troppau and Naples?',
  )
  await page.getByRole('button', { name: 'Ask' }).click()

  await expect(page.getByText(/proposed scope/i)).toBeVisible()
  await expect(page.getByText(/Vienna, Troppau, Laibach, Naples, and Verona/i)).toBeVisible()

  await page.getByRole('button', { name: /generate this investigation/i }).click()
  await expect(page.getByRole('status', { name: /generation progress/i })).toBeVisible()
  await expect(page.getByText('Scope defined')).toBeVisible()

  // Lands on the real Concert of Europe workspace once the checklist completes.
  await expect(page).toHaveURL(/\/investigations\/concert-of-europe-1814-1822\/scenes\//)
  await expect(page.getByLabel('Lens')).toBeVisible()
})

test('asking an unrelated question gives an honest no-match message, not a silent wrong guess', async ({
  page,
}) => {
  await page.goto('/')

  await page.getByLabel(/ask a historical question/i).fill(
    'What was the economic impact of the Meiji Restoration on Japanese silk exports?',
  )
  await page.getByRole('button', { name: 'Ask' }).click()

  await expect(page.getByRole('alert')).toContainText(/nothing curated matches/i)
  await expect(page).toHaveURL('/')

  // A suggested starting point still works from the no-match state.
  await page.getByRole('button', { name: /german assurance/i }).click()
  await expect(page.getByText(/proposed scope/i)).toBeVisible()
})

test('the ask entry surface has no detectable accessibility violations', async ({ page }) => {
  await page.goto('/')
  await page.getByLabel(/ask a historical question/i).waitFor()

  const results = await new AxeBuilder({ page }).analyze()
  expect(results.violations).toEqual([])
})
