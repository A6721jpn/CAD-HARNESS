# Questions for the user (morning 2026-10-15)

## Not freeze-blocking


## Critical values

Checked `DECISIONS.md`. No unanswered critical value remains, so none is listed here.

Already answered: U1/U2 play <= 0.5 mm per side and 3 degrees per side; U2 minimum gap >= 0.5 mm; U4 +/- 0.1 mm; U5 rough match, with the C-D(a) lenient thresholds as the fidelity gates; engraving size and depth delegated (C-D(b): 5.0 mm height and 0.6 mm depth); new-family extra call budget with no upper limit; tape location anywhere; U3 G2 plus <= 0.005 mm. U2 minimal concave-face contact is qualitative, with no numeric gate.

## Notes for the user
- U5 failed contour preparation twice (cycle 1: transparent PNG with a fixture recipe, then multiple pieces refused; cycle 2: curve fit could not meet its internal 1-pixel budget). No live budget was spent. Being fixed in cycle 3 with a generic stress suite and a fit tolerance tied to the lenient 'rough match' fidelity.

## Resolved
- 2026-10-16 19:51 JST: U5 bridges/backing question answered by the user: keep separate pieces, no bridges or backing (DECISIONS.md, C-R6).
