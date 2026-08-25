# Scientific writing style

This contract applies to the README, documentation, tutorials, browser site,
examples, release notes, issue templates, and other user-facing project text.

## Voice

- Write for astronomers and scientific Python users.
- State the object, operation, and consequence. Prefer concrete descriptions
  of the support, supplied centres, paths, coordinates, and measured tracer.
- Use short paragraphs and descriptive headings. Use lists for procedures and
  comparisons, not as a substitute for explanation.
- Distinguish mathematical definitions, implementation choices, and
  paper-reproduction settings.
- Use “we” only for an explicit project or author action. Do not use a vague
  collective voice to imply consensus.

## Terminology

- `support`: the accepted connected pixel mask, written as $\Omega$ in
  mathematical text.
- `supplied centre`: a user-provided centre $c_k$; do not call it an inferred
  nucleus unless it is one in the input data.
- `support-constrained distance`: shortest-path distance on the accepted
  pixel graph.
- `relative boundary depth`, $\rho_D$: $d_k/(d_k+b)$.
- `normalized progression`, $\rho_X$: $d_k/L_k$ within centre-associated
  region $B_k$.
- `registered tracer`: a pixel-aligned scalar field measured on an already
  built geometry.
- Use British spelling in prose (`centre`, `normalised` only when not naming
  the manuscript coordinate, `colour`). Preserve public parameter and
  attribute spellings exactly.

## Avoid

Do not use generic product slogans or contrastive fragments such as:

- “Boundary depth is not longitudinal progression.”
- “Unlock insights”, “powerful”, “seamless”, “next-generation”, “robust and
  scalable”, or “designed for everyone”.
- “This changes everything”, “see the difference”, or similar unqualified
  claims.
- “Provenance” as a navigation label when “implementation record”, “source
  record”, or a specific document title is clearer.

Replace slogans with a scientific observation. For example:

> In a narrow tail, $\rho_D$ remains sensitive to the nearby lateral boundary,
> whereas $\rho_X$ increases with support-constrained distance from the
> supplied centre.

## Claims and qualification

- Do not claim performance, accuracy, scientific validity, interoperability,
  or name availability beyond tested evidence.
- Identify synthetic examples as synthetic and observational inputs as
  observational.
- State when a behaviour follows from the 8-neighbour pixel-graph
  implementation rather than from the continuous mathematical definition.
- Describe release state explicitly: PyPI, Zenodo, repository rename, and
  manuscript state must not be implied.

## Code and notebooks

- Introduce the scientific question before the code that answers it.
- Keep examples executable and use the canonical top-level import.
- Explain why a coordinate is selected for a measurement.
- Report array shapes, units, and coordinate conventions at the point where
  ambiguity could arise.
- Do not hide paper-reproduction dtype or algorithm settings behind generic
  defaults.
