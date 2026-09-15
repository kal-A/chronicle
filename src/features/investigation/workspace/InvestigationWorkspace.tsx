import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useFocus } from '../focus/useFocus'
import { MapView } from '../map/MapView'
import { historicalYear } from '../map/territory'
import { formatHistoricalDate } from '../model/formatHistoricalDate'
import { describeFocus } from '../model/describeFocus'
import { compareHistoricalDates } from '../model/schema'
import type { Scene } from '../model/schema'
import type { GeneratedInvestigation } from '../model/generatedInvestigation'
import { WorkspaceHeader } from './WorkspaceHeader'
import { DockedPanel } from './dock/DockedPanel'
import { BottomSheet } from './dock/BottomSheet'
import { AskTab } from './panel/AskTab'
import { ExploreTab } from './panel/ExploreTab'
import { EvidenceTab } from './panel/EvidenceTab'
import { SourcesTab } from './panel/SourcesTab'
import { SystemsLensView } from './canvas/SystemsLensView'
import { resolveLenses, sceneScopeLens } from './lenses/lensResolution'
import { useActiveLensId } from './lenses/useActiveLensId'
import { TemporalMapRail } from './TemporalMapRail'
import { useInvestigationAssistant } from '../assistant/useInvestigationAssistant'
import type {
  AssistantAction,
  SelectedRecordInput,
  WorkspaceContextInput,
} from '../assistant/agentApi'
import type { FocusValue } from '../model/focus'

/** A reasonable default for the panel's max-width clamp — this workspace
 * doesn't track live viewport width via ResizeObserver (kept simple for
 * D0.3); the panel's own min/max/keyboard-resize behavior is what matters
 * for the completion criteria, not pixel-perfect clamping against the
 * actual rendered width. */
const ASSUMED_WORKSPACE_WIDTH_PX = 1024

export function InvestigationWorkspace({
  investigation,
  scene,
  enteredFromAsk = false,
  submittedQuestion,
}: {
  investigation: GeneratedInvestigation
  scene: Scene
  enteredFromAsk?: boolean
  submittedQuestion?: string
}) {
  const { focus, setFocus } = useFocus()
  const navigate = useNavigate()
  const isWholeScene = focus.kind === 'scene'

  useEffect(() => {
    document.title = `${investigation.presentation.title} · Chronicle`
    return () => {
      document.title = 'Chronicle'
    }
  }, [investigation.presentation.title])

  const lenses = useMemo(() => resolveLenses(investigation, scene), [investigation, scene])
  const defaultLensId = investigation.experiencePlan?.workspace.initialLensId ?? lenses[0].id
  const [activeLensId, setActiveLensId] = useActiveLensId(defaultLensId)
  const activeLens = lenses.find((lens) => lens.id === activeLensId) ?? lenses[0]
  const scoped = useMemo(() => sceneScopeLens(activeLens, scene), [activeLens, scene])
  const temporalEvents = useMemo(
    () =>
      [...scene.events]
        .filter((event) => scoped.eventIds.has(event.id))
        .sort((a, b) => compareHistoricalDates(a.eventTime, b.eventTime)),
    [scene.events, scoped.eventIds],
  )
  const [selectedEventIndex, setSelectedEventIndex] = useState(() =>
    Math.max(0, temporalEvents.length - 1),
  )

  useEffect(() => {
    setSelectedEventIndex((current) => Math.min(current, Math.max(0, temporalEvents.length - 1)))
  }, [temporalEvents.length])

  useEffect(() => {
    if (focus.kind !== 'event') return
    const eventIndex = temporalEvents.findIndex((event) => event.id === focus.eventId)
    if (eventIndex >= 0) setSelectedEventIndex(eventIndex)
  }, [focus, temporalEvents])

  const timeVisibleEventIds = useMemo(
    () => new Set(temporalEvents.slice(0, selectedEventIndex + 1).map((event) => event.id)),
    [selectedEventIndex, temporalEvents],
  )
  const activeEvent = temporalEvents[selectedEventIndex]
  const activePlace = activeEvent
    ? scene.entities.find(
        (entity) => entity.entityType === 'place' && entity.id === activeEvent.placeId,
      )
    : undefined
  const investigationQuestion =
    submittedQuestion ?? investigation.experiencePlan?.opening.question ?? scene.title

  const workspaceContext = useMemo<WorkspaceContextInput>(() => {
    const selectedDate = focus.kind === 'timeRange' ? focus.range : activeEvent?.eventTime
    const selectedDateRange = selectedDate
      ? {
          ...(selectedDate.earliest ? { earliest: selectedDate.earliest } : {}),
          ...(selectedDate.latest ? { latest: selectedDate.latest } : {}),
        }
      : undefined
    return {
      sceneId: scene.id,
      selectedLensId: activeLens.id,
      ...(selectedDateRange && Object.keys(selectedDateRange).length ? { selectedDateRange } : {}),
      selectedRecords: selectedRecordsFromFocus(focus),
    }
  }, [activeEvent?.eventTime, activeLens.id, focus, scene.id])

  const assistant = useInvestigationAssistant({
    corpusId: investigation.packageId,
    workspaceContext,
    initialQuestion: enteredFromAsk ? submittedQuestion : undefined,
  })

  const systemPath = investigation.experiencePlan?.systemPaths.find(
    (path) => path.lensId === activeLens.id,
  )

  const inspectorHref = `/investigations/${encodeURIComponent(investigation.packageId)}/scenes/${encodeURIComponent(scene.id)}/inspector`

  function handleAssistantAction(action: AssistantAction) {
    const stringValue = (name: string) =>
      typeof action[name] === 'string' ? action[name] as string : undefined
    if (action.type === 'FOCUS_EVENT') {
      const eventId = stringValue('eventId')
      if (eventId && scene.events.some((event) => event.id === eventId)) {
        setFocus({ kind: 'event', eventId }, 'narrative')
      }
    } else if (action.type === 'FOCUS_LOCATION') {
      const entityId = stringValue('locationId')
      if (entityId && scene.entities.some((entity) => entity.id === entityId)) {
        setFocus({ kind: 'entity', entityId, entityType: 'place' }, 'narrative')
      }
    } else if (action.type === 'ACTIVATE_LENS') {
      const lensId = stringValue('lensId')
      if (lensId && lenses.some((lens) => lens.id === lensId)) setActiveLensId(lensId)
    } else if (action.type === 'OPEN_SOURCE') {
      const sourceId = stringValue('sourceId')
      if (sourceId && scene.sources.some((source) => source.id === sourceId)) {
        setFocus({ kind: 'source', sourceId }, 'evidence')
      }
    } else if (action.type === 'OPEN_EVIDENCE') {
      const recordId = stringValue('recordId')
      if (recordId && scene.claims.some((claim) => claim.id === recordId)) {
        setFocus({ kind: 'claim', claimId: recordId }, 'evidence')
      } else if (recordId && scene.relationships.some((item) => item.id === recordId)) {
        setFocus({ kind: 'relationship', relationshipId: recordId }, 'evidence')
      }
    } else if (action.type === 'RESET_VIEW') {
      setFocus({ kind: 'scene', sceneId: scene.id }, 'narrative')
    }
  }

  const initialPanelTab = enteredFromAsk
    ? 'ask'
    : investigation.experiencePlan?.workspace.initialPanelTab ?? 'explore'

  return (
    <main
      className={`chronicle-investigation ${enteredFromAsk ? 'chronicle-investigation--arriving' : ''}`}
    >
      <header className="chronicle-investigation__header">
        <WorkspaceHeader
          investigationTitle={investigation.presentation.title}
          lenses={lenses}
          activeLensId={activeLens.id}
          onSelectLens={setActiveLensId}
          inspectorHref={inspectorHref}
          focusDescription={describeFocus(focus, scene)}
          canClearFocus={!isWholeScene}
          onClearFocus={() => setFocus({ kind: 'scene', sceneId: scene.id }, 'url')}
        />
      </header>

      <div className="chronicle-investigation__body">
        <section className="chronicle-investigation__canvas" aria-label="Investigation map">
          <div className="chronicle-scene-heading">
            <div>
              <h2>{scene.title}</h2>
              <p>{formatHistoricalDate(scene.dateRange)}</p>
            </div>
            <div className="chronicle-scene-heading__context" aria-live="polite">
              <span>{activePlace?.canonicalName ?? 'Investigation theatre'}</span>
              <strong>{activeEvent?.title ?? 'No dated event selected'}</strong>
            </div>
          </div>
          {activeLens.visualizationType === 'graph' && systemPath ? (
            <SystemsLensView
              scene={scene}
              systemPath={systemPath}
              focus={focus}
              onSelectFocus={(f) => setFocus(f, 'graph')}
            />
          ) : (
            <MapView
              scene={scene}
              focus={focus}
              onSelectFocus={(f) => setFocus(f, 'map')}
              placeIds={scoped.placeIds}
              eventIds={timeVisibleEventIds}
              controlStates={investigation.controlStates}
              territoryGeometries={investigation.territoryGeometries}
              currentYear={activeEvent ? historicalYear(activeEvent.eventTime, 'end') : null}
            />
          )}
          {activeLens.visualizationType === 'map' ? (
            <TemporalMapRail
              events={temporalEvents}
              selectedIndex={selectedEventIndex}
              onSelectIndex={(index) => {
                setSelectedEventIndex(index)
                const event = temporalEvents[index]
                if (event) setFocus({ kind: 'event', eventId: event.id }, 'timeline')
              }}
            />
          ) : null}
        </section>

        <DockedPanel
          question={investigationQuestion}
          scopeSummary={investigation.experiencePlan?.opening.scopeSummary}
          ask={<AskTab assistant={assistant} onAction={handleAssistantAction} />}
          explore={<ExploreTab investigation={investigation} lens={activeLens} />}
          evidence={
            <EvidenceTab
              scene={scene}
              focus={focus}
              onOpenInspector={() => navigate(inspectorHref)}
            />
          }
          sources={<SourcesTab scene={scene} />}
          initialTab={initialPanelTab}
          defaultWidth={investigation.experiencePlan?.workspace.defaultPanelWidth ?? 380}
          workspaceWidthPx={ASSUMED_WORKSPACE_WIDTH_PX}
        />
      </div>

      <BottomSheet
        question={investigationQuestion}
        ask={<AskTab assistant={assistant} onAction={handleAssistantAction} />}
        explore={<ExploreTab investigation={investigation} lens={activeLens} />}
        evidence={
          <EvidenceTab scene={scene} focus={focus} onOpenInspector={() => navigate(inspectorHref)} />
        }
        sources={<SourcesTab scene={scene} />}
        initialTab={initialPanelTab}
      />
    </main>
  )
}

function selectedRecordsFromFocus(focus: FocusValue): SelectedRecordInput[] {
  switch (focus.kind) {
    case 'event': return [{ recordType: 'event', recordId: focus.eventId }]
    case 'claim': return [{ recordType: 'claim', recordId: focus.claimId }]
    case 'relationship': return [{ recordType: 'relationship', recordId: focus.relationshipId }]
    case 'source': return [{ recordType: 'source', recordId: focus.sourceId }]
    case 'passage': return [{ recordType: 'passage', recordId: focus.passageId }]
    case 'entity':
      return [{ recordType: focus.entityType === 'place' ? 'place' : 'entity', recordId: focus.entityId }]
    default: return []
  }
}
