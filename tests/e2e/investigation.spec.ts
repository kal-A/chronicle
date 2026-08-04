import { test, expect } from '@playwright/test'
import AxeBuilder from '@axe-core/playwright'

test('investigation shell loads and has no detectable accessibility violations', async ({
  page,
}) => {
  await page.goto('/')
  await expect(
    page.getByRole('heading', { level: 1, name: 'Chronicle' }),
  ).toBeVisible()

  const results = await new AxeBuilder({ page }).analyze()
  expect(results.violations).toEqual([])
})
