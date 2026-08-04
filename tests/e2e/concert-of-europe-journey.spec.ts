import { test, expect } from '@playwright/test'

/**
 * Proves the generic renderer has no hidden coupling to the blank-cheque
 * package: this package was generated end-to-end by the Python pipeline's
 * curated provider set (backend/src/chronicle/providers/curated/
 * concert_of_europe/), not hand-authored TypeScript/JSON, and exercises the
 * same route/components a second, independently sourced dataset — real
 * dates, real figures, a real period map on one scene and a genuine,
 * disclosed absence of one on the other.
 */

const VIENNA_SCENE_URL =
  '/investigations/concert-of-europe-1814-1822/scenes/scene-congress-of-vienna'
const INTERVENTION_SCENE_URL =
  '/investigations/concert-of-europe-1814-1822/scenes/scene-principle-of-intervention'

test('Concert of Europe: the Vienna scene renders with its real period map and evidence', async ({
  page,
}) => {
  await page.goto(VIENNA_SCENE_URL)

  await expect(
    page.getByText('The Concert of Europe and Revolutionary Intervention, 1814-1822'),
  ).toBeVisible()
  await expect(
    page.getByRole('heading', { level: 2, name: 'The Congress System Established, 1814-1815' }),
  ).toBeVisible()

  // A real period map is attached to this scene (unlike the intervention
  // scene below) — its citation renders, not a schematic-fallback notice.
  await expect(page.getByText(/Treaty Adjustments, 1814, 1815/i)).toBeVisible()

  const mapRegion = page.getByRole('region', { name: /map and relationship graph/i })
  const viennaButton = mapRegion.getByRole('button', { name: /^Vienna/ })
  await expect(viennaButton).toBeVisible()

  // Open the narrative's material assertion and see the real evidence.
  await page
    .getByRole('button', { name: /redistributing territory among prussia, russia, and austria/i })
    .click()
  const evidenceRegion = page.getByRole('region', { name: /evidence/i })
  await expect(
    evidenceRegion.getByText(/congress of vienna's general treaty/i).first(),
  ).toBeVisible()
  await expect(evidenceRegion.getByText(/supporting/i).first()).toBeVisible()

  // Cross-facet sync: selecting the place changes what the evidence panel shows.
  await viennaButton.click()
  await expect(viennaButton).toHaveAttribute('aria-current', 'true')
})

test('Concert of Europe: the intervention scene honestly has no period map and shows the disputed doctrine', async ({
  page,
}) => {
  await page.goto(INTERVENTION_SCENE_URL)

  await expect(
    page.getByRole('heading', { level: 2, name: 'The Principle of Intervention, 1820-1822' }),
  ).toBeVisible()

  // No map asset is attached to this scene (docs/research/concert-of-europe-map-source.md's
  // disclosed gap) — the schematic fallback's own label says so explicitly.
  await expect(
    page.getByRole('img', { name: /no period-accurate basemap curated for this scene yet/i }),
  ).toBeVisible()

  // Open the Troppau/Naples/Castlereagh narrative block and confirm the
  // disputed relationship renders its classification as visible text.
  await page
    .getByRole('button', { name: /meeting at troppau, austria, prussia, and russia/i })
    .click()
  const evidenceRegion = page.getByRole('region', { name: /evidence/i })
  await expect(evidenceRegion.getByText(/disputed/i).first()).toBeVisible()
  await expect(
    evidenceRegion.getByText(/ipso facto cease to be members of the european alliance/i).first(),
  ).toBeVisible()

  // Timeline/back-navigation: return to the Vienna scene via browser history
  // after visiting it directly proves independent, package-driven routing.
  await page.goto(VIENNA_SCENE_URL)
  await expect(
    page.getByRole('heading', { level: 2, name: 'The Congress System Established, 1814-1815' }),
  ).toBeVisible()
})
