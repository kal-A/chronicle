import type { CSSProperties } from 'react'
import type { GeneratedInvestigation } from '../model/generatedInvestigation'
import { AtlanticAtlas } from './AtlanticAtlas'

const PARTICLES = Array.from({ length: 42 }, (_, index) => ({
  x: 4 + ((index * 37) % 92),
  y: 7 + ((index * 53) % 86),
  delay: (index % 9) * 34,
  size: index % 5 === 0 ? 3 : 2,
}))

export function CartographicTransition({
  investigation,
  question,
}: {
  investigation: GeneratedInvestigation
  question: string
}) {
  const scene = investigation.scenes.find(
    (candidate) => candidate.id === investigation.interactionSpec.defaultSceneId,
  )

  return (
    <div className="cartographic-transition" role="status" aria-label="Opening investigation">
      <div className="cartographic-transition__map" aria-hidden="true">
        <AtlanticAtlas reveal={1} drawProgress={1} />
      </div>
      <div className="cartographic-transition__particles" aria-hidden="true">
        {PARTICLES.map((particle, index) => (
          <span
            key={index}
            style={
              {
                '--particle-x': `${particle.x}%`,
                '--particle-y': `${particle.y}%`,
                '--particle-delay': `${particle.delay}ms`,
                '--particle-size': `${particle.size}px`,
                '--travel-x': `${50 - particle.x}vw`,
                '--travel-y': `${50 - particle.y}vh`,
              } as CSSProperties
            }
          />
        ))}
      </div>
      <div className="cartographic-transition__copy">
        <p>Resolving the investigation around</p>
        <h2>{scene?.title ?? investigation.presentation.title}</h2>
        <span>{question}</span>
      </div>
    </div>
  )
}
