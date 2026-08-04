import { describe, expect, it } from 'vitest'
import {
  EMPTY_PACKAGE_ID,
  FAILING_PACKAGE_ID,
  InvestigationPackageLoadError,
  InvestigationPackageNotFoundError,
  fetchInvestigationScene,
  getDefaultInvestigationRoute,
  listInvestigationRoutes,
} from './investigationRepository'
import { InvestigationSceneNotFoundError } from '../model/normalizeInvestigation'

describe('investigation package repository', () => {
  it('loads and normalizes a scene from the validated golden package', async () => {
    const result = await fetchInvestigationScene(
      'blank-cheque-golden',
      'scene-2-blank-cheque',
    )

    expect(result.investigation.packageId).toBe('blank-cheque-golden')
    expect(result.scene.id).toBe('scene-2-blank-cheque')
    expect(result.scene.claims.length).toBeGreaterThan(0)
  })

  it('loads an honest partial package for the empty-content state', async () => {
    const route = listInvestigationRoutes().find(
      (candidate) => candidate.packageId === EMPTY_PACKAGE_ID,
    )
    expect(route).toBeDefined()

    const result = await fetchInvestigationScene(
      route!.packageId,
      route!.sceneId,
    )

    expect(result.investigation.status).toBe('partial')
    expect(result.investigation.generationReport.outcome).toBe('partial')
    expect(result.scene.claims).toHaveLength(0)
    expect(result.scene.relationships).toHaveLength(0)
    expect(result.scene.narrativeBlocks[0].isMaterialAssertion).toBe(false)
  })

  it('rejects with a load error for the reserved failure-state package id', async () => {
    await expect(
      fetchInvestigationScene(FAILING_PACKAGE_ID, 'scene-any'),
    ).rejects.toBeInstanceOf(InvestigationPackageLoadError)
  })

  it('rejects with a package error for an unknown package id', async () => {
    await expect(
      fetchInvestigationScene('package-does-not-exist', 'scene-any'),
    ).rejects.toBeInstanceOf(InvestigationPackageNotFoundError)
  })

  it('rejects with a scene error for an unknown scene in a real package', async () => {
    await expect(
      fetchInvestigationScene('blank-cheque-golden', 'scene-does-not-exist'),
    ).rejects.toBeInstanceOf(InvestigationSceneNotFoundError)
  })

  it('derives the default route from registered package metadata', () => {
    const route = getDefaultInvestigationRoute()

    expect(listInvestigationRoutes()).toContainEqual(route)
    expect(route.packageId).toBe('blank-cheque-golden')
    expect(route.sceneId).toBe('scene-2-blank-cheque')
  })
})
