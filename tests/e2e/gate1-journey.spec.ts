import { test, expect } from '@playwright/test'

/**
 * Automates the *mechanics* of the Gate 1 task list in
 * docs/delivery/phase-1-validation-plan.md — it proves the interface lets
 * someone complete each task, not that a real reader actually comprehends
 * the content correctly. Comprehension can only be established by the
 * actual 5-participant human test; see
 * docs/delivery/validation/phase-1-gate-1-template.md for that gap.
 */

test('Gate 1 happy path: explain, locate, open evidence, distinguish fact from dispute, cross-facet select, navigate back, find a limitation', async ({
  page,
}) => {
  await page.goto('/')

  // Task 1 — explain what decision/exchange the scene centers on.
  await expect(
    page.getByRole('heading', { level: 2, name: /blank cheque/i }),
  ).toBeVisible()

  // Task 2 — identify where and when the key communication occurred.
  const mapRegionLocator = page.getByRole('region', {
    name: /map and relationship graph/i,
  })
  await expect(mapRegionLocator.getByRole('button', { name: /^Berlin/ })).toBeVisible()
  await expect(mapRegionLocator.getByRole('button', { name: /^Vienna/ })).toBeVisible()
  await expect(page.getByText('1914-07-05')).toBeVisible()

  // Task 3 — open the evidence behind the reported German assurance.
  const assuranceBlock = page.getByRole('button', {
    name: /szögyény met with wilhelm/i,
  })
  await assuranceBlock.click()
  const evidenceRegion = page.getByRole('region', { name: /evidence/i })
  await expect(
    evidenceRegion.getByText(/could count on germany.?s full support/i).first(),
  ).toBeVisible()
  await expect(evidenceRegion.getByText(/supporting/i).first()).toBeVisible()

  // Task 4 — distinguish documentary fact from disputed interpretation.
  // The disputed relationship must render its classification as visible
  // text, not color alone (AGENTS.md §12).
  const eventAboutReaction = page.getByRole('button', {
    name: /wilhelm ii annotates the report/i,
  })
  await eventAboutReaction.click()
  await expect(evidenceRegion.getByText(/disputed/i).first()).toBeVisible()

  // Task 5 — select in a non-narrative facet and see something else change.
  const viennaButton = mapRegionLocator.getByRole('button', { name: /^Vienna/ })
  await viennaButton.click()
  await expect(viennaButton).toHaveAttribute('aria-current', 'true')
  await expect(
    evidenceRegion.getByText(/vienna.?s diplomatic posture/i),
  ).toBeVisible()

  // Task 6 — return to a previous focus via browser history.
  await page.goBack()
  await expect(eventAboutReaction).toHaveAttribute('aria-current', 'true')

  // Task 7 — find an uncertainty/evidence limitation without being told
  // where it is. The narrative's prototype-content notice is visible
  // up front, unprompted.
  await expect(page.getByText(/prototype content/i)).toBeVisible()
})
