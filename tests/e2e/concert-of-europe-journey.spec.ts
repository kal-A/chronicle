import { test, expect } from '@playwright/test'

/**
 * Proves the generic renderer — now the map-first workspace
 * (docs/decisions/ADR-002-map-first-workspace.md) — has no hidden coupling
 * to the blank-cheque package: this Concert of Europe package was generated
 * end-to-end by the Python pipeline's curated provider set
 * (backend/src/chronicle/providers/curated/concert_of_europe/), its
 * InvestigationExperiencePlan is hand-authored fixture content for D0.3
 * (src/content/investigationFixtures.ts — D0.4 replaces it with pipeline
 * output), and it exercises the same workspace route/components a second,
 * independently sourced dataset: real dates, real figures, a real period
 * map on one scene, and a genuine, disclosed absence of a map — and of a
 * dedicated primary source for the Verona claim — on the other.
 */

const VIENNA_SCENE_URL =
  '/investigations/concert-of-europe-1814-1822/scenes/scene-congress-of-vienna'
const INTERVENTION_SCENE_URL =
  '/investigations/concert-of-europe-1814-1822/scenes/scene-principle-of-intervention'

test('Concert of Europe workspace: the Vienna scene renders its Sequence lens with the real period map', async ({
  page,
}) => {
  await page.goto(VIENNA_SCENE_URL)

  await expect(page.getByRole('heading', { level: 1, name: 'Chronicle' })).toBeVisible()
  await expect(
    page.getByText('The Concert of Europe and Revolutionary Intervention'),
  ).toBeVisible()

  // The default lens (Sequence, map-type) shows a real period map — not the
  // schematic fallback — for this scene specifically.
  await expect(page.getByText(/Treaty Adjustments, 1814, 1815/i)).toBeVisible()

  const lensSelect = page.getByLabel('Lens')
  await expect(lensSelect).toHaveValue('lens-sequence')

  // Switching to the Systems lens swaps the canvas to the labelled graph —
  // no map/graph "tab," per map-first-workspace-instructions.md §7.
  await lensSelect.selectOption('lens-systems')
  await expect(page.getByText('The intervention doctrine')).toBeVisible()
})

test('Concert of Europe workspace: the intervention scene has no map, and Systems shows the disputed doctrine', async ({
  page,
}) => {
  await page.goto(INTERVENTION_SCENE_URL)

  await expect(
    page.getByText('The Principle of Intervention, 1820-1822', { exact: false }),
  ).toBeVisible()

  const lensSelect = page.getByLabel('Lens')
  await lensSelect.selectOption('lens-systems')

  // The labelled systems graph's accessible node/edge list renders the real
  // relationship verbs, not numbered claim IDs.
  await expect(page.getByText(/establishes the doctrine invoked by/i).first()).toBeVisible()
  await expect(page.getByText('disputed', { exact: false }).first()).toBeVisible()

  // Uncertainty lens surfaces the disclosed gaps as first-class content.
  await lensSelect.selectOption('lens-uncertainty')
  // The docked panel and bottom sheet both mount their tab content (CSS
  // toggles which is visible per breakpoint) — same "always mounted" pattern
  // as the existing Map/Graph facets, so duplicate matches are expected.
  await expect(
    page.getByText(/no dedicated congress of verona primary document/i).first(),
  ).toBeVisible()

  // Evidence tab, scoped to the whole-scene focus, hands off to Inspector
  // for the deep view — proving the shallow/deep split actually connects.
  await page.getByRole('tab', { name: 'Evidence' }).click()
  await page.getByRole('link', { name: /inspector/i }).click()
  await expect(
    page.getByRole('heading', { level: 2, name: 'The Principle of Intervention, 1820-1822' }),
  ).toBeVisible()
  await expect(
    page.getByRole('img', { name: /no period-accurate basemap curated for this scene yet/i }),
  ).toBeVisible()
})
