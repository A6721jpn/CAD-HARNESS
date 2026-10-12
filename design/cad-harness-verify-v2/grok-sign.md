# CAD-HARNESS VERIFY v2 — grok sign

COUNTER. The blocker is the frozen user-text suffix only.

Analytic volumes match a fresh derivation: W1 `17112π`, W2 `39200`, W3 `624π²` with bbox `[0,40,-8,32,-8,8]`, W4 `33280`, W5 `21060π−120`, W6 `83552−525π−(160−4/3)`, S2 stock `45500`, A1 `54000−300π`, C2 `36784−396π`, C3 `29808−220.5π`, and the K1/K2/K3 wrong-candidate deltas `+888π` / `+90π` / `−136.5π`. Bar counts stay 8/10, 2/3, 4/5, 2/3, 4/5, 6/6, 4/6, eval-v1 8/10, legacy 4/4. C stays outside `bar_met`.

`PLAN-V2-CONSENSUS.md` line 47 appends 「寸法列はX×Y（3つ目はZ）。」 to every user payload. That sentence is false for W1, W2, W3, W4, and W5, and it is a grading note rather than a machining instruction. Line 74’s `(X半幅,Y半幅,Z0..H)` list is the right place for that notation.

## Replacement

Replace the sentence in line 47 that begins `下表の説明列＋「寸法列は` with:

`下表の説明列の直後に「単位mm。他の加工なし。」だけを足したものを本文とする。W3とA1以外は、その前に「XY中心、下面Z=0。」を置く。「寸法列はX×Y（3つ目はZ）。」はpayloadに入れない。`
