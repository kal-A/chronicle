# Timeline Generation

## Purpose

The timeline is a selective, question-relevant chronology backed by evidence, not every extracted date sorted into a list.

## Workflow

1. Identify candidate events and communications.
2. Normalize date expressions without erasing uncertainty.
3. Separate event/source/report/sent/received/awareness/discovery/interpretation times.
4. Cluster duplicate descriptions while preserving source-specific claims.
5. Classify event role and relevance to the approved scope.
6. Link actors, institutions, places, communications, claims, and passages.
7. Select turning points and scene groupings with reasons.
8. Validate ordering and contradictions.

TimelineEntry references an Event/Decision/Communication and presentation metadata; it does not duplicate unsupported event facts. Actor knowledge is represented only through evidence-backed KnownAtTime records.

## Verification

Reject invalid bounds, exact dates with unequal limits, untyped time roles, duplicate entries lacking a shared-event relationship, and entries without supporting records. Flag calendar conversion and timezone assumptions. Missing received-time or awareness-time remains explicit.

