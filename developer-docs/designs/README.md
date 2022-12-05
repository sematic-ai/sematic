# Design Docs

This repo contains designs that have been accepted and are in the course of
being implemented, or have been implemented.

**When creating a new design:**
- start from the template, fill in the specific information, and add a
  reference to this new file at the end of
  [the list below](#list-of-accepted-design-docs).
- open a PR with the new design, request reviews as usual, and iterate on the
  comments
- when the PR is accepted, update the acceptance date entry in the doc, and
  merge the PR

**During implementation**, things might not exactly match what was designed, so
when making implementation decision which contradict the design, also update
the contents of the design doc, and add a bullet point mentioning this in the
updates entry, and include these changes in the same commits that contain the
implementation.

**When the design becomes obsolete** due to new changes, then mark it as such
by adding an `[Obsolete]` tag at the beginning of the respective bullet point
below, and update and uncomment the entry in the design doc referring the
change that made the design irrelevant.

### List of Accepted Design Docs

- [Function Output Artifact Caching](function_output_artifact_caching.md)
