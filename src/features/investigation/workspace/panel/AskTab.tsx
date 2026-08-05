/**
 * Placeholder for the persistent Ask surface (map-first-workspace-
 * instructions.md §15) — the real conversational assistant, its scope
 * proposal flow, and generation progress are D0.5 work. This tab exists now
 * so the panel's tab set and layout are final in D0.3, without pretending
 * the assistant answers questions it doesn't yet have a backend for.
 */
export function AskTab() {
  return (
    <div className="flex flex-col gap-3">
      <p className="text-sm text-neutral-600 dark:text-neutral-400">
        Ask a question grounded in this investigation&rsquo;s reviewed evidence.
      </p>
      <input
        type="text"
        disabled
        placeholder="Coming in a later phase — the assistant isn't wired up yet."
        className="w-full rounded-lg border border-neutral-300 bg-neutral-50 px-3 py-2 text-sm text-neutral-400 dark:border-neutral-700 dark:bg-neutral-950"
      />
      <p className="text-xs text-neutral-500 dark:text-neutral-400">
        This tab is a placeholder for Phase D0.5. It intentionally does not
        simulate answering questions yet.
      </p>
    </div>
  )
}
