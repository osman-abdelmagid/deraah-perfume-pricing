from pathlib import Path
_FONTS = Path(__file__).resolve().parents[1] / "fonts"
F = (_FONTS / "ibm-plex-sans-arabic").as_posix()
NK = (_FONTS / "noto-naskh-arabic").as_posix()
BLUE, RED = "#1D4E89", "#B23A48"
CSS = f"""
@font-face {{ font-family: Plex; font-weight: 400; src: url(file://{F}-arabic-400-normal.woff2), url(file://{F}-latin-400-normal.woff2); }}
@font-face {{ font-family: Plex; font-weight: 600; src: url(file://{F}-arabic-600-normal.woff2), url(file://{F}-latin-600-normal.woff2); }}
@font-face {{ font-family: Plex; font-weight: 700; src: url(file://{F}-arabic-700-normal.woff2), url(file://{F}-latin-700-normal.woff2); }}
@font-face {{ font-family: Naskh; font-weight: 400; src: url(file://{NK}-arabic-400-normal.woff2); }}
@font-face {{ font-family: Naskh; font-weight: 700; src: url(file://{NK}-arabic-700-normal.woff2); }}
@page {{ size: A4; margin: 18mm 20mm 16mm 20mm; }}
* {{ box-sizing: border-box; }}
html {{ direction: rtl; }}
body {{ font-family: Naskh, Plex, serif; color: #222; font-size: 11pt; line-height: 1.75; margin: 0; }}
.page {{ page-break-after: always; position: relative; height: 263mm; overflow: hidden; }}
.page:last-child {{ page-break-after: auto; }}
.runner {{ font-family: Plex; display:flex; justify-content:space-between; font-size:7.8pt; color:#777; margin-bottom:16px; }}
h1, h2, h3, th, .ex, .memo, .exsub, .exsrc, table, .foot, .legend, .dlab, .blab, .bnote, .mlab, .seg, .dval, .bval, .axis-title, .grid span, .ref span {{ font-family: Plex, sans-serif; }}
h1 {{ font-size: 17pt; line-height:1.45; margin: 0 0 10px; font-weight:700; color:#111; }}
h2 {{ font-size: 13.5pt; line-height:1.5; margin: 0 0 8px; font-weight:700; color:#111; }}
h3 {{ font-size: 10.5pt; margin: 14px 0 4px; font-weight:700; color:#111; }}
p {{ margin: 0 0 8px; text-align: justify; }}
.memo {{ border-top: 2px solid #111; border-bottom: 1px solid #111; padding: 6px 0; margin-bottom: 14px; font-size: 9pt; display:grid; grid-template-columns: 60px 1fr 60px 1fr; row-gap:2px; }}
.memo b {{ font-weight:600; color:#555; }}
ol.find {{ margin: 0 0 6px; padding-right: 22px; list-style-type: arabic-indic; }}
ol.find li {{ margin-bottom: 6px; text-align: justify; }}
ol.find li b, p b {{ font-family: Naskh; font-weight: 700; }}
sup {{ font-size: 7pt; line-height:0; color:#555; font-family: Plex; }}
table {{ width:100%; border-collapse: collapse; font-size: 8.7pt; margin: 4px 0 2px; border-top: 1.5px solid #111; border-bottom: 1.5px solid #111; }}
th {{ font-weight:600; padding:5px 5px; text-align:center; border-bottom:1px solid #111; line-height:1.35; color:#111; }}
td {{ padding:4px 5px; text-align:center; border-bottom:1px solid #E4E4E4; line-height:1.45; }}
tr:last-child td {{ border-bottom: none; }}
td:first-child, th:first-child {{ text-align:right; }}
td.l, th.l {{ text-align:right; }}
tr.focus td {{ font-weight:700; color:{BLUE}; }}
tr.rival td {{ font-weight:700; color:{RED}; }}
td.fc {{ font-weight:700; color:{BLUE}; }}
table.tight th, table.tight td {{ padding:4px 3px; }}
table.recs td {{ vertical-align:top; font-size:8.6pt; padding:6px 5px; }}
table.recs td.rn {{ font-weight:700; width:16px; }}
table.recs td.rt {{ font-weight:600; width:165px; color:#111; }}
table.recs th:nth-child(5), table.recs td:nth-child(5) {{ width:62px; }}
table.cat td.barcell {{ text-align:right; width:150px; }}
table.cat .mini {{ display:inline-block; height:8px; vertical-align:middle; margin-left:5px; }}
table.cat tr.hot td:first-child {{ color:{RED}; font-weight:700; }}
table.cat tr.good td:first-child {{ color:{BLUE}; font-weight:700; }}
td.warn {{ color:{RED}; font-weight:600; }}
.ex {{ font-weight:700; font-size:9.5pt; margin: 14px 0 0; color:#111; border-top: 1px solid #111; padding-top: 5px; }}
.ex span {{ font-weight:400; }}
.exsub {{ font-size:8pt; color:#666; margin-bottom: 4px; }}
.exsrc {{ font-size:7.6pt; color:#666; margin: 3px 0 10px; }}
.dot-chart {{ --lab: 100px; position:relative; padding: 22px 0 20px; }}
.dot-chart .grid {{ position:absolute; top:20px; bottom:38px; width:0; border-right:1px solid #EEE; }}
.dot-chart .grid span {{ position:absolute; bottom:-18px; transform:translateX(50%); font-size:7.8pt; color:#666; }}
.dot-chart .ref {{ position:absolute; top:2px; bottom:38px; width:0; border-right:1px dashed #888; }}
.dot-chart .ref span {{ position:absolute; top:-3px; right:5px; white-space:nowrap; font-size:7.8pt; color:#666; }}
.drow {{ display:flex; align-items:center; height:31px; }}
.dlab {{ width: var(--lab); font-size:8.8pt; line-height:1.15; }}
.dlab small {{ display:block; font-size:7.2pt; color:#777; }}
.drow.focus .dlab {{ font-weight:700; }}
.dtrack {{ position:relative; flex:1; height:100%; }}
.range {{ position:absolute; top:14px; height:3px; }}
.dot {{ position:absolute; top:9.5px; width:12px; height:12px; border-radius:50%; }}
.dval {{ position:absolute; top:-6px; width:40px; text-align:center; font-size:8pt; }}
.drow.focus .dval {{ font-weight:700; }}
.axis-title {{ text-align:left; margin-top:16px; font-size:7.8pt; color:#666; }}
.bar-chart .brow {{ display:flex; align-items:center; height:22px; }}
.blab {{ width:90px; font-size:8.8pt; }} .blab.b {{ font-weight:700; }}
.btrack {{ width:220px; display:flex; align-items:center; gap:6px; }}
.bar {{ height:10px; }}
.bval {{ font-size:8.2pt; }}
.bnote {{ flex:1; font-size:8pt; color:#666; padding-right:10px; }}
.legend {{ display:flex; flex-wrap:wrap; gap:2px 12px; font-size:7.8pt; margin: 2px 0 5px; }}
.legend i {{ display:inline-block; width:9px; height:9px; margin-left:4px; vertical-align:middle; }}
.mrow {{ display:flex; align-items:center; height:24px; }}
.mlab {{ width:90px; font-size:8.6pt; line-height:1.1; }}
.mlab small {{ display:block; font-size:7pt; color:#777; }}
.mlab.fb {{ font-weight:700; }}
.mbar {{ flex:1; display:flex; height:16px; }}
.seg {{ height:100%; font-size:7.2pt; display:flex; align-items:center; justify-content:center; border-left:1px solid #fff; }}
.sources {{ direction:ltr; text-align:left; font-family: Plex; font-size:7.8pt; color:#444; line-height:1.55; margin:4px 0 0; padding-left:16px; }}
.foot {{ position:absolute; bottom:0; left:0; right:0; font-size:7.4pt; color:#888; display:flex; justify-content:space-between; }}
"""
