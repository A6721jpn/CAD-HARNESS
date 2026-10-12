# CAD-HARNESS VERIFY — grok sign

COUNTER. Blocker is the S1 volume expression only.

The edge term `(2−π/2)(58+42)2²` is the right removal for four 90° edges of length counted in full. The corner term `+(20/3−2π)2³` is not. A PartDesign fillet is a rolling ball: each top corner keeps a sphere octant (`π r³/6`) inside the `r³` cube. The edge term already counts both corner strips, and each corner still removes `(π/3−1)r³` more. Four corners subtract `4(π/3−1)2³`.

Those two expressions differ by about 4.58 mm³ on a solid near 37795 mm³, relative about 1.21×10⁻⁴, outside the relative 1e-4 gate. PLAN-CONSENSUS.md line 29 stops on a fixture mismatch and forbids editing gold to the measured solid. This expression stops Phase 2 before Sol.

## Replacement

In the S1 gold cell, replace the volume expression with:

`V=58×42×16−18×14×4−(2−π/2)(58+42)2²−4(π/3−1)2³`
