#!/usr/bin/env python3
"""Generate the static steel section reference pages for theolternative.com.

    python3 tools/generate_steel_sections.py [path/to/sections.json]

The input is a JSON array of sections exported from the Steel Profiles catalog
(one object per section with the Core Data attribute names). When no path is
given, the trimmed copy kept in tools/data/sections-dimensions.json is used.
Only the free "Dimensions" group of each section is published; the structural
properties stay in the app.

Output (all static HTML, no runtime dependencies):
    steel-sections/index.html
    steel-sections/<lib>/index.html
    steel-sections/<lib>/<series>/index.html            table of all sizes
    steel-sections/<lib>/<series>/<size>/index.html     one page per hot-rolled section
    guides/hea-heb-hem/index.html                       data-driven guide
    sitemap.xml is rewritten with every generated URL.
"""
import json
import math
import os
import re
import sys
from collections import OrderedDict, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = "https://theolternative.com"
APP_ID = "564614324"
PRO_ID = "662511256"
PPID_EUROCODE = "65391258-17f5-4ae3-b4a6-cfd67004c5dd"
STORE_URL = f"https://apps.apple.com/app/steel-profiles/id{APP_ID}?ppid={PPID_EUROCODE}"
STORE_URL_PLAIN = f"https://apps.apple.com/app/steel-profiles/id{APP_ID}"
PRO_URL = f"https://apps.apple.com/app/steel-profiles-pro/id{PRO_ID}"
ICON = "/images/steel-profiles-free-icon.png"

# ---------------------------------------------------------------------------
# Catalog description
# ---------------------------------------------------------------------------

LIBRARIES = OrderedDict([
    ("EU", {"slug": "eu", "name": "European sections (EN)", "short": "European",
            "intro": "Hot-rolled and hollow sections to the European standards (Euronorm, EN 10025, EN 10034, "
                     "EN 10056, EN 10067, EN 10210, EN 10219) as rolled by ArcelorMittal and other European mills."}),
    ("UK", {"slug": "uk", "name": "British sections (BS)", "short": "British",
            "intro": "Universal beams, columns and bearing piles, joists, parallel flange channels, tees and angles "
                     "to BS 4-1 and BS EN 10056-1, as listed in the SCI/BCSA Blue Book."}),
])

# Dimension keys shown per entity, in order (the free "Dimensions" group of the app).
DIM_KEYS = {
    "SteelSection_H_EU": ["h", "b", "tw", "tf", "r1", "hi", "d", "ss", "weight", "area", "al", "ag"],
    "SteelSection_IPN_EU": ["h", "b", "tw", "tf", "r1", "r2", "d", "ss", "weight", "area", "al", "ag"],
    "SteelSection_UPE_EU": ["h", "b", "tw", "tf", "r1", "hi", "d", "x", "xm", "ss", "weight", "area", "al", "ag"],
    "SteelSection_UPN_EU": ["h", "b", "tw", "tf", "r1", "r2", "d", "x", "xm", "ss", "weight", "area", "al", "ag"],
    "SteelSection_U_EU": ["h", "b", "tw", "tf", "r1", "r2", "d", "x", "xm", "ss", "weight", "area", "al", "ag"],
    "SteelSection_CH_UK": ["h", "b", "tw", "tf", "r1", "r2", "d", "x", "xm", "ss", "weight", "area", "al", "ag"],
    "SteelSection_L_EU": ["h", "b", "t", "r1", "r2", "x", "y", "v1", "v2", "u1", "u2", "u3", "weight", "area", "al", "ag"],
    "SteelSection_T_EU": ["h", "b", "t", "r", "r1", "r2", "x", "y", "weight", "area"],
    "SteelSection_T_UK": ["h", "b", "tw", "tf", "r1", "y", "weight", "area"],
    "SteelSection_RHS_EU": ["h", "b", "t", "r1", "r2", "weight", "area", "al"],
    "SteelSection_CHS_EU": ["outsideDiameter", "t", "d_t", "weight", "area", "al"],
    "SteelSection_BF_EU": ["h", "t", "bulbC", "bulbD", "bulbR", "x", "y", "weight", "area", "al"],
}

# Columns of the series tables per entity.
TABLE_KEYS = {
    "SteelSection_H_EU": ["h", "b", "tw", "tf", "r1", "weight", "area"],
    "SteelSection_IPN_EU": ["h", "b", "tw", "tf", "r1", "r2", "weight", "area"],
    "SteelSection_UPE_EU": ["h", "b", "tw", "tf", "r1", "weight", "area"],
    "SteelSection_UPN_EU": ["h", "b", "tw", "tf", "r1", "r2", "weight", "area"],
    "SteelSection_U_EU": ["h", "b", "tw", "tf", "r1", "r2", "weight", "area"],
    "SteelSection_CH_UK": ["h", "b", "tw", "tf", "r1", "r2", "weight", "area"],
    "SteelSection_L_EU": ["h", "b", "t", "r1", "r2", "weight", "area"],
    "SteelSection_T_EU": ["h", "b", "t", "r", "weight", "area"],
    "SteelSection_T_UK": ["h", "b", "tw", "tf", "r1", "weight", "area"],
    "SteelSection_RHS_EU": ["h", "b", "t", "weight", "area"],
    "SteelSection_CHS_EU": ["outsideDiameter", "t", "weight", "area"],
    "SteelSection_BF_EU": ["h", "t", "bulbC", "weight", "area"],
}

# Label (HTML), unit, description.
PROPS = {
    "h": ("h", "mm", "Overall depth"),
    "b": ("b", "mm", "Overall width (flange width, or leg length)"),
    "outsideDiameter": ("D", "mm", "Outside diameter"),
    "tw": ("t<sub>w</sub>", "mm", "Web thickness"),
    "tf": ("t<sub>f</sub>", "mm", "Flange thickness"),
    "t": ("t", "mm", "Thickness (leg, wall or web)"),
    "r": ("r", "mm", "Radius of the fillet between flange and web"),
    "r1": ("r<sub>1</sub>", "mm", "Root radius (fillet between flange and web), or external corner radius for hollow sections"),
    "r2": ("r<sub>2</sub>", "mm", "Toe radius of the flange, or internal corner radius for hollow sections"),
    "hi": ("h<sub>i</sub>", "mm", "Internal depth between flanges"),
    "d": ("d", "mm", "Depth of the straight portion of the web between fillets"),
    "ss": ("s<sub>s</sub>", "mm", "Stiff bearing length"),
    "x": ("x", "mm", "Distance from the back of the web (or heel) to the centroid, horizontal"),
    "y": ("y", "mm", "Distance from the designated edge to the centroid, vertical"),
    "xm": ("x<sub>m</sub>", "mm", "Distance from the shear centre to the back of the web"),
    "v1": ("v<sub>1</sub>", "mm", "Distance from the long leg edge to the major principal axis"),
    "v2": ("v<sub>2</sub>", "mm", "Distance from the short leg edge to the major principal axis"),
    "u1": ("u<sub>1</sub>", "mm", "Distance from the corner to the minor principal axis"),
    "u2": ("u<sub>2</sub>", "mm", "Distance from the short leg edge to the minor principal axis"),
    "u3": ("u<sub>3</sub>", "mm", "Distance from the long leg edge to the minor principal axis"),
    "d_t": ("D/t", "", "Diameter to wall thickness ratio"),
    "bulbC": ("c", "mm", "Bulb width beyond the web face"),
    "bulbD": ("d", "mm", "Bulb depth at the web face"),
    "bulbR": ("r", "mm", "Bulb radius"),
    "weight": ("G", "kg/m", "Mass per metre"),
    "area": ("A", "cm²", "Cross-sectional area"),
    "al": ("A<sub>L</sub>", "m²/m", "Painting surface per metre"),
    "ag": ("A<sub>G</sub>", "m²/t", "Painting surface per tonne"),
}

# Structural properties kept in the app (names only, shown as a list on the size pages).
APP_PROPS = {
    "SteelSection_H_EU": ["I<sub>y</sub>, W<sub>el,y</sub>, W<sub>pl,y</sub>, i<sub>y</sub>", "A<sub>vz</sub> shear area",
                          "I<sub>z</sub>, W<sub>el,z</sub>, W<sub>pl,z</sub>, i<sub>z</sub>", "I<sub>T</sub> and I<sub>w</sub>",
                          "Maximum bolt size and flange gauges", "EN 1993-1-1 class for S235, S355 and S460"],
    "SteelSection_IPN_EU": ["I<sub>y</sub>, W<sub>el,y</sub>, W<sub>pl,y</sub>, i<sub>y</sub>", "A<sub>vz</sub> shear area",
                            "I<sub>z</sub>, W<sub>el,z</sub>, W<sub>pl,z</sub>, i<sub>z</sub>", "I<sub>T</sub> and I<sub>w</sub>",
                            "Maximum bolt size and flange gauges", "EN 1993-1-1 class for S235, S355 and S460"],
    "SteelSection_UPE_EU": ["I<sub>y</sub>, W<sub>el,y</sub>, W<sub>pl,y</sub>, i<sub>y</sub>", "A<sub>vz</sub> shear area",
                            "I<sub>z</sub>, W<sub>el,z</sub>, W<sub>pl,z</sub>, i<sub>z</sub>", "I<sub>T</sub> and I<sub>w</sub>",
                            "Maximum bolt size and edge distances", "EN 1993-1-1 class for S235, S355 and S460"],
    "SteelSection_L_EU": ["I<sub>y</sub>, I<sub>z</sub>, W<sub>el</sub>, W<sub>pl</sub>, i", "I<sub>u</sub>, I<sub>v</sub>, i<sub>u</sub>, i<sub>v</sub> and I<sub>yz</sub> (principal axes)",
                          "I<sub>T</sub>", "Bolt sizes, edge distances and net areas", "EN 1993-1-1 compression class"],
    "SteelSection_T_EU": ["I<sub>y</sub>, W<sub>el,y</sub>, W<sub>pl,y</sub>, i<sub>y</sub>", "I<sub>z</sub>, W<sub>el,z</sub>, W<sub>pl,z</sub>, i<sub>z</sub>",
                          "I<sub>T</sub>", "EN 1993-1-1 compression class"],
    "SteelSection_T_UK": ["I<sub>y</sub>, W<sub>el,y</sub>, W<sub>pl,y</sub>, i<sub>y</sub>", "I<sub>z</sub>, W<sub>el,z</sub>, W<sub>pl,z</sub>, i<sub>z</sub>", "I<sub>T</sub>"],
    "SteelSection_RHS_EU": ["I, W<sub>el</sub>, W<sub>pl</sub>, i about both axes", "I<sub>T</sub> and C<sub>T</sub> torsional constants"],
    "SteelSection_CHS_EU": ["I, W<sub>el</sub>, W<sub>pl</sub>, i", "I<sub>T</sub> and C<sub>T</sub> torsional constants"],
    "SteelSection_BF_EU": ["I<sub>y</sub>, W<sub>el,y</sub> at toe and bulb, W<sub>pl,y</sub>, i<sub>y</sub>",
                           "I<sub>z</sub>, W<sub>el,z</sub>, W<sub>pl,z</sub>, i<sub>z</sub>", "I<sub>T</sub>"],
}
for _e in ("SteelSection_UPN_EU", "SteelSection_U_EU", "SteelSection_CH_UK"):
    APP_PROPS[_e] = APP_PROPS["SteelSection_UPE_EU"]

STANDARDS = {
    "EU 53 62": "Euronorm 53-62", "EU 19 57": "Euronorm 19-57", "AM": "ArcelorMittal sections catalogue",
    "AA": "ArcelorMittal sections catalogue", "ASTM A 6/A 6M   07": "ASTM A6/A6M-07", "ASTM A 6/A 6M 07": "ASTM A6/A6M-07",
    "Mill": "mill catalogue", "DIN 1025 1:1963": "DIN 1025-1:1963",
    "DIN 1025 1:1995, NF A 45 209: 1983": "DIN 1025-1:1995 and NF A 45-209:1983",
    "EN 10056 1: 1998": "EN 10056-1:1998", "EN 10055:1995": "EN 10055:1995",
    "DIN 1026 2: 2002 10": "DIN 1026-2:2002-10", "DIN 1026 1: 2000, NF A 45 202: 1986": "DIN 1026-1:2000 and NF A 45-202:1986",
    "EN10219": "EN 10219", "EN10210": "EN 10210", "EN 10067": "EN 10067",
    "BS 4 1:2005": "BS 4-1:2005", "BS 4 1:1993": "BS 4-1:1993", "BS EN10056 1:1999": "BS EN 10056-1:1999",
    "BS EN10219:2006": "BS EN 10219:2006", "BS EN10219:1997": "BS EN 10219:1997", "BS EN10210:1997": "BS EN 10210:1997",
}

HOLLOW = {"RHS H", "RHS C", "SHS H", "SHS C", "CHS C", "CHS H"}

# Series: stored type -> (slug, title, short name, description HTML, size-page flag)
SERIES = OrderedDict()


def series(lib, typ, slug, title, kind, desc, sizes=True):
    SERIES[(lib, typ)] = {"slug": slug, "title": title, "kind": kind, "desc": desc, "sizes": sizes}


series("EU", "IPE", "ipe", "IPE beams", "European I beams with parallel flanges",
       "<p>IPE sections are the standard European medium flange I beams (Euronorm 19-57, tolerances to EN 10034). The number is the nominal depth in millimetres, from IPE 80 to IPE 600. They are the usual choice for floor beams, purlins and secondary members, and the parallel flanges make bolted connections straightforward.</p>"
       "<p>IPE A, IPE O and IPE AA are lighter and heavier variants with the same nominal depth: IPE A and IPE AA have thinner flanges and webs, IPE O is heavier than IPE.</p>")
series("EU", "IPEA", "ipe-a", "IPE A beams", "Light IPE variants",
       "<p>IPE A beams are the lightweight version of the IPE range: same nominal depth, thinner web and flanges, lower mass per metre. They are rolled by ArcelorMittal and listed in its sections catalogue.</p>")
series("EU", "IPEAA", "ipe-aa", "IPE AA beams", "Extra-light IPE variants",
       "<p>IPE AA beams are the lightest variant of the IPE range, for applications where stiffness rather than strength governs and every kilogram counts.</p>")
series("EU", "IPEO", "ipe-o", "IPE O beams", "Heavy IPE variants",
       "<p>IPE O beams are heavier than the IPE of the same nominal depth: thicker flanges and web, slightly larger width, more capacity without changing the floor depth.</p>")
series("EU", "IPN", "ipn", "IPN beams", "European I beams with tapered flanges",
       "<p>IPN beams (DIN 1025-1, formerly INP) are the narrow flange I beams with 14 % tapered inner flange faces. They predate the IPE range and are still produced for replacement work, crane runways and small spans. The number is the nominal depth in millimetres.</p>")
series("EU", "HE", "he-by-mass", "HE sections by mass", "Wide flange columns designated by mass",
       "<p>These HE sections are designated by depth and mass per metre (for example HE 650 x 343) instead of the A/B/M letters. They are the very heavy column sections of the ArcelorMittal range, rolled to ASTM A6/A6M profiles with the dimensions of the HD/HL families.</p>")
series("EU", "HEA", "hea", "HEA sections", "European wide flange beams, light series",
       "<p>HEA (HE A) sections are the light series of the European wide flange beams (Euronorm 53-62, tolerances to EN 10034). The actual depth is slightly less than the nominal size: HEA 200 is 190 mm deep and 200 mm wide. HEA is the usual choice for columns and for beams that need a wide flange, and the parallel flanges simplify connections.</p>"
       "<p>Read the guide <a href=\"/guides/hea-heb-hem/\">HEA vs HEB vs HEM</a> for how the three series compare.</p>")
series("EU", "HEAA", "heaa", "HEAA sections", "European wide flange beams, extra-light series",
       "<p>HEAA (HE AA) sections are the lightest of the European wide flange series: the same width as HEA, HEB and HEM of the same nominal size but thinner flanges and web. They are rolled by ArcelorMittal.</p>")
series("EU", "HEB", "heb", "HEB sections", "European wide flange beams, medium series",
       "<p>HEB (HE B) sections are the medium series of the European wide flange beams (Euronorm 53-62). Up to HEB 300 they are square: the depth equals the width (HEB 200 is 200 x 200 mm). They are the most common column section in continental Europe and a frequent choice for heavy beams.</p>"
       "<p>Read the guide <a href=\"/guides/hea-heb-hem/\">HEA vs HEB vs HEM</a> for how the three series compare.</p>")
series("EU", "HEM", "hem", "HEM sections", "European wide flange beams, heavy series",
       "<p>HEM (HE M) sections are the heavy series of the European wide flange beams (Euronorm 53-62): thick flanges and web, the greatest mass of the three series, used where a compact section must carry large loads, typically columns in multi-storey buildings.</p>")
series("EU", "HL", "hl", "HL sections", "Extra wide flange beams",
       "<p>HL sections are the deep wide flange beams of the ArcelorMittal range (920 to 1100 mm nominal depth), rolled to ASTM A6/A6M profiles and designated by depth and mass per metre.</p>")
series("EU", "HD", "hd", "HD sections", "Wide flange columns",
       "<p>HD sections are the heavy column sections of the ArcelorMittal range: 260 to 400 mm nominal depth with masses up to 1,299 kg/m, used for columns in tall buildings and heavily loaded structures.</p>")
series("EU", "HP", "hp", "HP bearing piles", "Wide flange bearing piles",
       "<p>HP bearing piles are wide flange sections with equal flange and web thickness, rolled for driven piling. Not to be confused with the HP bulb flats (Holland profiles) used in shipbuilding, which are listed under <a href=\"/steel-sections/eu/bulb-flat/\">bulb flats</a>.</p>")
series("EU", "UPE", "upe", "UPE channels", "European channels with parallel flanges",
       "<p>UPE channels (DIN 1026-2) are the European parallel flange channels. The number is the depth in millimetres. Compared with UPN of the same depth they have a wider flange and a parallel inner face, which makes bolting easier.</p>")
series("EU", "UPN", "upn", "UPN channels", "European channels with tapered flanges",
       "<p>UPN channels (DIN 1026-1, formerly U or UNP) have 8 % tapered inner flange faces. The number is the depth in millimetres, from UPN 80 to UPN 400. They are used for purlins, trimmers, bracing and in pairs as built-up columns.</p>")
series("EU", "U", "u", "Small U channels", "Small tapered flange channels",
       "<p>Small U channels (U 40 to U 65) below the UPN range, with tapered flanges, from mill catalogues.</p>")
series("EU", "L", "l", "Angles (EN 10056-1)", "Equal and unequal leg angles",
       "<p>Hot-rolled equal and unequal leg angles to EN 10056-1. The designation gives the two leg lengths and the thickness in millimetres: L 100 x 100 x 10 is an equal angle, L 100 x 65 x 10 an unequal one. Angles are used for bracing, trusses, lintels, cleats and framing.</p>")
series("EU", "T", "t", "T sections (EN 10055)", "Hot-rolled tees with rounded edges",
       "<p>Hot-rolled T sections to EN 10055 with equal width and depth, from T 30 to T 80, with tapered flanges and rounded edges.</p>")
series("EU", "RHS H", "rhs-hot", "RHS hot-finished (EN 10210)", "Rectangular hollow sections, hot-finished",
       "<p>Hot-finished rectangular hollow sections to EN 10210. The designation gives width, depth and wall thickness in millimetres. Hot-finished sections have smaller corner radii and no residual stresses from forming, which gives them a better buckling curve than cold-formed sections in Eurocode 3.</p>", sizes=False)
series("EU", "RHS C", "rhs-cold", "RHS cold-formed (EN 10219)", "Rectangular hollow sections, cold-formed",
       "<p>Cold-formed welded rectangular hollow sections to EN 10219, with larger corner radii (2t to 3t depending on thickness) than hot-finished sections.</p>", sizes=False)
series("EU", "SHS H", "shs-hot", "SHS hot-finished (EN 10210)", "Square hollow sections, hot-finished",
       "<p>Hot-finished square hollow sections to EN 10210, from 40 x 40 to 400 x 400 mm.</p>", sizes=False)
series("EU", "SHS C", "shs-cold", "SHS cold-formed (EN 10219)", "Square hollow sections, cold-formed",
       "<p>Cold-formed welded square hollow sections to EN 10219.</p>", sizes=False)
series("EU", "CHS H", "chs-hot", "CHS hot-finished (EN 10210)", "Circular hollow sections, hot-finished",
       "<p>Hot-finished circular hollow sections to EN 10210, designated by outside diameter and wall thickness.</p>", sizes=False)
series("EU", "CHS C", "chs-cold", "CHS cold-formed (EN 10219)", "Circular hollow sections, cold-formed",
       "<p>Cold-formed welded circular hollow sections to EN 10219, designated by outside diameter and wall thickness.</p>", sizes=False)
series("EU", "Bulb flat (HP)", "bulb-flat", "Bulb flats (Holland profiles, EN 10067)", "Hot-rolled bulb flats for shipbuilding",
       "<p>Bulb flats to EN 10067, also called Holland profiles or HP flats, are the stiffeners of the shipbuilding industry: a flat bar with a bulb on one edge, welded to plating as deck, side and bottom stiffeners. The designation gives the depth and the web thickness in millimetres, from HP 60 x 4 to HP 430 x 20.</p>")

series("UK", "UB", "ub", "Universal beams (UB)", "British I beams for bending",
       "<p>Universal beams to BS 4-1:2005 are the British I beams with parallel flanges, designated by nominal depth, nominal width and mass per metre (203 x 133 x 25 UB). Depth is much greater than width, which makes them efficient in bending.</p>")
series("UK", "UC", "uc", "Universal columns (UC)", "British wide flange columns",
       "<p>Universal columns to BS 4-1:2005 are the British wide flange column sections: depth close to width, thick flanges, designated like UBs by depth, width and mass per metre (203 x 203 x 46 UC).</p>")
series("UK", "UBP", "ubp", "Universal bearing piles (UBP)", "Wide flange bearing piles",
       "<p>Universal bearing piles to BS 4-1:2005 have equal flange and web thickness for driving, in the 203 to 356 mm range.</p>")
series("UK", "J", "j", "Joists (RSJ)", "Rolled steel joists with tapered flanges",
       "<p>Joists to BS 4-1:2005, the traditional rolled steel joists (RSJ) with tapered flanges and small sizes from 76 x 76 to 254 x 203 mm, still rolled for lintels and replacement work.</p>")
series("UK", "PFC", "pfc", "Parallel flange channels (PFC)", "British channels with parallel flanges",
       "<p>Parallel flange channels to BS 4-1:2005, designated by depth, width and mass per metre (230 x 75 x 26 PFC).</p>")
series("UK", "CH", "ch", "Channels (BS 4-1:1993)", "British tapered flange channels",
       "<p>Tapered flange channels to the superseded BS 4-1:1993, listed for existing structures and replacement work.</p>")
series("UK", "L=", "equal-angles", "Equal angles", "Equal leg angles to BS EN 10056-1",
       "<p>Hot-rolled equal leg angles to BS EN 10056-1:1999, from 20 x 20 x 3 to 200 x 200 x 24 mm. The sizes are the EN 10056-1 range: each designation links to its page in the European library.</p>", sizes=False)
series("UK", "L", "unequal-angles", "Unequal angles", "Unequal leg angles to BS EN 10056-1",
       "<p>Hot-rolled unequal leg angles to BS EN 10056-1:1999, from 40 x 25 x 4 to 200 x 150 x 18 mm. The sizes are the EN 10056-1 range: each designation links to its page in the European library.</p>", sizes=False)
series("UK", "T (UB)", "tees-ub", "Tees cut from universal beams", "Structural tees from UB",
       "<p>Structural tees cut from universal beams (BS 4-1:2005), designated by flange width, depth and mass per metre.</p>")
series("UK", "T (UC)", "tees-uc", "Tees cut from universal columns", "Structural tees from UC",
       "<p>Structural tees cut from universal columns (BS 4-1:2005), designated by flange width, depth and mass per metre.</p>")

# Sibling groups: same nominal size across series (for the "Related sections" links).
SIBLINGS = [
    [("EU", "HEAA"), ("EU", "HEA"), ("EU", "HEB"), ("EU", "HEM")],
    [("EU", "IPEAA"), ("EU", "IPEA"), ("EU", "IPE"), ("EU", "IPEO")],
    [("EU", "UPE"), ("EU", "UPN")],
]

# ---------------------------------------------------------------------------
# Naming
# ---------------------------------------------------------------------------

_HE_RE = re.compile(r"^HE(\d+)(AA|A|B|M)$")
_HL_LETTER_RE = re.compile(r"^HL(\d+)(AA|A|B|M|R)_*$")
_PREFIX_RE = re.compile(r"^([A-Za-z]+)\s*(.*)$")


def display_name(sec):
    """Common designation, e.g. HE200B -> 'HEA 200', UB838x292x226 -> 'UB 838 x 292 x 226'."""
    n = sec["name"]
    m = _HE_RE.match(n)
    if m:
        return f"HE{m.group(2)} {m.group(1)}"
    m = _HL_LETTER_RE.match(n)
    if m:
        return f"HL {m.group(1)} {m.group(2)}"
    m = _PREFIX_RE.match(n)
    prefix, rest = m.group(1), m.group(2)
    rest = rest.replace(",", ".").replace("X", "x").replace("x", " x ").replace("_", "").strip()
    if prefix in ("IPEA", "IPEAA", "IPEO"):
        prefix = "IPE " + prefix[3:]
    return f"{prefix} {rest}".strip()


def alt_name(sec):
    """Alternative designation shown under the title, or None."""
    n = sec["name"]
    m = _HE_RE.match(n)
    if m:
        return f"HE {m.group(1)} {m.group(2)}"
    if sec["library"] == "UK" and sec["type"] in ("UB", "UC", "UBP", "PFC"):
        rest = n[len(sec["type"]):].replace("x", " x ")
        return f"{rest} {sec['type']}"
    if sec["entity"] == "SteelSection_BF_EU":
        return f"Holland profile {n[2:].replace('x', ' x ')}"
    return None


def size_slug(sec):
    n = sec["name"].lower().replace(",", ".").replace("_", "")
    m = _HE_RE.match(sec["name"])
    if m:
        return f"he{m.group(2).lower()}-{m.group(1)}"
    m = _HL_LETTER_RE.match(sec["name"])
    if m:
        return f"hl-{m.group(1)}-{m.group(2).lower()}"
    m = _PREFIX_RE.match(n)
    return f"{m.group(1)}-{m.group(2).strip()}".replace(" ", "")


def size_key(sec):
    """Nominal size shared by sibling series (HE200A/HE200B -> '200', IPE300/IPEA300 -> '300')."""
    m = re.search(r"(\d+)", sec["name"])
    return m.group(1) if m else sec["name"]


def standard_name(s):
    s = (s or "").strip()
    return STANDARDS.get(s, s)


# ---------------------------------------------------------------------------
# Formatting
# ---------------------------------------------------------------------------

def fmt(v):
    if v is None:
        return "–"
    if isinstance(v, str):
        return v
    if abs(v) >= 1000:
        return f"{v:,.0f}"
    if v == 0:
        return "0"
    digits = 4 - int(math.floor(math.log10(abs(v)))) - 1
    s = f"{round(v, max(digits, 0)):.{max(digits, 0)}f}"
    if "." in s:
        s = s.rstrip("0").rstrip(".")
    return s


def esc(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;"))


# ---------------------------------------------------------------------------
# SVG drawings
# ---------------------------------------------------------------------------

def _arc(r, x, y, sweep=0):
    return f"A {r:.2f} {r:.2f} 0 0 {sweep} {x:.2f} {y:.2f}"


def path_i_section(h, b, tw, tf, r1, taper=0.0):
    """Outline of an I/H section centred on the origin, y up. taper = flange slope (0.14 for IPN)."""
    r1 = min(r1 or 0, tw, tf)
    half_b, half_h, half_tw = b / 2, h / 2, tw / 2
    if taper:
        # Thickness tf is measured at b/4 from the edge; inner face slopes 'taper' towards the web.
        quarter = (half_b - half_tw) / 2
        t_edge = tf - taper * quarter
        t_root = tf + taper * quarter
    else:
        t_edge = t_root = tf
    p = [f"M {half_b:.2f} {half_h:.2f}", f"L {-half_b:.2f} {half_h:.2f}", f"L {-half_b:.2f} {half_h - t_edge:.2f}"]
    # upper left flange inner face to web with fillet
    p.append(f"L {-half_tw - r1:.2f} {half_h - t_root:.2f}")
    p.append(_arc(r1, -half_tw, half_h - t_root - r1, 0))
    p.append(f"L {-half_tw:.2f} {-half_h + t_root + r1:.2f}")
    p.append(_arc(r1, -half_tw - r1, -half_h + t_root, 0))
    p.append(f"L {-half_b:.2f} {-half_h + t_edge:.2f}")
    p.append(f"L {-half_b:.2f} {-half_h:.2f}")
    p.append(f"L {half_b:.2f} {-half_h:.2f}")
    p.append(f"L {half_b:.2f} {-half_h + t_edge:.2f}")
    p.append(f"L {half_tw + r1:.2f} {-half_h + t_root:.2f}")
    p.append(_arc(r1, half_tw, -half_h + t_root + r1, 0))
    p.append(f"L {half_tw:.2f} {half_h - t_root - r1:.2f}")
    p.append(_arc(r1, half_tw + r1, half_h - t_root, 0))
    p.append(f"L {half_b:.2f} {half_h - t_edge:.2f}")
    p.append("Z")
    return " ".join(p)


def path_channel(h, b, tw, tf, r1, taper=0.0):
    """Channel with the web on the left (x = 0 at the back of the web), y up, centred vertically."""
    r1 = min(r1 or 0, tw, tf)
    half_h = h / 2
    if taper:
        quarter = (b - tw) / 2
        t_edge = tf - taper * quarter
        t_root = tf + taper * quarter
    else:
        t_edge = t_root = tf
    p = [f"M 0 {half_h:.2f}", f"L {b:.2f} {half_h:.2f}", f"L {b:.2f} {half_h - t_edge:.2f}",
         f"L {tw + r1:.2f} {half_h - t_root:.2f}", _arc(r1, tw, half_h - t_root - r1, 1),
         f"L {tw:.2f} {-half_h + t_root + r1:.2f}", _arc(r1, tw + r1, -half_h + t_root, 1),
         f"L {b:.2f} {-half_h + t_edge:.2f}", f"L {b:.2f} {-half_h:.2f}", f"L 0 {-half_h:.2f}", "Z"]
    return " ".join(p)


def path_angle(h, b, t, r1, r2):
    """Angle with the heel at the origin, legs along +x (b) and +y (h)."""
    r1 = min(r1 or 0, t)
    r2 = min(r2 or 0, t / 2)
    p = [f"M 0 0", f"L {b:.2f} 0", f"L {b:.2f} {t - r2:.2f}", _arc(r2, b - r2, t, 1),
         f"L {t + r1:.2f} {t:.2f}", _arc(r1, t, t + r1, 0), f"L {t:.2f} {h - r2:.2f}", _arc(r2, t - r2, h, 1),
         f"L 0 {h:.2f}", "Z"]
    return " ".join(p)


def path_tee(h, b, tw, tf, r1, taper=0.0):
    """Tee with the flange at the top, stem down, centred horizontally, y up with flange top at +h/2."""
    r1 = min(r1 or 0, tw, tf)
    half_b, half_h, half_tw = b / 2, h / 2, tw / 2
    if taper:
        quarter = (half_b - half_tw) / 2
        t_edge = tf - taper * quarter
        t_root = tf + taper * quarter
    else:
        t_edge = t_root = tf
    p = [f"M {-half_b:.2f} {half_h:.2f}", f"L {half_b:.2f} {half_h:.2f}", f"L {half_b:.2f} {half_h - t_edge:.2f}",
         f"L {half_tw + r1:.2f} {half_h - t_root:.2f}", _arc(r1, half_tw, half_h - t_root - r1, 1),
         f"L {half_tw:.2f} {-half_h:.2f}", f"L {-half_tw:.2f} {-half_h:.2f}",
         f"L {-half_tw:.2f} {half_h - t_root - r1:.2f}", _arc(r1, -half_tw - r1, half_h - t_root, 1),
         f"L {-half_b:.2f} {half_h - t_edge:.2f}", "Z"]
    return " ".join(p)


def path_rhs(h, b, t, r1, r2):
    ro = max(r1 or 1.5 * t, t)
    ri = max(r2 or (ro - t), 0.01)
    half_b, half_h = b / 2, h / 2

    def rect(w2, h2, r, cw):
        s = 1 if cw else 0
        if cw:
            return " ".join([f"M {-w2 + r:.2f} {h2:.2f}", f"L {w2 - r:.2f} {h2:.2f}", _arc(r, w2, h2 - r, 1),
                             f"L {w2:.2f} {-h2 + r:.2f}", _arc(r, w2 - r, -h2, 1), f"L {-w2 + r:.2f} {-h2:.2f}",
                             _arc(r, -w2, -h2 + r, 1), f"L {-w2:.2f} {h2 - r:.2f}", _arc(r, -w2 + r, h2, 1), "Z"])
        return " ".join([f"M {-w2 + r:.2f} {h2:.2f}", _arc(r, -w2, h2 - r, 0), f"L {-w2:.2f} {-h2 + r:.2f}",
                         _arc(r, -w2 + r, -h2, 0), f"L {w2 - r:.2f} {-h2:.2f}", _arc(r, w2, -h2 + r, 0),
                         f"L {w2:.2f} {h2 - r:.2f}", _arc(r, w2 - r, h2, 0), "Z"])
    return rect(half_b, half_h, ro, True) + " " + rect(half_b - t, half_h - t, ri, False)


def path_chs(d, t):
    ro, ri = d / 2, d / 2 - t
    return (f"M {ro:.2f} 0 A {ro:.2f} {ro:.2f} 0 1 1 {-ro:.2f} 0 A {ro:.2f} {ro:.2f} 0 1 1 {ro:.2f} 0 Z "
            f"M {ri:.2f} 0 A {ri:.2f} {ri:.2f} 0 1 0 {-ri:.2f} 0 A {ri:.2f} {ri:.2f} 0 1 0 {ri:.2f} 0 Z")


def path_bulb_flat(h, t, c, r):
    """Bulb flat: flat face at x = 0, toe at y = 0, bulb at the top on the +x side (EN 10067 geometry)."""
    tan30, cos30, sin30 = math.tan(math.radians(30)), math.cos(math.radians(30)), math.sin(math.radians(30))
    cx, cy = t + c - r, h - r
    px, py = cx + r * sin30, cy - r * cos30            # flank tangent point on the bulb arc
    wy = py - (px - t) * tan30                           # flank meets the web face
    p = [f"M 0 0", f"L {t:.2f} 0", f"L {t:.2f} {wy:.2f}", f"L {px:.2f} {py:.2f}",
         f"A {r:.2f} {r:.2f} 0 0 0 {cx:.2f} {h:.2f}", f"L 0 {h:.2f}", "Z"]
    return " ".join(p)


def dim_line(x1, y1, x2, y2, label, offset=0.0, vertical=False, scale=1.0):
    """A dimension line with ticks and a label (coordinates in section mm, y up)."""
    s = scale
    if vertical:
        x = x1 + offset
        return (f'<line class="dim" x1="{x*s:.1f}" y1="{-y1*s:.1f}" x2="{x*s:.1f}" y2="{-y2*s:.1f}"/>'
                f'<line class="dim" x1="{(x-3/s)*s:.1f}" y1="{-y1*s:.1f}" x2="{(x+3/s)*s:.1f}" y2="{-y1*s:.1f}"/>'
                f'<line class="dim" x1="{(x-3/s)*s:.1f}" y1="{-y2*s:.1f}" x2="{(x+3/s)*s:.1f}" y2="{-y2*s:.1f}"/>'
                f'<text class="dimlabel" x="{x*s + 6:.1f}" y="{-(y1+y2)/2*s + 4:.1f}">{label}</text>')
    y = y1 + offset
    return (f'<line class="dim" x1="{x1*s:.1f}" y1="{-y*s:.1f}" x2="{x2*s:.1f}" y2="{-y*s:.1f}"/>'
            f'<line class="dim" x1="{x1*s:.1f}" y1="{-(y-3/s)*s:.1f}" x2="{x1*s:.1f}" y2="{-(y+3/s)*s:.1f}"/>'
            f'<line class="dim" x1="{x2*s:.1f}" y1="{-(y-3/s)*s:.1f}" x2="{x2*s:.1f}" y2="{-(y+3/s)*s:.1f}"/>'
            f'<text class="dimlabel" text-anchor="middle" x="{(x1+x2)/2*s:.1f}" y="{-y*s + 14:.1f}">{label}</text>')


def label(x, y, text, scale, anchor="start"):
    return f'<text class="dimlabel" text-anchor="{anchor}" x="{x*scale:.1f}" y="{-y*scale:.1f}">{text}</text>'


def svg_for(sec):
    """Return (svg_html, caption) or (None, None)."""
    e = sec["entity"]
    g = lambda k: sec.get(k)
    W = 300.0  # drawing box in px
    parts, extents = [], None
    try:
        if e in ("SteelSection_H_EU", "SteelSection_IPN_EU"):
            h, b, tw, tf, r1 = g("h"), g("b"), g("tw"), g("tf"), g("r1") or 0
            taper = 0.14 if e == "SteelSection_IPN_EU" else 0.0
            d = path_i_section(h, b, tw, tf, r1, taper)
            size = max(h, b)
            s = W / (size * 1.45)
            parts.append(f'<path class="steel" d="{d}" transform="scale({s:.4f},{-s:.4f})"/>')
            parts.append(dim_line(b / 2, -h / 2, b / 2, h / 2, "h", offset=12 / s, vertical=True, scale=s))
            parts.append(dim_line(-b / 2, -h / 2, b / 2, -h / 2, "b", offset=-12 / s, scale=s))
            parts.append(label(-b / 2 - 6 / s, h / 2 - tf / 2 - 4 / s, "t<tspan baseline-shift=\"sub\" font-size=\"70%\">f</tspan>", s, "end"))
            parts.append(label(tw / 2 + 6 / s, 0, "t<tspan baseline-shift=\"sub\" font-size=\"70%\">w</tspan>", s))
            extents = (-b / 2 - 40 / s, -h / 2 - 34 / s, b / 2 + 56 / s, h / 2 + 8 / s)
        elif e in ("SteelSection_UPE_EU", "SteelSection_UPN_EU", "SteelSection_U_EU", "SteelSection_CH_UK"):
            h, b, tw, tf, r1 = g("h"), g("b"), g("tw"), g("tf"), g("r1") or 0
            taper = 0.0 if e == "SteelSection_UPE_EU" else 0.08
            d = path_channel(h, b, tw, tf, r1, taper)
            s = W / (max(h, b * 2) * 1.45)
            parts.append(f'<path class="steel" d="{d}" transform="scale({s:.4f},{-s:.4f})"/>')
            parts.append(dim_line(b, -h / 2, b, h / 2, "h", offset=12 / s, vertical=True, scale=s))
            parts.append(dim_line(0, -h / 2, b, -h / 2, "b", offset=-12 / s, scale=s))
            parts.append(label(b * 0.55, h / 2 + 6 / s, "t<tspan baseline-shift=\"sub\" font-size=\"70%\">f</tspan>", s, "middle"))
            parts.append(label(tw + 6 / s, 0, "t<tspan baseline-shift=\"sub\" font-size=\"70%\">w</tspan>", s))
            extents = (-8 / s, -h / 2 - 34 / s, b + 56 / s, h / 2 + 24 / s)
        elif e == "SteelSection_L_EU":
            h, b, t, r1, r2 = g("h"), g("b"), g("t"), g("r1") or 0, g("r2") or 0
            d = path_angle(h, b, t, r1, r2)
            s = W / (max(h, b) * 1.45)
            parts.append(f'<path class="steel" d="{d}" transform="scale({s:.4f},{-s:.4f})"/>')
            parts.append(dim_line(b, 0, b, h, "h", offset=12 / s, vertical=True, scale=s))
            parts.append(dim_line(0, 0, b, 0, "b", offset=-12 / s, scale=s))
            parts.append(label(t + 6 / s, h * 0.6, "t", s))
            extents = (-8 / s, -34 / s, b + 56 / s, h + 8 / s)
        elif e in ("SteelSection_T_EU", "SteelSection_T_UK"):
            h, b = g("h"), g("b")
            if e == "SteelSection_T_EU":
                tw = tf = g("t"); r1 = g("r") or 0; taper = 0.02
            else:
                tw, tf, r1, taper = g("tw"), g("tf"), g("r1") or 0, 0.0
            d = path_tee(h, b, tw, tf, r1, taper)
            s = W / (max(h, b) * 1.45)
            parts.append(f'<path class="steel" d="{d}" transform="scale({s:.4f},{-s:.4f})"/>')
            parts.append(dim_line(b / 2, -h / 2, b / 2, h / 2, "h", offset=12 / s, vertical=True, scale=s))
            parts.append(dim_line(-b / 2, h / 2, b / 2, h / 2, "b", offset=6 / s, scale=s))
            parts.append(label(tw / 2 + 6 / s, -h * 0.2, "t<tspan baseline-shift=\"sub\" font-size=\"70%\">w</tspan>" if e == "SteelSection_T_UK" else "t", s))
            extents = (-b / 2 - 8 / s, -h / 2 - 8 / s, b / 2 + 56 / s, h / 2 + 30 / s)
        elif e == "SteelSection_RHS_EU":
            h, b, t = g("h"), g("b"), g("t")
            d = path_rhs(h, b, t, g("r1"), g("r2"))
            s = W / (max(h, b) * 1.45)
            parts.append(f'<path class="steel" fill-rule="evenodd" d="{d}" transform="scale({s:.4f},{-s:.4f})"/>')
            parts.append(dim_line(b / 2, -h / 2, b / 2, h / 2, "h", offset=12 / s, vertical=True, scale=s))
            parts.append(dim_line(-b / 2, -h / 2, b / 2, -h / 2, "b", offset=-12 / s, scale=s))
            parts.append(label(b / 2 - t - 6 / s, 0, "t", s, "end"))
            extents = (-b / 2 - 8 / s, -h / 2 - 34 / s, b / 2 + 56 / s, h / 2 + 8 / s)
        elif e == "SteelSection_CHS_EU":
            dd, t = g("outsideDiameter"), g("t")
            d = path_chs(dd, t)
            s = W / (dd * 1.45)
            parts.append(f'<path class="steel" fill-rule="evenodd" d="{d}" transform="scale({s:.4f},{-s:.4f})"/>')
            parts.append(dim_line(-dd / 2, -dd / 2, dd / 2, -dd / 2, "D", offset=-12 / s, scale=s))
            parts.append(label(dd / 2 - t - 6 / s, 0, "t", s, "end"))
            extents = (-dd / 2 - 8 / s, -dd / 2 - 34 / s, dd / 2 + 8 / s, dd / 2 + 8 / s)
        elif e == "SteelSection_BF_EU":
            h, t, c, r = g("h"), g("t"), g("bulbC"), g("bulbR")
            d = path_bulb_flat(h, t, c, r)
            s = W / (h * 1.45)
            parts.append(f'<path class="steel" d="{d}" transform="scale({s:.4f},{-s:.4f})"/>')
            parts.append(dim_line(t + c, 0, t + c, h, "h", offset=12 / s, vertical=True, scale=s))
            parts.append(dim_line(0, 0, t, 0, "t", offset=-12 / s, scale=s))
            parts.append(dim_line(t, h, t + c, h, "c", offset=6 / s, scale=s))
            extents = (-8 / s, -34 / s, t + c + 56 / s, h + 30 / s)
        else:
            return None, None
    except (TypeError, ValueError):
        return None, None
    x0, y0, x1, y1 = extents
    vb = f"{x0*s:.1f} {-y1*s:.1f} {(x1-x0)*s:.1f} {(y1-y0)*s:.1f}"
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{vb}" role="img" '
           f'aria-label="Cross-section drawing of {esc(display_name(sec))}">' + "".join(parts) + "</svg>")
    return svg, "Cross-section to scale"


# ---------------------------------------------------------------------------
# HTML
# ---------------------------------------------------------------------------

def page(title, description, canonical, body, extra_head=""):
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{esc(title)} — theolternative</title>
  <meta name="description" content="{esc(description)}">
  <link rel="canonical" href="{SITE}{canonical}">
  <link rel="apple-touch-icon" sizes="180x180" href="/images/apple-touch-icon.png">
  <link rel="icon" type="image/png" sizes="32x32" href="/images/favicon-32x32.png">
  <link rel="icon" type="image/png" sizes="16x16" href="/images/favicon-16x16.png">
  <link rel="manifest" href="/site.webmanifest">
  <meta name="theme-color" content="#1a1a1e">
  <meta property="og:type" content="website">
  <meta property="og:url" content="{SITE}{canonical}">
  <meta property="og:title" content="{esc(title)} — theolternative">
  <meta property="og:description" content="{esc(description)}">
  <meta property="og:image" content="{SITE}{ICON}">
  <meta name="twitter:card" content="summary">
  <meta name="twitter:title" content="{esc(title)} — theolternative">
  <meta name="twitter:description" content="{esc(description)}">
  <meta name="twitter:image" content="{SITE}{ICON}">
  <link rel="stylesheet" href="/css/style.css">
  <script src="/js/components.js" defer></script>
{extra_head}</head>
<body data-theme="steel-dark">
  <site-header></site-header>

  <main>
    <div class="container">
{body}
    </div>
  </main>

  <site-footer></site-footer>
</body>
</html>
"""


def breadcrumbs(items):
    """items: list of (name, url) with the last one current (url may be None)."""
    html = ['<nav class="crumbs" aria-label="Breadcrumb">']
    ld = []
    for i, (name, url) in enumerate(items):
        if i:
            html.append(' <span aria-hidden="true">›</span> ')
        if url and i < len(items) - 1:
            html.append(f'<a href="{url}">{esc(name)}</a>')
        else:
            html.append(f'<span aria-current="page">{esc(name)}</span>')
        ld.append({"@type": "ListItem", "position": i + 1, "name": name, "item": SITE + (url or items[-1][1] or "/")})
    html.append("</nav>")
    script = ('  <script type="application/ld+json">\n' +
              json.dumps({"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": ld}, ensure_ascii=False) +
              "\n  </script>\n")
    return "".join(html), script


def cta_block(sec_name=None, lib="EU"):
    what = f"{esc(sec_name)} with " if sec_name else "every section with "
    libname = "British" if lib == "UK" else "European"
    return f"""
      <div class="product-section">
        <div class="product-card cta-card">
          <h2>Full properties in Steel Profiles</h2>
          <p>The free app shows {what}its dimensions and drawing on iPhone, iPad and Mac. The {libname} library unlocks the complete structural properties, the design checks to Eurocode 3, the Equivalent Finder across standards and the comparison of up to three sections. Favorites, weight lists and saved sections sync through iCloud.</p>
          <div class="cta-actions">
            <a href="{STORE_URL}" target="_blank" rel="noopener">
              <img class="app-store-badge" src="https://tools.applemediaservices.com/api/badges/download-on-the-app-store/white/en-us?size=250x83" alt="Download on the App Store">
            </a>
            <a href="/apps/steel-profiles-free/" class="btn-learn-more">About Steel Profiles</a>
            <a href="/apps/steel-profiles-pro/" class="btn-learn-more">Steel Profiles Pro for teams</a>
          </div>
        </div>
      </div>
"""


def write(path, html):
    full = os.path.join(ROOT, path.lstrip("/"), "index.html")
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(html)


# ---------------------------------------------------------------------------
# Pages
# ---------------------------------------------------------------------------

def table_html(secs, keys, link=True, series_url=None):
    head = "".join(f'<th scope="col">{PROPS[k][0]}<span class="unit"> {PROPS[k][1]}</span></th>' for k in keys)
    rows = []
    for s in secs:
        name = esc(display_name(s))
        if link and s.get("_url"):
            name = f'<a href="{s["_url"]}">{name}</a>'
        cells = "".join(f"<td>{fmt(s.get(k))}</td>" for k in keys)
        rows.append(f'<tr><th scope="row">{name}</th>{cells}</tr>')
    return (f'<div class="table-scroll"><table class="spec-table"><thead><tr><th scope="col">Designation</th>{head}</tr></thead>'
            f'<tbody>{"".join(rows)}</tbody></table></div>')


def series_page(lib, typ, info, secs, urls):
    libinfo = LIBRARIES[lib]
    url = f"/steel-sections/{libinfo['slug']}/{info['slug']}/"
    keys = TABLE_KEYS[secs[0]["entity"]]
    stds = sorted({standard_name(s.get("standard")) for s in secs if s.get("standard")})
    first, last = display_name(secs[0]), display_name(secs[-1])
    crumbs, ld = breadcrumbs([("Steel sections", "/steel-sections/"), (libinfo["short"], f"/steel-sections/{libinfo['slug']}/"), (info["title"], url)])
    desc = f"{info['title']}: dimensions, mass per metre and area of all {len(secs)} sizes from {first} to {last}, with cross-section drawings. {info['kind']}."
    body = f"""
      {crumbs}
      <div class="product-hero article-hero">
        <div class="product-meta">
          <h1>{esc(info['title'])}</h1>
          <p class="subtitle">{esc(info['kind'])} · {len(secs)} sizes · {esc(', '.join(stds))}</p>
        </div>
      </div>

      <div class="product-section article">
        {info['desc']}
        <p>The table lists the dimensions, mass and area of every size.{' Tap a designation for its drawing and detailed dimensions.' if any(s.get('_url') for s in secs) else ''} All values are in millimetres, kilograms per metre and square centimetres.</p>
      </div>

      <div class="product-section">
        <h2>Dimensions and weights</h2>
        {table_html(secs, keys, link=True)}
      </div>
{cta_block(None, lib)}
      <div class="product-section">
        <h2>Other {esc(libinfo['short'])} series</h2>
        <div class="series-links">{''.join(f'<a href="{u}">{esc(t)}</a>' for t, u in urls if u != url)}</div>
      </div>
"""
    write(url, page(info["title"], desc, url, body, ld))
    return url


def size_page(lib, typ, info, sec, prev_sec, next_sec, siblings, all_secs_url):
    libinfo = LIBRARIES[lib]
    url = sec["_url"]
    name = display_name(sec)
    alt = alt_name(sec)
    keys = [k for k in DIM_KEYS[sec["entity"]] if sec.get(k) is not None]
    std = standard_name(sec.get("standard"))
    crumbs, ld = breadcrumbs([("Steel sections", "/steel-sections/"), (libinfo["short"], f"/steel-sections/{libinfo['slug']}/"),
                              (info["title"], all_secs_url), (name, url)])
    svg, caption = svg_for(sec)
    rows = "".join(
        f'<tr><th scope="row">{PROPS[k][0]}</th><td>{fmt(sec.get(k))}<span class="unit"> {PROPS[k][1]}</span></td><td class="desc">{esc(PROPS[k][2])}</td></tr>'
        for k in keys)
    summary_bits = []
    if sec.get("h") is not None and sec.get("b") is not None:
        summary_bits.append(f"{fmt(sec['h'])} mm deep and {fmt(sec['b'])} mm wide")
    elif sec.get("outsideDiameter") is not None:
        summary_bits.append(f"{fmt(sec['outsideDiameter'])} mm outside diameter")
    elif sec.get("h") is not None:
        summary_bits.append(f"{fmt(sec['h'])} mm deep")
    if sec.get("tw") is not None and sec.get("tf") is not None:
        summary_bits.append(f"web {fmt(sec['tw'])} mm, flanges {fmt(sec['tf'])} mm")
    elif sec.get("t") is not None:
        summary_bits.append(f"{fmt(sec['t'])} mm thick")
    summary_bits.append(f"{fmt(sec.get('weight'))} kg/m")
    if sec.get("area") is not None:
        summary_bits.append(f"area {fmt(sec['area'])} cm²")
    summary = ", ".join(summary_bits)
    desc = f"{name}{' (' + alt + ')' if alt else ''} dimensions: {summary}. {info['kind']}, {std}. Drawing and full properties in the Steel Profiles app."
    pager = ""
    if prev_sec or next_sec:
        pager = '<nav class="pager" aria-label="Neighbouring sizes">'
        pager += f'<a href="{prev_sec["_url"]}">‹ {esc(display_name(prev_sec))}</a>' if prev_sec else "<span></span>"
        pager += f'<a href="{next_sec["_url"]}">{esc(display_name(next_sec))} ›</a>' if next_sec else "<span></span>"
        pager += "</nav>"
    sib_html = ""
    if siblings:
        sib_html = ('<div class="product-section"><h2>Same size in other series</h2><div class="series-links">' +
                    "".join(f'<a href="{s["_url"]}">{esc(display_name(s))}</a>' for s in siblings) + "</div></div>")
    figure = ""
    if svg:
        figure = f'<figure class="section-figure">{svg}<figcaption>{caption}</figcaption></figure>'
    app_props = "".join(f"<li>{p}</li>" for p in APP_PROPS.get(sec["entity"], []))
    body = f"""
      {crumbs}
      <div class="product-hero article-hero">
        <div class="product-meta">
          <h1>{esc(name)}</h1>
          <p class="subtitle">{esc(alt + ' · ' if alt else '')}{esc(info['kind'])} · {esc(std)}</p>
        </div>
      </div>

      <div class="product-section">
        <p>{esc(name)} is one of the {esc(info['title'])} of the {esc(libinfo['short'])} library ({esc(info['kind'].lower())}): {esc(summary)}.</p>
        <div class="section-layout">
          {figure}
          <div class="table-scroll">
            <table class="spec-table dims"><thead><tr><th scope="col">Dimension</th><th scope="col">Value</th><th scope="col">Description</th></tr></thead><tbody>{rows}</tbody></table>
          </div>
        </div>
        {pager}
      </div>

      <div class="product-section">
        <h2>Section properties</h2>
        <p>The structural properties of {esc(name)} are available in the Steel Profiles app with the {esc(libinfo['short'])} library:</p>
        <ul>{app_props}</ul>
        <p>The app also runs design checks to EN 1993-1-1 on {esc(name)}, finds the closest sections in the {'AISC, European, Canadian' if lib == 'UK' else 'AISC, British, Canadian'} and Australian standards and compares it side by side with any other section.</p>
      </div>
{cta_block(name, lib)}
      {sib_html}
      <div class="product-section">
        <p><a href="{all_secs_url}">All {esc(info['title'])}</a> · <a href="/steel-sections/{libinfo['slug']}/">{esc(libinfo['name'])}</a> · <a href="/steel-sections/">All steel sections</a></p>
      </div>
"""
    write(url, page(f"{name} dimensions", desc, url, body, ld))


def library_page(lib, libinfo, series_list):
    url = f"/steel-sections/{libinfo['slug']}/"
    crumbs, ld = breadcrumbs([("Steel sections", "/steel-sections/"), (libinfo["short"], url)])
    cards = "".join(
        f'<a class="series-card" href="{u}"><strong>{esc(t)}</strong><span>{esc(k)}</span><span class="count">{n} sizes</span></a>'
        for t, u, k, n in series_list)
    hollow_note = ""
    if lib == "UK":
        hollow_note = ("<p>Hot-finished and cold-formed hollow sections (RHS, SHS, CHS) used in the UK are the EN 10210 and EN 10219 ranges: "
                       "see the <a href=\"/steel-sections/eu/\">European sections</a>.</p>")
    total = sum(n for _, _, _, n in series_list)
    desc = f"{libinfo['name']}: dimensions and weights of {total} hot-rolled sections. {libinfo['intro']}"
    body = f"""
      {crumbs}
      <div class="product-hero article-hero">
        <div class="product-meta">
          <h1>{esc(libinfo['name'])}</h1>
          <p class="subtitle">{total} sections · dimensions, mass and area</p>
        </div>
      </div>
      <div class="product-section article">
        <p>{esc(libinfo['intro'])}</p>
        {hollow_note}
      </div>
      <div class="product-section">
        <div class="series-grid">{cards}</div>
      </div>
{cta_block(None, lib)}
"""
    write(url, page(libinfo["name"], desc, url, body, ld))


def index_page(libs):
    url = "/steel-sections/"
    crumbs, ld = breadcrumbs([("Steel sections", url)])
    cards = "".join(
        f'<a class="series-card" href="/steel-sections/{LIBRARIES[l]["slug"]}/"><strong>{esc(LIBRARIES[l]["name"])}</strong><span>{esc(LIBRARIES[l]["intro"])}</span><span class="count">{n} sections</span></a>'
        for l, n in libs)
    body = f"""
      {crumbs}
      <div class="product-hero article-hero">
        <div class="product-meta">
          <h1>Steel sections</h1>
          <p class="subtitle">Dimensions, weights and drawings of European and British steel profiles</p>
        </div>
      </div>
      <div class="product-section article">
        <p>A free reference of the hot-rolled and hollow steel sections in the <a href="/apps/steel-profiles-free/">Steel Profiles</a> catalog: every size with its dimensions, mass per metre and cross-sectional area, and a scale drawing for each hot-rolled section. The data is the same the app ships with.</p>
        <p>The app adds the structural properties (moments of inertia, section moduli, radii of gyration, torsional and warping constants, Eurocode 3 classes), the American AISC 14 and 16, Canadian CISC and Australian AS/NZS libraries, design checks to Eurocode 3 and AISC 360, and tools to find equivalent sections across standards.</p>
      </div>
      <div class="product-section">
        <div class="series-grid">{cards}</div>
      </div>
      <div class="product-section">
        <h2>Guides</h2>
        <div class="series-links">
          <a href="/guides/hea-heb-hem/">HEA vs HEB vs HEM</a>
          <a href="/guides/w-shape-designation/">How AISC W shapes are designated</a>
          <a href="/guides/ec3-bolt-resistances/">Bolt resistances to Eurocode 3</a>
          <a href="/guides/steel-grade-equivalents/">Steel grade equivalents</a>
        </div>
      </div>
{cta_block(None)}
"""
    write(url, page("Steel sections", "Dimensions, weights and cross-section drawings of European (IPE, HEA, HEB, HEM, UPN, angles, hollow sections, bulb flats) and British (UB, UC, PFC) steel sections.", url, body, ld))


def guide_hea_heb_hem(by_name):
    url = "/guides/hea-heb-hem/"
    crumbs, ld = breadcrumbs([("Guides", "/steel-sections/"), ("HEA vs HEB vs HEM", url)])

    def row(size):
        cells = []
        for typ, letter in (("HEAA", "AA"), ("HEA", "A"), ("HEB", "B"), ("HEM", "M")):
            s = by_name.get(f"HE{size}{letter}")
            if s:
                cells.append(f'<td><a href="{s["_url"]}">{fmt(s["h"])} × {fmt(s["b"])}</a><br><span class="unit">t<sub>w</sub> {fmt(s["tw"])}, t<sub>f</sub> {fmt(s["tf"])}, {fmt(s["weight"])} kg/m</span></td>')
            else:
                cells.append("<td>–</td>")
        return f'<tr><th scope="row">{size}</th>{"".join(cells)}</tr>'

    rows = "".join(row(s) for s in (100, 140, 200, 240, 300, 400, 500, 600, 800, 1000))
    body = f"""
      {crumbs}
      <div class="product-hero article-hero">
        <div class="product-meta">
          <h1>HEA vs HEB vs HEM</h1>
          <p class="subtitle">What the letters mean in the European wide flange series, and how to choose</p>
        </div>
      </div>
      <div class="product-section article">
        <p>The European wide flange beams of Euronorm 53-62 come in three series that share the same nominal sizes and, up to 300 mm, the same width: <strong>HEA</strong> (light), <strong>HEB</strong> (medium) and <strong>HEM</strong> (heavy). ArcelorMittal adds an extra-light <strong>HEAA</strong> series. The number in the designation is the nominal size; the actual depth differs between series because the flange thickness changes while the inner depth stays about the same.</p>

        <h2>The three series at a glance</h2>
        <ul class="plain">
          <li><strong>HEA (HE A)</strong>: thin flanges, the depth is a little less than the nominal size (HEA 200 is 190 mm deep). The lightest standard series, favoured where the member is governed by bending or where mass matters.</li>
          <li><strong>HEB (HE B)</strong>: the reference series. Up to HEB 300 the section is square, depth equals width (HEB 200 is 200 × 200 mm). The most common column section in continental Europe.</li>
          <li><strong>HEM (HE M)</strong>: thick flanges and web, depth greater than the nominal size (HEM 200 is 220 mm deep and 206 mm wide). For heavily loaded columns and short, stocky members.</li>
          <li><strong>HEAA (HE AA)</strong>: lighter than HEA, same width, for members governed by stiffness or for secondary structures.</li>
        </ul>

        <h2>Dimensions compared</h2>
        <p>Depth × width in millimetres, with web and flange thickness and mass per metre.</p>
        <div class="table-scroll">
          <table class="spec-table"><thead><tr><th scope="col">Size</th><th scope="col">HEAA</th><th scope="col">HEA</th><th scope="col">HEB</th><th scope="col">HEM</th></tr></thead><tbody>{rows}</tbody></table>
        </div>

        <h2>How to choose</h2>
        <ul class="plain">
          <li><strong>Columns</strong>: HEB is the usual starting point. Switch to HEM when the load is high and the size must stay small, or to HEA when the column is lightly loaded and bracing keeps the buckling length short.</li>
          <li><strong>Beams</strong>: an IPE of greater depth is normally lighter than an HEA for the same bending resistance. HEA and HEB are chosen for beams when the depth is limited, when the flange must be wide for a bearing or a connection, or when lateral-torsional buckling governs.</li>
          <li><strong>Connections</strong>: all three series have parallel flanges. The maximum bolt size and the flange gauge are the same within a nominal size, so a connection detailed for an HEB usually fits the HEA and HEM of that size.</li>
          <li><strong>Availability</strong>: HEA and HEB are stocked by most European merchants in S235, S275 and S355. HEM and HEAA are less common and often need mill delivery.</li>
        </ul>

        <h2>Naming</h2>
        <p>Both notations are in use and mean the same section: HEA 200 is HE 200 A, HEB 300 is HE 300 B. The old German names IPB (HEB), IPBl (HEA) and IPBv (HEM) still appear in drawings. In the <a href="/apps/steel-profiles-free/">Steel Profiles</a> app, searching for "HEA" lists every HEA size and "HEA 200", "HEA200" and "HE 200 A" all find the same section.</p>

        <p>Browse the full tables: <a href="/steel-sections/eu/heaa/">HEAA</a>, <a href="/steel-sections/eu/hea/">HEA</a>, <a href="/steel-sections/eu/heb/">HEB</a>, <a href="/steel-sections/eu/hem/">HEM</a>.</p>
      </div>
{cta_block(None)}
"""
    write(url, page("HEA vs HEB vs HEM", "What the A, B and M letters mean in the European HE wide flange series, dimensions compared size by size, and how to choose between HEA, HEB and HEM.", url, body, ld))
    return url


# ---------------------------------------------------------------------------
# Sitemap
# ---------------------------------------------------------------------------

STATIC_URLS = [
    ("/", "1.0"), ("/about/", "0.5"), ("/support/", "0.3"), ("/privacy/", "0.3"),
    ("/apps/livesick/", "0.8"), ("/apps/steel-profiles-pro/", "0.8"), ("/apps/steel-profiles-free/", "0.8"),
    ("/apps/steel-profiles-free/whats-new/", "0.6"), ("/apps/wifiphoto/", "0.8"),
    ("/guides/hea-heb-hem/", "0.7"), ("/guides/w-shape-designation/", "0.7"),
    ("/guides/ec3-bolt-resistances/", "0.7"), ("/guides/steel-grade-equivalents/", "0.7"),
]


def write_sitemap(generated):
    lines = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for u, p in STATIC_URLS:
        lines.append(f"  <url>\n    <loc>{SITE}{u}</loc>\n    <priority>{p}</priority>\n  </url>")
    for u, p in generated:
        lines.append(f"  <url>\n    <loc>{SITE}{u}</loc>\n    <priority>{p}</priority>\n  </url>")
    lines.append("</urlset>\n")
    with open(os.path.join(ROOT, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def trim(sec):
    keep = {"entity", "library", "name", "type", "typeIndex", "orderBySizeIndex", "standard"}
    keep |= set(DIM_KEYS[sec["entity"]])
    return {k: v for k, v in sec.items() if k in keep}


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "tools", "data", "sections-dimensions.json")
    with open(src, encoding="utf-8") as f:
        data = json.load(f)
    data = [trim(s) for s in data if s["library"] in LIBRARIES]
    if len(sys.argv) > 1:
        trimmed = os.path.join(ROOT, "tools", "data", "sections-dimensions.json")
        os.makedirs(os.path.dirname(trimmed), exist_ok=True)
        with open(trimmed, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, separators=(",", ":"), sort_keys=True)

    groups = defaultdict(list)
    for s in data:
        groups[(s["library"], s["type"])].append(s)
    for secs in groups.values():
        secs.sort(key=lambda s: s["orderBySizeIndex"])

    # URLs
    by_name = {}
    generated = []
    series_urls = defaultdict(list)
    for (lib, typ), info in SERIES.items():
        if lib == "UK" and typ in HOLLOW:
            continue
        secs = groups.get((lib, typ))
        if not secs:
            print("missing", lib, typ)
            continue
        url = f"/steel-sections/{LIBRARIES[lib]['slug']}/{info['slug']}/"
        series_urls[lib].append((info["title"], url, info["kind"], len(secs)))
        seen = set()
        for s in secs:
            if info["sizes"]:
                slug = size_slug(s)
                if slug in seen:
                    print("duplicate slug", lib, typ, s["name"])
                slug_url = f"{url}{slug}/"
                seen.add(slug)
                s["_url"] = slug_url
            by_name[(lib, s["name"])] = s
    # UK angles are the EN 10056-1 range already published under the European library: link, do not duplicate.
    for typ in ("L=", "L"):
        for s in groups.get(("UK", typ), []):
            eu = by_name.get(("EU", s["name"]))
            if eu and eu.get("_url"):
                s["_url"] = eu["_url"]

    # Pages
    totals = []
    for lib, libinfo in LIBRARIES.items():
        count = 0
        for (l, typ), info in SERIES.items():
            if l != lib or (lib == "UK" and typ in HOLLOW):
                continue
            secs = groups.get((lib, typ))
            if not secs:
                continue
            count += len(secs)
            url = series_page(lib, typ, info, secs, [(t, u) for t, u, _, _ in series_urls[lib]])
            generated.append((url, "0.6"))
            if not info["sizes"]:
                continue
            group_id = next((i for i, g in enumerate(SIBLINGS) if (lib, typ) in g), None)
            for i, s in enumerate(secs):
                prev_sec = secs[i - 1] if i > 0 else None
                next_sec = secs[i + 1] if i + 1 < len(secs) else None
                sibs = []
                if group_id is not None:
                    key = size_key(s)
                    for (sl, st) in SIBLINGS[group_id]:
                        if st == typ:
                            continue
                        for cand in groups.get((sl, st), []):
                            if size_key(cand) == key and cand.get("_url"):
                                sibs.append(cand)
                size_page(lib, typ, info, s, prev_sec, next_sec, sibs, url)
                generated.append((s["_url"], "0.5"))
        library_page(lib, libinfo, series_urls[lib])
        generated.append((f"/steel-sections/{libinfo['slug']}/", "0.7"))
        totals.append((lib, count))
    index_page(totals)
    generated.insert(0, ("/steel-sections/", "0.8"))
    guide_hea_heb_hem({n: s for (l, n), s in by_name.items() if l == "EU"})
    write_sitemap(generated)
    print(f"generated {len(generated)} section pages")


if __name__ == "__main__":
    main()
