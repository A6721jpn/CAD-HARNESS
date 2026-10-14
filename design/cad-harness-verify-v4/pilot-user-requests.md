# Pilot user requests (intake) - v4
Source: the user personally (13:52 decision; delivered 2026-10-14 13:59-14:05 JST). Request text copied verbatim from pilot-user/requests.md (sha256 f386afc7a3a05bb9b3e5600e912bd0f7ee7df7a3fac8ee5467c65d27d24062df). Nothing added, paraphrased or invented. The user gave 5 requests (not 10): N <= 5.
Attachments live in pilot-user/. STEP files over 1 MB are NOT committed to git (sha256 and size recorded here).

### U1
- Submitted (JST): 2026-10-14 13:59-14:05
- Request text (verbatim):
```
この筐体を長手方向が鉛直になるようにガタガタしないように直立させて、プラ箱のNF13 Boxにぴしっとおさまるようなホルダーを作って。並べ方は規則的に適当に並べて。筐体がささるところに番号をつけられるようにして。3Dプリンターで作って両面テープでNF13 boxに貼るから。
```
- Critical dimensions / tolerances (user-supplied): request text only: upright long axis vertical, no rattle, fits NF13 Box (box dimensions NOT given by user), numbering per slot, double-sided tape mount; no numeric values given
- Allowed defaults: not specified by the user
- Attachments: pilot-user/U1.step  sha256 05f366a5e9a0bd7b451f063ef04ca10447b2028b09f81c734b01a6313a0cf8ae  2695956 bytes  (not in git, >1MB)
- Expected deliverable: FreeCAD 1.1.4 single-part model (FCStd + STEP)
- Eligibility: pending 3-party screening (E3-E7)

### U2
- Submitted (JST): 2026-10-14 13:59-14:05
- Request text (verbatim):
```
このガラスを横に立てて並べる保管用ボックスを3Dプリンターで作るから設計して。10枚入るようにして。ガタガタしないようにして。端面が剥げやすいからガラス端面にはなにもあてないようにして
```
- Critical dimensions / tolerances (user-supplied): request text only: capacity 10 glass sheets, standing on edge, no rattle, nothing touches glass edge faces; no numeric clearances given
- Allowed defaults: not specified by the user
- Attachments: pilot-user/U2.step  sha256 a80d43f6180be313290647e94ae31e0a7c6f71658348252f09db733318791bd9  808687 bytes  (committed)
- Expected deliverable: FreeCAD 1.1.4 single-part model (FCStd + STEP)
- Eligibility: pending 3-party screening (E3-E7)

### U3
- Submitted (JST): 2026-10-14 13:59-14:05
- Request text (verbatim):
```
このSTEPは表面がなめらかなはずなんだけど、いくつかのサーフェスに分かれてしまっている。角があるなどの明らかにサーフェス境界が必要なところではない自由曲面の意匠面のサーフェス境界をなくして、かつG3連続でなめらかに意匠面を接合してほしい。元データとの誤差は0.005mmまで絶対値で許容する。
```
- Critical dimensions / tolerances (user-supplied): 0.005 mm absolute deviation from the original data (user); G3 continuity across the merged freeform design surfaces (user)
- Allowed defaults: not specified by the user
- Attachments: pilot-user/U3.step  sha256 3cdf4f1d3e9f3e83a7341a0d9e6f9ce2ce8e74c63d578bc27e8810a89ac6fd36  2127563 bytes  (not in git, >1MB)
- Expected deliverable: FreeCAD 1.1.4 single-part model (FCStd + STEP)
- Eligibility: pending 3-party screening (E3-E7)

### U4
- Submitted (JST): 2026-10-14 13:59-14:05
- Request text (verbatim):
```
このフレームの下面の自由曲面部分を、上面からオフセットした形に修正しつつ厚みを2mmにして。下面に接続されているフィーチャーもいい感じに接続し直して。周辺フィーチャーの外寸は変えないで、オフセットさせて自由曲面部分の肉厚だけかえたい。
```
- Critical dimensions / tolerances (user-supplied): request text only: freeform underside = offset of top surface, wall thickness 2 mm, outer dimensions of surrounding features unchanged; no tolerance given
- Allowed defaults: not specified by the user
- Attachments: pilot-user/U4.step  sha256 d85327e5ce14ccc386d182f2d04b6d535fb49cd74c456bad6aa34e0be630c92a  7081133 bytes  (not in git, >1MB)
- Expected deliverable: FreeCAD 1.1.4 single-part model (FCStd + STEP)
- Eligibility: pending 3-party screening (E3-E7)

### U5
- Submitted (JST): 2026-10-14 13:59-14:05
- Request text (verbatim):
```
アップルのロゴマークをネットから探してきて、それをCADで構築して。平板を打ち抜いたような形状で、厚みとロゴサイズをパラメトリックにしてCADモデルを構築して。あと３軸CNCで作るから最小工具Rを0.25で考えて構築して。
```
- Critical dimensions / tolerances (user-supplied): minimum tool radius R0.25 mm for 3-axis CNC (user); thickness and logo size must be parameters (user; no values given)
- Allowed defaults: not specified by the user
- Attachments: none (user: no attachment)
- Expected deliverable: FreeCAD 1.1.4 single-part model (FCStd + STEP)
- Eligibility: pending 3-party screening (E3-E7)

## User answers 2026-10-14 14:25 JST (verbatim in pilot-user/requests.md, sha256 a3a75986e005d18f9e2c734638b455adb8370b362095fcc4fe149bee3ae20593)
```
NF13は合ってる　長手方向はパーツのY軸にあたるかな　外寸がながい軸ね　ガタは0.5mm以下、テープ厚み0.5 　並べる数は指定なし、刻印がよい
ガラスは1.3mm　端面は厚みをつけた1.3mmの外周帯状の面であたってさえなければOK　ガラスは凸面側は当ててよいが、凹面は最低限の接触にしてほしい
対応範囲は広げないが最終的にはカバーする。なぜいま対応範囲外なのかを詳しく教えて。
ロゴデータは添付 (U5_logo.png, raster PNG 38KB)
```
- U1 user-given: box = JEJ Astage NF-13CR (inner 245 x 365 x 140 mm per the catalogue, user-confirmed); long axis = part Y (longest outer dimension) vertical; play <= 0.5 mm; tape thickness 0.5 mm; count unspecified; numbers engraved.
- U2 user-given: glass thickness 1.3 mm; edge face = the 1.3 mm-wide perimeter band, must not be touched; the convex face may contact; the concave face should have minimal contact.
- U3/U4: the user says the scope is not expanded now but will eventually be covered; they stay excluded (E3) in this pilot.
- U5 attachment: pilot-user/U5_logo.png, raster RGBA 814x1000, 39139 bytes, sha256 cff917e0b7e317eff88977aafea0379a99522e3ab120b36b7d73ee5626bfdd3b.
