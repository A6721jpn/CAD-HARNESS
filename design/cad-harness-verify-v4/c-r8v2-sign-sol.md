# C-R8v2 review — sol

BLOCK

The paired adjacency and local-opening scope in `PLAN-V4-ADDENDUM-C.md:151-152` address my C-R8 B1/B2 clarification requests. Remaining finding:

**B1 — `PLAN-V4-ADDENDUM-C.md:153`: source area is not an impossibility certificate, and automatic dropping changes the required topology.** The 0.25 mm minimum radius constrains the **final part**. Line 152 explicitly permits outward certified approximation elsewhere. Therefore an original component smaller than the derived disc area may be enlarged into a valid separate component within the existing fidelity bounds; source area alone does not prove that no compliant fit exists. “Cannot be produced” is not established by this predicate.

Dropping those components also contradicts the preserved piece-count/topology requirements at `:135` and `:141`. Scoring the original mask and reporting deletions makes the loss visible but does not preserve topology. A rough-match answer is not an explicit exception to those gates. The morning notification at `:155-156` cannot substitute for advance authorization of that exception.

Concrete fix without new user numbers: retain each 4-connected component; attempt the permitted certified fit, including bounded outward approximation, and refuse with stress FAIL if no compliant geometry is obtained. Do not classify every sub-disc source area as impossible. If deletion is instead desired, obtain explicit authorization for a **lossy topology exception**, expressly supersede the affected C-R6/C-R7 gates, and specify separate original/retained/output component counts and correspondence in the recipe and independent checker. Describe the area cutoff as an authorized simplification policy, not a consequence proved by min-R.

Retain all fourteen geometric-pass cases, original-mask fidelity, one final registration, actual-output radius/access checks, valid separated solids and pre-finalization hash commitments. No new acceptance values proposed. This review writes only this signature; no source/stress edits, user/private attachment access or commit. C-R7 offline verification remains separate ongoing work.
