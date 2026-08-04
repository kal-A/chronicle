import {
  EMPTY_INVESTIGATION_PACKAGE_ID,
  investigationFixtures,
} from '../../../content/investigationFixtures'
import {
  normalizeInvestigationScene,
  type InvestigationSceneNotFoundError,
} from '../model/normalizeInvestigation'
import type { GeneratedInvestigation } from '../model/generatedInvestigation'
import type { Scene } from '../model/schema'

export const EMPTY_PACKAGE_ID = EMPTY_INVESTIGATION_PACKAGE_ID
export const FAILING_PACKAGE_ID = 'fixture-simulated-package-failure'

export class InvestigationPackageNotFoundError extends Error {
  constructor(packageId: string) {
    super(`No investigation package found for id "${packageId}"`)
    this.name = 'InvestigationPackageNotFoundError'
  }
}

export class InvestigationPackageLoadError extends Error {
  constructor(packageId: string) {
    super(`Simulated failure loading investigation package "${packageId}"`)
    this.name = 'InvestigationPackageLoadError'
  }
}

export interface InvestigationRoute {
  packageId: string
  sceneId: string
}

export interface LoadedInvestigationScene {
  investigation: GeneratedInvestigation
  scene: Scene
}

export interface InvestigationRepositoryOptions {
  /** Artificial latency in ms, used to exercise a real loading state. */
  delayMs?: number
}

function delay(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

export async function fetchInvestigationScene(
  packageId: string,
  sceneId: string,
  options: InvestigationRepositoryOptions = {},
): Promise<LoadedInvestigationScene> {
  await delay(options.delayMs ?? 0)

  if (packageId === FAILING_PACKAGE_ID) {
    throw new InvestigationPackageLoadError(packageId)
  }

  const registration = investigationFixtures.find(
    (candidate) => candidate.investigation.packageId === packageId,
  )
  if (!registration) throw new InvestigationPackageNotFoundError(packageId)

  return {
    investigation: registration.investigation,
    scene: normalizeInvestigationScene(registration.investigation, sceneId),
  }
}

export function listInvestigationRoutes(): InvestigationRoute[] {
  return investigationFixtures.flatMap(({ investigation }) =>
    investigation.scenes.map((scene) => ({
      packageId: investigation.packageId,
      sceneId: scene.id,
    })),
  )
}

export function getDefaultInvestigationRoute(): InvestigationRoute {
  const registration =
    investigationFixtures.find((candidate) => candidate.isDefault) ??
    investigationFixtures[0]
  return {
    packageId: registration.investigation.packageId,
    sceneId: registration.investigation.interactionSpec.defaultSceneId,
  }
}

export type { InvestigationSceneNotFoundError }
