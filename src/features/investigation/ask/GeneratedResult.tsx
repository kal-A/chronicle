import type { AgentRunRecord, CorpusBuildAccepted } from '../assistant/agentApi'

/**
 * The honest inline outcome of a live generation run: a cited answer, a
 * principled abstention, or a bounded failure. A generated corpus is
 * passage-only and does not populate the map-first workspace, so the outcome is
 * presented as text with its citations and limitations rather than a scene.
 */
export function GeneratedResult({
  run,
  build,
  onAskSomethingElse,
}: {
  run: AgentRunRecord
  build: CorpusBuildAccepted
  onAskSomethingElse: () => void
}) {
  const answer = run.finalAnswer
  const isAnswered = run.status === 'answer_ready' && answer !== null

  return (
    <section className="chronicle-generated-result" aria-live="polite">
      <p className="chronicle-eyebrow">
        Acquired {build.acquired} source{build.acquired === 1 ? '' : 's'} ·{' '}
        {build.passages} passage{build.passages === 1 ? '' : 's'}
      </p>

      {isAnswered ? (
        <>
          <h2>What the sources support</h2>
          <p className="chronicle-generated-answer">{answer!.directAnswer}</p>
          {answer!.keyPoints.length > 0 ? (
            <ul className="chronicle-generated-points">
              {answer!.keyPoints.map((point) => (
                <li key={point.statementId}>{point.text}</li>
              ))}
            </ul>
          ) : null}
          <p className="chronicle-generated-citations">
            {answer!.citations.length} cited passage
            {answer!.citations.length === 1 ? '' : 's'} · every claim traces to a
            retrieved source.
          </p>
          {answer!.limitations.length > 0 ? (
            <div className="chronicle-generated-limitations">
              <h3>Limitations</h3>
              <ul>
                {answer!.limitations.map((limitation) => (
                  <li key={limitation}>{limitation}</li>
                ))}
              </ul>
            </div>
          ) : null}
        </>
      ) : run.status === 'abstained' ? (
        <>
          <h2>Chronicle abstained</h2>
          <p className="chronicle-generated-answer">
            {run.abstentionReason ??
              'The acquired evidence could not support a grounded answer.'}
          </p>
          <p className="chronicle-generated-honesty">
            Chronicle declines to assert what the sources it found do not support —
            an honest abstention, not a failure.
          </p>
        </>
      ) : (
        <>
          <h2>Generation could not complete</h2>
          <p role="alert" className="chronicle-generated-answer">
            {run.errorMessage ??
              'The local research run did not complete. Try again or narrow the scope.'}
          </p>
        </>
      )}

      <button
        type="button"
        onClick={onAskSomethingElse}
        className="chronicle-secondary-action"
      >
        Ask something else
      </button>
    </section>
  )
}
