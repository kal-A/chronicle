function rangeProgress(progress: number, start: number, end: number): number {
  if (progress <= start) return 0
  if (progress >= end) return 1
  return (progress - start) / (end - start)
}

export function resolveAtlasDrawStages(progress: number) {
  const clamped = Math.max(0, Math.min(1, progress))
  return {
    coastline: clamped,
    graticule: rangeProgress(clamped, 0.42, 0.76),
    labels: rangeProgress(clamped, 0.7, 0.94),
    instruments: rangeProgress(clamped, 0.84, 1),
    settledInk: rangeProgress(clamped, 0.93, 1),
  }
}
