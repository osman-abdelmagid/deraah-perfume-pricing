"""Render the Arabic PDF report from outputs/metrics.json.

Run from the repository root:  python src/build_report.py
Needs: pip install playwright && playwright install chromium
"""
import json, re, asyncio, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from report_style import CSS as BASE_CSS, BLUE, RED
from playwright.async_api import async_playwright

M = json.load(open(ROOT / "outputs" / "metrics.json"))
AR = {"Deraah": "درعة", "Assaf": "عساف", "Al Majed Oud": "الماجد للعود", "Ibraq (Ibrahim Al Qurashi)": "إبراق (إبراهيم القرشي)",
      "Rasasi": "الرصاصي", "Swiss Arabian": "سويس أرابيان", "Ajmal": "أجمل", "Arabian Oud": "العربية للعود"}
SH = {**AR, "Ibraq (Ibrahim Al Qurashi)": "إبراق"}
H = ["Deraah", "Assaf", "Al Majed Oud", "Ibraq (Ibrahim Al Qurashi)", "Rasasi", "Swiss Arabian", "Ajmal", "Arabian Oud"]
HP = [h for h in H if h != "Swiss Arabian"]  # houses with enough sizes for price per ml
GREY = "#BFC3C9"
SB_AR = {"AL GAZIRA": "الجزيرة", "H2O": "إتش تو أو", "RING": "رينج", "GINGLE": "جينجل", "ONE LOVE": "ون لوف", "MAIOS": "مايوس",
         "LABEAUTE": "لابوتيه", "LINK": "لينك", "POUR MOI": "بور موا", "V.S": "في إس", "Q&A": "كيو آند إيه", "CAGE": "كيج",
         "PROUD": "براود", "JADDID": "جديد", "DERAAH OUD": "درعة عود", "PAPILLON": "بابيون", "DERAAH PRIVATE": "درعة برايفت",
         "MAISON D'ORIENT": "ميزون دورينت", "MON BOUQUET": "مون بوكيه"}
DATE = "٢٥ نوفمبر ٢٠٢٦"
AUTHOR = "عثمان عبدالماجد"
SRC = '<div class="exsrc">المصدر: المتاجر الإلكترونية الرسمية للشركات، ٢٥ نوفمبر ٢٠٢٦؛ تحليل المُعِدّ.</div>'
def sup(k): return f"<sup>{k}</sup>"
def pct(x, d=0): return f"{x*100:.{d}f}%"
def n(x): return f"{x:,.0f}"
def f2(x): return f"{x:.2f}"
ppm = M["ppm"]
def col(h): return BLUE if h == "Deraah" else (RED if h == "Assaf" else GREY)
def rowcls(h): return ' class="focus"' if h == "Deraah" else (' class="rival"' if h == "Assaf" else "")

# ---------- Exhibit 1: price per ml dot + IQR ----------
def ppm_chart():
    rows = sorted(HP, key=lambda h: ppm[h]["med"]); vmax = 4.6; ref = M["list_ppm"]["Deraah"]
    o = ['<div class="dot-chart">']
    for t in range(0, 5):
        o.append(f'<div class="grid" style="right:calc(var(--lab) + (100% - var(--lab)) * {t/vmax})"><span>{t}</span></div>')
    o.append(f'<div class="ref" style="right:calc(var(--lab) + (100% - var(--lab)) * {ref/vmax})"><span>سعر درعة قبل الخصم {f2(ref)}</span></div>')
    for h in rows:
        p = ppm[h]; c = col(h); foc = h in ("Deraah", "Assaf")
        o.append(f'''<div class="drow{' focus' if foc else ''}"><div class="dlab">{SH[h]}<small>{M["ppm_n"][h]} عطراً</small></div>
          <div class="dtrack"><div class="range" style="right:{p["p25"]/vmax*100}%;width:{(p["p75"]-p["p25"])/vmax*100}%;background:{c};opacity:.45"></div>
          <div class="dot" style="right:calc({p["med"]/vmax*100}% - 6px);background:{c}"></div>
          <div class="dval" style="right:calc({p["med"]/vmax*100}% - 20px)">{f2(p["med"])}</div></div></div>''')
    o.append('<div class="axis-title">ريال لكل مل</div></div>')
    return "\n".join(o)

def price_table():
    r = []
    for h in sorted(HP, key=lambda h: ppm[h]["med"]):
        mp = M["med_price_100"][h]
        r.append(f'<tr{rowcls(h)}><td>{AR[h]}</td><td>{M["ppm_n"][h]}</td><td>{f2(ppm[h]["med"])}</td><td>{f2(M["eff_ppm"][h])}</td><td>{n(mp) if mp == mp else "—"}</td></tr>')
    return f'<table><thead><tr><th>الشركة</th><th>عطور مقاسة</th><th>سعر المل المعروض</th><th>سعر المل بعد عروض الباقات</th><th>سعر عبوة ١٠٠ مل</th></tr></thead><tbody>{"".join(r)}</tbody></table>'

# ---------- Exhibit 3: price bands stacked ----------
BANDS = [("<1", "أقل من ١ ريال/مل", "#DCE5F0"), ("1-2", "من ١ إلى ٢", "#9DB6D6"), ("2-4", "من ٢ إلى ٤", "#4F7DB3"), ("4+", "٤ فأكثر", "#1D3F6E")]
def band_chart():
    o = ['<div class="legend">' + "".join(f'<span><i style="background:{c}"></i>{l}</span>' for _, l, c in BANDS) + '</div><div class="mix">']
    for h in sorted(HP, key=lambda h: -M["bands"][h]["<1"]):
        segs = []
        for k, _, c in BANDS:
            v = M["bands"][h][k]
            if v <= 0: continue
            segs.append(f'<div class="seg" style="width:{v*100}%;background:{c};color:{"#fff" if k in ("2-4","4+") else "#222"}">{pct(v) if v >= 0.06 else ""}</div>')
        o.append(f'<div class="mrow"><div class="mlab{" fb" if h in ("Deraah","Assaf") else ""}">{SH[h]}</div><div class="mbar">{"".join(segs)}</div></div>')
    return "\n".join(o) + "</div>"

# ---------- Exhibit 4: Deraah sub-brands ----------
def sb_chart():
    sb = sorted(M["subbrands"].items(), key=lambda kv: kv[1]["median"]); vmax = 3.6
    a = ppm["Assaf"]["med"]
    o = ['<div class="dot-chart sb">']
    for t in range(0, 4):
        o.append(f'<div class="grid" style="right:calc(var(--lab) + (100% - var(--lab)) * {t/vmax})"><span>{t}</span></div>')
    o.append(f'<div class="ref" style="right:calc(var(--lab) + (100% - var(--lab)) * {a/vmax})"><span>متوسط عساف {f2(a)}</span></div>')
    o.append(f'<div class="band" style="right:calc(var(--lab) + (100% - var(--lab)) * {1.0/vmax});width:calc((100% - var(--lab)) * {0.35/vmax})"></div>')
    for k, v in sb:
        o.append(f'''<div class="drow"><div class="dlab">{SB_AR.get(k,k)} <span class="cnt">({v["size"]})</span></div>
          <div class="dtrack"><div class="range" style="right:{v["min"]/vmax*100}%;width:{(v["max"]-v["min"])/vmax*100}%;background:{GREY}"></div>
          <div class="dot" style="right:calc({v["median"]/vmax*100}% - 6px);background:{BLUE}"></div>
          <div class="dval" style="right:calc({v["median"]/vmax*100}% + 7px);top:-1px;background:#fff;width:auto;padding:0 2px">{f2(v["median"])}</div></div></div>''')
    o.append('<div class="axis-title">ريال لكل مل</div></div>')
    return "\n".join(o)

# ---------- Exhibit 5: effective discount ----------
MECH = {"Deraah": "سعر مشطوب على كل العطور تقريباً", "Assaf": "سعر مشطوب، ومعه «٣ بسعر ٢» على معظم العطور",
        "Al Majed Oud": "شارة نسبة خصم", "Ibraq (Ibrahim Al Qurashi)": "شارة نسبة خصم", "Swiss Arabian": "سعر مشطوب",
        "Arabian Oud": "سعر مشطوب على جزء من العطور", "Rasasi": "«٣ بسعر ٢»", "Ajmal": "«الثاني بنصف السعر»"}
def disc_chart():
    o = ['<div class="bar-chart">']
    for h in sorted(H, key=lambda h: -M["eff_disc"][h]):
        v = M["eff_disc"][h]
        o.append(f'<div class="brow"><div class="blab{" b" if h in ("Deraah","Assaf") else ""}">{SH[h]}</div><div class="btrack"><div class="bar" style="width:{v/0.7*100}%;background:{col(h)}"></div><span class="bval">{pct(v)}</span></div><div class="bnote">{MECH[h]}</div></div>')
    return "\n".join(o) + "</div>"

def disc_table():
    r = []
    for h in sorted(H, key=lambda h: -M["eff_disc"][h]):
        lp = M["list_ppm"][h]; sp = ppm[h]["med"] if h != "Swiss Arabian" else None
        r.append(f'<tr{rowcls(h)}><td>{AR[h]}</td><td>{pct(M["share_markdown"][h])}</td><td>{pct(M["share_bundle"][h])}</td>'
                 f'<td>{pct(M["md_disc"][h]) if M["md_disc"][h]==M["md_disc"][h] else "—"}</td>'
                 f'<td>{f2(lp) if lp==lp else "—"}</td><td>{f2(sp) if sp else "—"}</td></tr>')
    return f'<table><thead><tr><th>الشركة</th><th>عطور بسعر مشطوب</th><th>عطور عليها عرض باقة</th><th>متوسط عمق الشطب</th><th>سعر المل قبل الخصم</th><th>سعر المل بعد الخصم</th></tr></thead><tbody>{"".join(r)}</tbody></table>'

RECS = [
    ("خط عطور اقتصادي محدد بأقل من ريال للمل لمواجهة عساف",
     f"{pct(M['under1']['Deraah'])} فقط من عطور درعة بأقل من ريال للمل، مقابل {pct(M['under1']['Assaf'])} لعساف. خفض أسعار التشكيلة كلها يضغط الهامش بلا داعٍ.",
     "فرق السعر مع عساف في الخط الاقتصادي، وهامش الخط", "٦٠ يوماً"),
    ("استبدال جزء من الشطب بعروض باقات على العطور",
     f"لا تستخدم درعة الباقات على عطورها، بينما تغطي {pct(M['share_bundle']['Rasasi'])} من عطور الرصاصي و{pct(M['share_bundle']['Ajmal'])} من عطور أجمل و{pct(M['share_bundle']['Assaf'])} من عطور عساف.",
     "عدد القطع في الطلب، والهامش لكل طلب", "تجربة ٨ أسابيع"),
    ("تجربة سعر ثابت بلا شطب على عدد من العطور الرئيسية",
     f"{pct(M['share_markdown']['Deraah'])} من عطور درعة مشطوبة بمتوسط {pct(M['md_disc']['Deraah'])}، فلم يعد السعر قبل الخصم ({f2(M['list_ppm']['Deraah'])} ريال للمل) مرجعاً للعميل.",
     "المبيع والهامش مقارنة بمجموعة ضابطة", "تجربة ٨ أسابيع"),
    ("سلّم سعري واضح للعلامات الفرعية بفروق ثابتة",
     f"{M['n_band']} من {M['n_labels4']} علامة يقع متوسط سعرها بين ١٫٠ و١٫٣٥ ريال للمل، فلا يرى العميل فرقاً بينها.",
     "عدد العلامات في كل مستوى، والفرق السعري بين المستويات", "١٢ شهراً"),
    ("متتبع أسبوعي لأسعار المنافسين وعروضهم",
     "الأسعار والعروض تتغير بين المواسم، وبيانات هذه المذكرة لقطة واحدة من موسم نوفمبر.",
     "تحديث أسبوعي آلي للمنافسين الثمانية", "٣٠ يوماً"),
]
def recs_table():
    r = "".join(f'<tr><td class="rn">{i+1}</td><td class="l rt">{a}</td><td class="l">{b}</td><td class="l">{c}</td><td>{d}</td></tr>' for i, (a, b, c, d) in enumerate(RECS))
    return f'<table class="recs"><thead><tr><th></th><th class="l">التوصية</th><th class="l">السبب</th><th class="l">مؤشر النجاح</th><th>المدة</th></tr></thead><tbody>{r}</tbody></table>'

CSS = BASE_CSS + """
.dot-chart.sb .drow { height: 19px; } .dot-chart.sb .dlab { font-size:8.2pt; } .cnt { color:#888; font-size:7.2pt; }
.dot-chart.sb .dval { font-size: 7.2pt; line-height:1.4; }
.dot-chart.sb .dot { top: 5px; width: 9px; height: 9px; }
.dot-chart.sb .range { top: 9px; height: 2px; }
.dot-chart .band { position:absolute; top:22px; bottom:38px; background: rgba(178,58,72,.08); }
"""

def runner(p): return f'<div class="runner"><span>درعة مقابل المنافسين: أسعار العطور وعروضها</span><span>{p}</span></div>'

p1 = f"""<div class="page">{runner(1)}
<div class="memo"><b>إلى</b><span>إدارة التحليلات، درعة</span><b>التاريخ</b><span>{DATE}</span>
<b>من</b><span>{AUTHOR}</span><b>الموضوع</b><span>مقارنة أسعار عطور درعة وعروضها بالمنافسين</span></div>
<h1>درعة لم تعد الأرخص في العطور، وخصمها الدائم لم يعد يميّزها</h1>
<p>تنافس درعة بالسعر: متوسط سعر المل لعطورها {f2(ppm["Deraah"]["med"])} ريال، أي أقل من نصف سعر العربية للعود. لكن عساف يبيع اليوم أرخص منها، والخصم بنسبة النصف تقريباً صار ممارسة معظم الشركات. تستند هذه المذكرة إلى {n(M["n_perf"])} عطراً جُمعت من المتاجر الإلكترونية لدرعة وسبعة منافسين، وتقتصر على العطور وأسعارها وعروضها.</p>
<h3>النتائج الرئيسية</h3>
<ol class="find">
<li><b>عساف أرخص من درعة.</b> يبيع العطر بـ{f2(ppm["Assaf"]["med"])} ريال للمل، وبـ{f2(M["eff_ppm"]["Assaf"])} مع عرض «٣ بسعر ٢». و{pct(M["deraah_above_assaf"])} من عطور درعة أغلى من متوسطه، والماجد للعود يبيع بسعر درعة نفسه ({f2(ppm["Al Majed Oud"]["med"])}).</li>
<li><b>درعة بلا خط اقتصادي واضح.</b> {pct(M["under1"]["Deraah"])} من عطورها بأقل من ريال للمل مقابل {pct(M["under1"]["Assaf"])} لعساف، و{pct(M["bands"]["Deraah"]["1-2"])} منها محصورة بين ريال وريالين.</li>
<li><b>السعر المشطوب فقد معناه.</b> {pct(M["share_markdown"]["Deraah"])} من عطور درعة مشطوبة بمتوسط {pct(M["md_disc"]["Deraah"])}، كما هي الحال لدى معظم المنافسين. أما الرصاصي وأجمل فيعتمدان عروض الباقات بدل الشطب.</li>
<li><b>العلامات الفرعية متقاربة السعر.</b> {M["n_band"]} من {M["n_labels4"]} علامة لعطور درعة يقع متوسط سعرها بين ١٫٠ و١٫٣٥ ريال للمل.</li>
</ol>
<h3>التوصيات</h3>
{recs_table()}
<p style="font-size:9.5pt;margin-top:6px">رُتّبت التوصيات حسب الأثر المتوقع. الثانية والثالثة تُختبران على نطاق محدود قبل تعميمهما.</p>
</div>"""

p2 = f"""<div class="page">{runner(2)}
<h2>١. مستوى السعر: عساف يبيع أرخص من درعة، و{pct(M["deraah_above_assaf"])} من عطور درعة أغلى من متوسطه</h2>
<p>للمقارنة بين عطور مختلفة الأحجام، حُسب سعر المل (سعر البيع مقسوماً على الحجم) لعطور البخاخ المفردة من ٢٠ إلى ٣٠٠ مل. تقع درعة والماجد للعود في المستوى نفسه، ويقع عساف تحتهما، بينما تتوزع عطور العربية للعود وأجمل على نطاق أوسع يتجاوز ٤ ريالات للمل.</p>
<div class="ex">شكل ١ <span>· متوسط سعر المل والنطاق الذي يقع فيه نصف عطور كل شركة (ريال)</span></div>
<div class="exsub">النقطة: الوسيط. الخط: من الربع الأول إلى الربع الثالث.</div>
{ppm_chart()}
{SRC}
<div class="ex">شكل ٢ <span>· مؤشرات سعر العطور حسب الشركة (ريال)</span></div>
{price_table()}
<div class="exsrc">ملاحظة: «بعد عروض الباقات» يحتسب أثر «٣ بسعر ٢» (ثلث السعر) أو «الثاني بنصف السعر» (ربع السعر) عند شراء الكمية المطلوبة. استُبعدت سويس أرابيان لأنها لا تنشر الحجم إلا لـ١١ من ٦٣ عطراً. المصدر: المتاجر الإلكترونية الرسمية للشركات، ٢٥ نوفمبر ٢٠٢٦؛ تحليل المُعِدّ.</div>
<p>عبوة ١٠٠ مل من درعة بـ{n(M["med_price_100"]["Deraah"])} ريالاً في المتوسط، ومن عساف بـ{n(M["med_price_100"]["Assaf"])}. ومع عروض الباقات تتغير الصورة: الرصاصي، رغم سعره المعروض الأعلى، يقترب من درعة ({f2(M["eff_ppm"]["Rasasi"])} مقابل {f2(M["eff_ppm"]["Deraah"])}) لمن يشتري ثلاث قطع.</p>
</div>"""

p3 = f"""<div class="page">{runner(3)}
<h2>٢. السلّم السعري: درعة بلا خط اقتصادي واضح، وعلاماتها الفرعية في نطاق سعري واحد</h2>
<p>يوزّع شكل ٣ عطور كل شركة على شرائح سعر المل. عساف يركّز ثلثي عطوره تحت ريال للمل، بينما تتركز عطور درعة بين ريال وريالين، ولا تتجاوز ريالين إلا في {pct(M["bands"]["Deraah"]["2-4"]+M["bands"]["Deraah"]["4+"])} من العطور.</p>
<div class="ex">شكل ٣ <span>· توزيع العطور على شرائح سعر المل (حصة من عطور كل شركة)</span></div>
{band_chart()}
{SRC}
<div class="ex">شكل ٤ <span>· العلامات الفرعية لعطور درعة: متوسط سعر المل وأدنى سعر وأعلاه (ريال)</span></div>
<div class="exsub">النقطة: الوسيط. الخط: من أرخص عطر إلى أغلاه. المنطقة المظللة: من ١٫٠ إلى ١٫٣٥ ريال للمل. بين القوسين: عدد العطور.</div>
{sb_chart()}
{SRC}
<p>{M["n_band"]} علامة من {M["n_labels4"]} يقع متوسطها في المنطقة المظللة، فلا يرى العميل فرقاً سعرياً بينها. تنصح «ماكنزي» بأن يضع تاجر التجزئة فروقاً سعرية ثابتة بين مستويات علاماته الخاصة ويراقب الالتزام بها،{sup("٣")} وقد خفّضت سلاسل كبرى عدد مستويات علاماتها؛ ألغت «تيسكو» علامتها الاقتصادية،{sup("٤")} وخفّضت «بي جيه» خطوط علاماتها الخاصة من عشرة إلى اثنين.{sup("٥")}</p>
</div>"""

p4 = f"""<div class="page">{runner(4)}
<h2>٣. الخصومات: معظم الشركات تخصم النصف على كل العطور تقريباً، والفرق في آلية العرض</h2>
<p>تختلف آليات العروض بين الشركات، لذلك حُوِّل كل عرض إلى خصم فعلي على السعر: السعر المشطوب أو شارة النسبة تساوي الفرق بين السعرين، و«٣ بسعر ٢» تساوي ٣٣٪ عند شراء ثلاث قطع، و«الثاني بنصف السعر» تساوي ٢٥٪ عند شراء قطعتين. ويجمع عساف بين الشطب و«٣ بسعر ٢» على معظم عطوره.</p>
<div class="ex">شكل ٥ <span>· متوسط الخصم الفعلي على العطور وآلية العرض</span></div>
{disc_chart()}
{SRC}
<div class="ex">شكل ٦ <span>· الشطب والباقات والسعر قبل الخصم وبعده</span></div>
{disc_table()}
{SRC}
<p>تشير الأبحاث إلى أن الخصم الدائم يفقد أثره. في استطلاع لـ«باين آند كومباني» شمل أكثر من ٣٠ ألف مستهلك، كانت الصلة بين الخصومات والقيمة المدركة ضعيفة، بينما ارتبط التسعير اليومي الثابت بها ارتباطاً قوياً.{sup("٢")} ويتراجع أثر الخصم مع عمقه: في إحدى الحالات رفع الخصم من ٢٠٪ إلى ٣٠٪ المبيعات ٧٪، بينما جاء رفعه من ٥٠٪ إلى ٦٠٪ بنتيجة عكسية.{sup("٢")} كما تشترط وزارة التجارة ترخيصاً لكل تخفيض، وبطاقة تبيّن السعر قبل التخفيض وبعده، وعروضاً حقيقية بلا تضليل في الأسعار،{sup("٦")} وهو ما يصعب الدفاع عنه حين يكون السعر المشطوب دائماً.</p>
<p>لذلك لا يُنصح بمجاراة عساف بخصم أعمق. البديل عروض باقات متعددة القطع على العطور، كما تفعل الرصاصي وأجمل، مع تجربة سعر ثابت بلا شطب على عدد محدود من العطور الرئيسية ومقارنة المبيع والهامش بمجموعة ضابطة.</p>
</div>"""

p5 = f"""<div class="page">{runner(5)}
<h2>المنهجية وحدود البيانات</h2>
<h3>المصادر والتغطية</h3>
<p>جُمعت البيانات في {DATE} من صفحات الأقسام العامة في المتاجر الإلكترونية الرسمية لثماني شركات: درعة، عساف، الماجد للعود، إبراق (إبراهيم القرشي)، الرصاصي، سويس أرابيان، أجمل، العربية للعود. يقتصر التحليل على العطور ({n(M["n_perf"])} عطراً، منها {n(M["perf_n"]["Deraah"])} لدرعة)، ويستبعد الزيوت والبخور والأطقم والمعطرات والإكسسوارات. اختيرت الشركات لأنها ضمن أكبر الحصص السوقية (العربية للعود ١٢٫٧٪، درعة ٦٫١٪، الماجد ٥٫٢٪ في ٢٠٢٢ وفق يورومونيتور)،{sup("١")} أو لأنها تنافس درعة مباشرة في الفئة الاقتصادية (عساف وإبراق).</p>
<h3>سعر المل</h3>
<p>سعر المل هو سعر البيع مقسوماً على الحجم، ويُحسب لعطور البخاخ المفردة من ٢٠ إلى ٣٠٠ مل فقط. الحجم من اسم المنتج أو صفحته. ولعطور درعة التي لا يذكر اسمها الحجم، أُخذ من رمز المنتج، وقد طابق الحجم المذكور في ٩٩٫٣٪ من ٤١١ حالة. وتعرض درعة بعض العطور بأكثر من صفحة؛ دُمجت الصفحات ذات الاسم والحجم والسعر الواحد.</p>
<h3>الخصم الفعلي</h3>
<p>السعر المشطوب أو شارة النسبة تُحتسب بالفرق بين السعرين. عرض «٣ بسعر ٢» يساوي ٣٣٪، و«الثاني بنصف السعر» ٢٥٪، ولا يتحققان إلا بشراء الكمية المطلوبة. وحين يجتمع الشطب والباقة (عساف) يُحتسب الأثران معاً. وسعر الماجد للعود قبل الخصم محسوب من شارة النسبة على بطاقة المنتج، وتحققتُ منه يدوياً (١٤٩ ريالاً مع شارة ٥٠٪ تقابل ٢٩٨ ريالاً على الموقع).</p>
<h3>الحدود</h3>
<p>البيانات لقطة واحدة من موسم عروض نوفمبر، والخصومات في شهر عادي قد تكون أقل. أسعار المتجر الإلكتروني قد تختلف عن أسعار الفروع. سويس أرابيان لا تنشر الحجم لمعظم عطورها، فاستُبعدت من مقارنة سعر المل. ولم يُشمل عبدالصمد القرشي (ثاني أكبر حصة) ولا دخون لتعذّر الوصول إلى متجريهما. ولا تتضمن المذكرة بيانات مبيعات؛ قياس أثر التوصيات يحتاج ربطها ببيانات المبيعات الداخلية لدرعة.</p>
<h3>المراجع</h3>
<ol class="sources">
<li>Argaam (19 Aug 2024), "A look at market share of major Saudi perfume companies" (Euromonitor data from the Al Majed for Oud IPO prospectus).</li>
<li>Bain &amp; Company, "Curing the Discount Disease in Soft Goods Retail".</li>
<li>McKinsey &amp; Company, "The potential for powerhouse private brands: an updated view".</li>
<li>McKinsey &amp; Company, "A turning point for private brands: How retailers can seize the opportunity".</li>
<li>Store Brands (2015), "Too Many Brands?".</li>
<li>Saudi Ministry of Commerce, "9 controls for commercial discounts in stores and e-commerce", mc.gov.sa.</li>
</ol>
</div>"""

html = f'<!DOCTYPE html><html lang="ar" dir="rtl"><head><meta charset="utf-8"><style>{CSS}</style></head><body>{p1}{p2}{p3}{p4}{p5}</body></html>'

AD = str.maketrans("0123456789", "٠١٢٣٤٥٦٧٨٩")
def arabize(t):
    t = re.sub(r"(?<=\d),(?=\d{3})", "٬", t)
    t = re.sub(r"(?<=\d)\.(?=\d)", "٫", t)
    return t.replace("%", "٪").translate(AD)
head, body = html.split("<body>", 1)
parts = re.split(r'(<ol class="sources">.*?</ol>|<[^>]+>)', body, flags=re.S)
html = head + "<body>" + "".join(p if p.startswith("<") else arabize(p) for p in parts)
HTML = ROOT / "outputs" / "report.html"
HTML.write_text(html, encoding="utf-8")

async def main():
    async with async_playwright() as p:
        import os
        b = await p.chromium.launch(executable_path=os.environ.get("CHROME_PATH"), args=["--allow-file-access-from-files"])
        pg = await b.new_page()
        await pg.goto(HTML.as_uri())
        await pg.wait_for_timeout(900)
        await pg.pdf(path=str(ROOT / "report" / "deraah_perfume_pricing_ar.pdf"), format="A4", print_background=True,
                     margin={"top": "18mm", "bottom": "16mm", "left": "20mm", "right": "20mm"})
        await b.close()
asyncio.run(main())
print("ok")
