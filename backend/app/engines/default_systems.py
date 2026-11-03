"""Default (editable) aluminium system definitions.

Every length / quantity is a formula. Variables available:
  W, H            overall width / height (mm)
  panels, sliding, fixed, casement   panel counts       rows, transoms
  glass_thk       glass thickness (mm)
  frame, mullion  profile section sizes entered in the designer
  glass_perimeter, glass_area         (accessories only) totals from glass step
  ...plus every key under "constants" (system-specific deductions).
These numbers are generic starting points. Real extrusion catalogues differ -
edit them in Settings -> Aluminium systems to match your supplier's system.
"""

SLIDING_WINDOW = {
    "constants": {"frame_w_deduct": 70, "frame_h_deduct": 70, "sash_h_deduct": 75,
                  "sash_overlap": 25, "glass_w_deduct": 55, "glass_h_deduct": 45},
    "glass_code": "GLASS-{glass_thk}",
    "cuts": [
        {"role": "Frame head", "profile": "AL-FR-HEAD", "qty": "1", "length": "W"},
        {"role": "Frame sill", "profile": "AL-FR-SILL", "qty": "1", "length": "W"},
        {"role": "Frame jamb", "profile": "AL-FR-JAMB", "qty": "2", "length": "H"},
        {"role": "Sash stile", "profile": "AL-SH-VERT", "qty": "2*sliding", "length": "H-sash_h_deduct"},
        {"role": "Sash rail", "profile": "AL-SH-HOR", "qty": "2*sliding",
         "length": "(W-frame_w_deduct)/panels+sash_overlap"},
        {"role": "Fixed bead (vertical)", "profile": "AL-BEAD", "qty": "2*fixed", "length": "H-sash_h_deduct"},
        {"role": "Fixed bead (horizontal)", "profile": "AL-BEAD", "qty": "2*fixed",
         "length": "(W-frame_w_deduct)/panels"},
        {"role": "Transom", "profile": "AL-TRANSOM", "qty": "transoms*panels",
         "length": "(W-frame_w_deduct)/panels"},
    ],
    "glass": {"qty": "panels*rows",
              "w": "(W-frame_w_deduct)/panels+sash_overlap-glass_w_deduct",
              "h": "(H-frame_h_deduct)/rows-glass_h_deduct"},
    "accessories": [
        {"code": "ROLLER", "qty": "2*sliding"},
        {"code": "LOCK-SLIDE", "qty": "min(sliding,1)"},
        {"code": "HANDLE-SLIDE", "qty": "sliding"},
        {"code": "SCREW-ALU", "qty": "20+8*panels"},
        {"code": "PILE-STRIP", "qty": "(2*(H-sash_h_deduct)+2*W/panels)*sliding/1000"},
        {"code": "GASKET-GLASS", "qty": "glass_perimeter/1000"},
    ],
}

CASEMENT_WINDOW = {
    "constants": {"frame_w_deduct": 70, "frame_h_deduct": 70, "sash_clear": 12,
                  "glass_w_deduct": 80, "glass_h_deduct": 80, "mullion_w": 45},
    "glass_code": "GLASS-{glass_thk}",
    "cuts": [
        {"role": "Frame head", "profile": "AL-FR-HEAD", "qty": "1", "length": "W"},
        {"role": "Frame sill", "profile": "AL-FR-SILL", "qty": "1", "length": "W"},
        {"role": "Frame jamb", "profile": "AL-FR-JAMB", "qty": "2", "length": "H"},
        {"role": "Mullion", "profile": "AL-MULLION", "qty": "max(panels-1,0)", "length": "H-frame_h_deduct"},
        {"role": "Casement sash (horizontal)", "profile": "AL-CS-SASH", "qty": "2*casement",
         "length": "(W-frame_w_deduct-(panels-1)*mullion_w)/panels-sash_clear"},
        {"role": "Casement sash (vertical)", "profile": "AL-CS-SASH", "qty": "2*casement",
         "length": "(H-frame_h_deduct)/rows-sash_clear"},
        {"role": "Fixed bead (horizontal)", "profile": "AL-BEAD", "qty": "2*fixed",
         "length": "(W-frame_w_deduct-(panels-1)*mullion_w)/panels"},
        {"role": "Fixed bead (vertical)", "profile": "AL-BEAD", "qty": "2*fixed",
         "length": "(H-frame_h_deduct)/rows"},
        {"role": "Transom", "profile": "AL-TRANSOM", "qty": "transoms*panels",
         "length": "(W-frame_w_deduct-(panels-1)*mullion_w)/panels"},
    ],
    "glass": {"qty": "panels*rows",
              "w": "(W-frame_w_deduct-(panels-1)*mullion_w)/panels-glass_w_deduct",
              "h": "(H-frame_h_deduct)/rows-glass_h_deduct"},
    "accessories": [
        {"code": "HINGE-CASE", "qty": "2*casement+(H>1200)*casement"},
        {"code": "HANDLE-CASE", "qty": "casement"},
        {"code": "STAY-ARM", "qty": "casement"},
        {"code": "SCREW-ALU", "qty": "20+10*panels"},
        {"code": "GASKET-GLASS", "qty": "glass_perimeter/1000"},
    ],
}

SLIDING_DOOR = {
    "constants": {"frame_w_deduct": 90, "frame_h_deduct": 60, "sash_h_deduct": 70,
                  "sash_overlap": 30, "glass_w_deduct": 70, "glass_h_deduct": 110},
    "glass_code": "GLASS-{glass_thk}",
    "cuts": [
        {"role": "Frame head", "profile": "AL-DR-FR-HEAD", "qty": "1", "length": "W"},
        {"role": "Track sill", "profile": "AL-DR-SILL", "qty": "1", "length": "W"},
        {"role": "Frame jamb", "profile": "AL-DR-FR-JAMB", "qty": "2", "length": "H"},
        {"role": "Sash stile", "profile": "AL-DR-SH-VERT", "qty": "2*sliding", "length": "H-sash_h_deduct"},
        {"role": "Sash rail", "profile": "AL-DR-SH-HOR", "qty": "2*sliding",
         "length": "(W-frame_w_deduct)/panels+sash_overlap"},
        {"role": "Fixed bead (vertical)", "profile": "AL-BEAD", "qty": "2*fixed", "length": "H-sash_h_deduct"},
        {"role": "Fixed bead (horizontal)", "profile": "AL-BEAD", "qty": "2*fixed",
         "length": "(W-frame_w_deduct)/panels"},
    ],
    "glass": {"qty": "panels*rows",
              "w": "(W-frame_w_deduct)/panels+sash_overlap-glass_w_deduct",
              "h": "(H-frame_h_deduct)/rows-glass_h_deduct"},
    "accessories": [
        {"code": "ROLLER-HD", "qty": "2*sliding"},
        {"code": "LOCK-SLDR", "qty": "min(sliding,1)"},
        {"code": "HANDLE-SLIDE", "qty": "sliding"},
        {"code": "SCREW-ALU", "qty": "24+8*panels"},
        {"code": "GASKET-GLASS", "qty": "glass_perimeter/1000"},
    ],
}

HINGED_DOOR = {
    "constants": {"frame_w_deduct": 90, "frame_h_deduct": 60, "leaf_clear": 10,
                  "glass_w_deduct": 90, "glass_h_deduct": 90, "mullion_w": 45},
    "glass_code": "GLASS-{glass_thk}",
    "cuts": [
        {"role": "Frame head", "profile": "AL-DR-FR-HEAD", "qty": "1", "length": "W"},
        {"role": "Threshold", "profile": "AL-DR-THR", "qty": "1", "length": "W"},
        {"role": "Frame jamb", "profile": "AL-DR-FR-JAMB", "qty": "2", "length": "H"},
        {"role": "Leaf stile", "profile": "AL-DR-LEAF-V", "qty": "2*casement", "length": "H-frame_h_deduct-leaf_clear"},
        {"role": "Leaf rail", "profile": "AL-DR-LEAF-H", "qty": "2*casement",
         "length": "(W-frame_w_deduct)/panels-leaf_clear"},
        {"role": "Fixed bead (horizontal)", "profile": "AL-BEAD", "qty": "2*fixed",
         "length": "(W-frame_w_deduct)/panels"},
        {"role": "Fixed bead (vertical)", "profile": "AL-BEAD", "qty": "2*fixed", "length": "H-frame_h_deduct"},
    ],
    "glass": {"qty": "panels*rows",
              "w": "(W-frame_w_deduct)/panels-glass_w_deduct",
              "h": "(H-frame_h_deduct)/rows-glass_h_deduct"},
    "accessories": [
        {"code": "HINGE-DR", "qty": "3*casement"},
        {"code": "LOCK-DR", "qty": "casement"},
        {"code": "HANDLE-DR", "qty": "casement"},
        {"code": "SCREW-ALU", "qty": "24+8*panels"},
        {"code": "GASKET-GLASS", "qty": "glass_perimeter/1000"},
    ],
}

DEFAULT_SYSTEMS = [
    {"code": "SLIDING-WIN-2T", "name": "Sliding window (2-track)", "kind": "window", "config": SLIDING_WINDOW},
    {"code": "CASEMENT-WIN", "name": "Casement window", "kind": "window", "config": CASEMENT_WINDOW},
    {"code": "SLIDING-DOOR", "name": "Sliding door", "kind": "door", "config": SLIDING_DOOR},
    {"code": "HINGED-DOOR", "name": "Hinged door", "kind": "door", "config": HINGED_DOOR},
]
