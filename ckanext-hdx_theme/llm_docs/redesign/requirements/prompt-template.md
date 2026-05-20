# v2 Redesign Task — Analysis & Requirement Definition

## Context

We are working on the **v2 redesign** of HDX.

- Follow existing v2 patterns, components, and constraints
- Use design tokens and BEM conventions
- Avoid Bootstrap entirely
- Use `v2=true` to scope changes where needed
- Preserve ALL existing functionality, logic, and analytics unless explicitly stated otherwise

---

## Task

We need to work on:

👉 [COMPONENT / PAGE / FEATURE NAME]

Figma exports:
- [path/to/export-1.html]
- [path/to/export-2.html]
- [etc.]

---

## Scope

Clearly define what is INCLUDED:
- [...]

Clearly define what is OUT OF SCOPE:
- [...]

---

## Goal

Create a requirement/task in:

`llm_docs/redesign/requirements/`

---

## What to do

### 1. Audit existing implementation

- Identify:
  - Templates / snippets / macros involved
  - Data sources (backend, template vars, helpers)
  - Existing logic and behaviors
- Check:
  - Analytics (Mixpanel, etc.)
  - Query params / URL behavior (if applicable)
  - Dependencies (Bootstrap, legacy CSS, JS)

---

### 2. Audit Figma design (CRITICAL)

- Extract:
  - Layout and structure
  - Spacing, alignment, backgrounds
  - Components and variants
  - Responsive behavior (XL / MD / SM)

---

### 3. Compare current vs Figma

- Identify:
  - Visual differences
  - Structural differences
  - Behavioral differences

---

### 4. Component & system mapping

- Map UI elements to:
  - Existing reusable components
- If missing:
  - Propose minimal extensions

⚠️ Do NOT create new components unless necessary

---

### 5. Behavior & logic

- Define:
  - Interactions (dropdowns, toggles, expand/collapse, etc.)
  - State handling (use CSS pseudo-classes, NOT explicit states like `is-hovered`)
- Preserve:
  - Existing logic
  - Backend behavior
  - Analytics

---

### 6. Responsive behavior

Define behavior for:

- XL
- MD
- SM

⚠️ Must match Figma exactly

---

### 7. Template strategy

- Use `v2=true` to scope changes
- Avoid duplicating CKAN blocks
- Replace inline where needed

Ensure:
- No regression for non-v2 pages

---

### 8. Constraints

- ❌ No Bootstrap (`container`, `row`, `col-*`, `d-*`, etc.)
- ❌ No explicit hover states (`is-hovered`, `state-hovered`)
- ✅ Use CSS pseudo-classes (`:hover`)
- ✅ Use design tokens
- ✅ Follow BEM
- ✅ Reuse existing components
- ❌ No hacks

---

### 9. Open questions (MANDATORY)

- List ALL uncertainties
- DO NOT assume anything
- Ask before making decisions

Examples:
- [...]
- [...]

---

## Output

The requirement file MUST include:

- Audit findings
- Figma analysis
- Comparison (current vs target)
- Options considered
- Recommended approach
- Open questions

---

## Critical mindset

- Be conservative (do not break existing behavior)
- Match Figma pixel-accurately
- Prefer reuse over new implementations
- Ask questions instead of guessing

---

DO NOT implement anything.
ASK QUESTIONS before making decisions.

---

## Lifecycle

| Phase | Action |
|-------|--------|
| Analysis | List ALL open questions in section 9. Do not assume. |
| Implementation | Resolve questions; document resolutions in "Confirmed Decisions" or "Implementation Notes". |
| After `implemented` | Replace "Open questions" section with "Decisions Taken" table. Remove the Verification section. |
