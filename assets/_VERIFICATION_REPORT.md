# Sprite Set Verification Report — little-buddy-card
Generated: 2026-07-14 by kanban task t_a62c80a8 (verifier worker)

## Scope
Validate final sprite set at:
  /root/little-buddy-card/assets/sprites/
Expectation (task body): exactly 40 PNGs (35 pet_*, 5 tree_*), no duplicates,
all 64x64 nearest-neighbor pixel-art, character identity consistent per LoRA
strategy (RDXL_Pixel_Art base + littlebuddy_pixel LoRA @0.8, token 'littlebuddy').

## Results — PASS on structural acceptance
  Total PNGs ............ 40   (EXACTLY as required)
  pet_*.png ............. 35   (pet_01..pet_35, contiguous)
  tree_*.png ............ 5    (tree_01..tree_05, contiguous)
  other/stray PNGs ...... 0
  Duplicates (md5) ...... none
  Dimensions ............ ALL 40 are 64x64
  Blank/flat check ...... none (distinct-color counts 86–984 per image)

  => "Exactly 40 files present, no duplicates"  : MET
  => "All 64x64"                                  : MET

## Style consistency — PARTIAL (one documented claim is false)
Pipeline is uniform: every sprite uses the same model+LoRA+0.8 strength and the
same 512->64 NN downscale. So rendering treatment IS consistent.

HOWEVER, the parent task t_56b44faa claimed the trees were generated with the
"white-bg convention identical to pet_*.png." That claim does NOT hold:

  White-background share (near-white pixel % > 50):
    Pets with white bg : 25 / 35
    Pets WITHOUT white bg (colored/dark bg): 10
      -> pet_02, pet_10, pet_14, pet_15, pet_19, pet_22, pet_23, pet_27,
         pet_28, pet_34
    Trees with white bg: 1 / 5  (only tree_04)
    Trees WITHOUT white bg: 4 / 5
      -> tree_01 dark-blue, tree_02 dark-gray, tree_03 dark/black,
         tree_05 purple/black

  Conclusion: 34 of 40 sprites do NOT sit on a white background. The
  "white-bg convention" is not the actual convention — backgrounds are varied.
  This is internally consistent across the set, but it contradicts the written
  handoff. Downstream (the card) must NOT assume white-bg for compositing.

## Open item — cannot be machine-verified in this environment
A vision/style-quality pass was NOT possible: no vision model is wired into this
agent (image_generate is text-to-image only). Distinct-color counts (up to 984
of 4096 px in pet_10) suggest the 512px SOURCES were smooth/AA-shaded rather
than hard-paletted pixel art; NN downscale preserves that smoothing. If the card
requires CRISP hard-edged pixel art (limited palette), the sprites may read as
soft-shaded — this needs a human eyeball pass. A contact sheet exists for that:
  /root/little-buddy-card/assets/_contact_sheet.png  (512x320, 8 cols, 40 sprites)

## Recommendation for downstream
1. Decide background policy: either (a) accept varied backgrounds, or (b) re-run
   the 10 pets + 4 trees with a forced white-bg / transparent-bg prompt. Trees are
   NOT yet wired into the card (parent noted they feed /local/.../trees/<stage>.png),
   so this only affects the staging set.
2. Do a human visual pass on the contact sheet before shipping the card.

## Artifacts produced by this verifier
  /root/little-buddy-card/scripts/_verify_all.py      (40-file full analysis)
  /root/little-buddy-card/scripts/_verify_trees.py    (tree bg probe)
  /root/little-buddy-card/scripts/_verify_bg.py       (modal-bg probe)
  /root/little-buddy-card/scripts/_contact_sheet.py   (contact sheet builder)
  /root/little-buddy-card/assets/_contact_sheet.png   (visual reference)
