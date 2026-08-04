import { run, type RunOptions } from 'axe-core'

export async function expectNoA11yViolations(
  container: Element,
  options: RunOptions = {},
) {
  const results = await run(container, options)
  if (results.violations.length > 0) {
    const summary = results.violations
      .map(
        (violation) =>
          `${violation.id}: ${violation.help} (${violation.nodes.length} node(s))`,
      )
      .join('\n')
    throw new Error(`Accessibility violations found:\n${summary}`)
  }
}
