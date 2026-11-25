"""First draft of the Power BI project. The committed powerbi/ folder is what Power BI Desktop saved after opening this.

Generate a Power BI Project (PBIP): TMDL semantic model + report (report.json) for the Deraah competitor analysis."""
import json, os, uuid, shutil

NAME = "Deraah_Pricing"
from pathlib import Path
OUT = str(Path(__file__).resolve().parents[1] / "outputs" / "pbip_generated")
DATA_FOLDER = r"C:\Users\USER\Documents\Projects\deraah_market_analysis\deraah-perfume-pricing\data\powerbi" + "\\"
shutil.rmtree(OUT, ignore_errors=True)
SM = f"{OUT}/{NAME}.SemanticModel"
RP = f"{OUT}/{NAME}.Report"
os.makedirs(f"{SM}/definition/tables", exist_ok=True)
os.makedirs(RP, exist_ok=True)

def w(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\r\n") as f:
        f.write(text)

# ---------------- project files ----------------
w(f"{OUT}/{NAME}.pbip", json.dumps({
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/pbip/pbipProperties/1.0.0/schema.json",
    "version": "1.0", "artifacts": [{"report": {"path": f"{NAME}.Report"}}],
    "settings": {"enableAutoRecovery": True}}, indent=2))
w(f"{RP}/definition.pbir", json.dumps({
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definitionProperties/1.0.0/schema.json",
    "version": "4.0", "datasetReference": {"byPath": {"path": f"../{NAME}.SemanticModel"}}}, indent=2))
w(f"{SM}/definition.pbism", json.dumps({
    "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/semanticModel/definitionProperties/1.0.0/schema.json",
    "version": "4.0", "settings": {}}, indent=2))
w(f"{OUT}/.gitignore", "**/.pbi/localSettings.json\n**/.pbi/cache.abf\n")

# ---------------- TMDL ----------------
T = "\t"
w(f"{SM}/definition/database.tmdl", "database\n\tcompatibilityLevel: 1567\n")
tables = {
 "fact_perfumes": {"file": "fact_perfumes.csv", "cols": [("house","string"),("sub_brand","string"),("product_id","string"),("product_name","string"),
   ("gender","string"),("size_value","double"),("size_unit","string"),("units_in_pack","int64"),("price_sar","double"),("list_price_sar","double"),
   ("on_markdown","boolean"),("discount_pct","double"),("promo_type","string"),("effective_discount","double"),("price_per_ml","double"),
   ("list_price_per_ml","double"),("eff_price_per_ml","double"),("ppm_band","string"),("price_band_sar","string"),("url","string"),
   ("scrape_date","string"),("promo_ar","string"),("is_bundle","boolean"),("sub_brand_ar","string")]},
 "dim_house": {"file": "dim_house.csv", "cols": [("house","string"),("house_ar","string"),("house_sort","int64"),("is_focus","boolean"),
           ("market_share_2022","double"),("branches_2022","int64"),("platform","string"),("store_url","string"),("promo_model","string")]},
 "dim_ppm_band": {"file": "dim_ppm_band.csv", "cols": [("ppm_band","string"),("ppm_band_ar","string"),("ppm_sort","int64")]},
}
MTYPE = {"string": "type text", "double": "type number", "int64": "Int64.Type", "boolean": "type logical", "dateTime": "type date"}
SORTBY = {("dim_house","house_ar"): "house_sort", ("dim_ppm_band","ppm_band_ar"): "ppm_sort"}
FMT = {"price_sar": "#,0.00", "list_price_sar": "#,0.00", "price_per_ml": "0.00", "list_price_per_ml": "0.00", "eff_price_per_ml": "0.00",
       "discount_pct": "0%", "effective_discount": "0%", "market_share_2022": "0.0%"}
FACT = "fact_perfumes"
MEASURES = [
 ("Perfumes", "COUNTROWS ( fact_perfumes )", "#,0"),
 ("Perfumes Priced per ml", "CALCULATE ( COUNTROWS ( fact_perfumes ), NOT ISBLANK ( fact_perfumes[price_per_ml] ) )", "#,0"),
 ("Median Price per ml", "MEDIAN ( fact_perfumes[price_per_ml] )", "0.00"),
 ("Median Price per ml after Bundles", "MEDIAN ( fact_perfumes[eff_price_per_ml] )", "0.00"),
 ("Median List Price per ml", "MEDIAN ( fact_perfumes[list_price_per_ml] )", "0.00"),
 ("P25 Price per ml", "PERCENTILEX.INC ( FILTER ( fact_perfumes, NOT ISBLANK ( fact_perfumes[price_per_ml] ) ), fact_perfumes[price_per_ml], 0.25 )", "0.00"),
 ("P75 Price per ml", "PERCENTILEX.INC ( FILTER ( fact_perfumes, NOT ISBLANK ( fact_perfumes[price_per_ml] ) ), fact_perfumes[price_per_ml], 0.75 )", "0.00"),
 ("Min Price per ml", "MIN ( fact_perfumes[price_per_ml] )", "0.00"),
 ("Max Price per ml", "MAX ( fact_perfumes[price_per_ml] )", "0.00"),
 ("Median Price 100ml", "CALCULATE ( MEDIAN ( fact_perfumes[price_sar] ), fact_perfumes[size_value] = 100, NOT ISBLANK ( fact_perfumes[price_per_ml] ) )", "#,0"),
 ("Share Under 1 SAR per ml", "DIVIDE ( CALCULATE ( [Perfumes], fact_perfumes[price_per_ml] < 1 ), [Perfumes Priced per ml] )", "0%"),
 ("Share Marked Down", "DIVIDE ( CALCULATE ( [Perfumes], fact_perfumes[on_markdown] = TRUE () ), [Perfumes] )", "0%"),
 ("Share with Bundle Offer", "DIVIDE ( CALCULATE ( [Perfumes], fact_perfumes[is_bundle] = TRUE () ), [Perfumes] )", "0%"),
 ("Median Markdown Depth", "CALCULATE ( MEDIAN ( fact_perfumes[discount_pct] ), fact_perfumes[on_markdown] = TRUE () )", "0%"),
 ("Median Effective Discount", "MEDIAN ( fact_perfumes[effective_discount] )", "0%"),
 ("Share of House Perfumes", "DIVIDE ( [Perfumes Priced per ml], CALCULATE ( [Perfumes Priced per ml], REMOVEFILTERS ( dim_ppm_band ) ) )", "0%"),
]

def table_tmdl(name, spec):
    lines = [f"table {name}", f"\tlineageTag: {uuid.uuid4()}", ""]
    if name == FACT:
        for mname, expr, fmt in MEASURES:
            lines += [f"\tmeasure '{mname}' = {expr}", f"\t\tformatString: {fmt}", f"\t\tlineageTag: {uuid.uuid4()}", ""]
    for c, dt in spec["cols"]:
        lines += [f"\tcolumn {c}", f"\t\tdataType: {dt}"]
        if c in FMT: lines.append(f"\t\tformatString: {FMT[c]}")
        lines.append("\t\tsummarizeBy: none")
        if (name, c) in SORTBY: lines.append(f"\t\tsortByColumn: {SORTBY[(name, c)]}")
        lines += [f"\t\tlineageTag: {uuid.uuid4()}", f"\t\tsourceColumn: {c}", "", "\t\tannotation SummarizationSetBy = Automatic", ""]
    types = ", ".join('{"%s", %s}' % (c, MTYPE[t]) for c, t in spec["cols"])
    lines += [f"\tpartition {name} = m", "\t\tmode: import", "\t\tsource =", "\t\t\t\tlet",
              f"\t\t\t\t    Source = Csv.Document(File.Contents(DataFolder & \"{spec['file']}\"), [Delimiter=\",\", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),",
              "\t\t\t\t    Promoted = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),",
              f"\t\t\t\t    Typed = Table.TransformColumnTypes(Promoted, {{{types}}}, \"en-US\")",
              "\t\t\t\tin", "\t\t\t\t    Typed", "", "\tannotation PBI_ResultType = Table", ""]
    return "\n".join(lines)

for n_, spec in tables.items():
    w(f"{SM}/definition/tables/{n_}.tmdl", table_tmdl(n_, spec))
w(f"{SM}/definition/expressions.tmdl",
  f'expression DataFolder = "{DATA_FOLDER}" meta [IsParameterQuery=true, Type="Text", IsParameterQueryRequired=true]\n'
  f"\tlineageTag: {uuid.uuid4()}\n\n\tannotation PBI_ResultType = Text\n")
rels = [(FACT, "house", "dim_house", "house"), (FACT, "ppm_band", "dim_ppm_band", "ppm_band")]
w(f"{SM}/definition/relationships.tmdl", "\n".join(
    f"relationship {uuid.uuid4()}\n\tfromColumn: {a}.{b}\n\ttoColumn: {c}.{e}\n" for a, b, c, e in rels))
w(f"{SM}/definition/model.tmdl", "\n".join([
    "model Model", "\tculture: en-US", "\tdefaultPowerBIDataSourceVersion: powerBI_V3", "\tsourceQueryCulture: en-US",
    "\tdataAccessOptions", "\t\tlegacyRedirects", "\t\treturnErrorValuesAsNull", "",
    "annotation __PBI_TimeIntelligenceEnabled = 0", "",
    "annotation PBI_QueryOrder = [\"DataFolder\",\"fact_perfumes\",\"dim_house\",\"dim_ppm_band\"]", "",
    "ref table fact_perfumes", "ref table dim_house", "ref table dim_ppm_band", ""]))

# ---------------- Report (report.json) ----------------
def col(entity, prop, src):
    return {"Column": {"Expression": {"SourceRef": {"Source": src}}, "Property": prop}}
def meas(prop, src="f"):
    return {"Measure": {"Expression": {"SourceRef": {"Source": src}}, "Property": prop}}
ALIAS = {"fact_perfumes": "f", "dim_house": "h", "dim_ppm_band": "b"}

def lit(v):
    return {"expr": {"Literal": {"Value": v}}}

def visual(vtype, x, y, wdt, hgt, roles, title=None, filters=None, order=None, objects=None, z=0):
    """roles: {role: [(kind, entity, prop)]} kind in col/meas"""
    froms, selects, projections = {}, [], {}
    for role, items in roles.items():
        projections[role] = []
        for kind, ent, prop in items:
            a = ALIAS[ent]; froms[a] = ent
            qn = f"{ent}.{prop}"
            if qn not in [s["Name"] for s in selects]:
                expr = col(ent, prop, a) if kind == "col" else meas(prop, a)
                selects.append({**expr, "Name": qn, "NativeReferenceName": prop})
            projections[role].append({"queryRef": qn, **({"active": True} if role in ("Category", "Rows") else {})})
    pq = {"Version": 2, "From": [{"Name": a, "Entity": e, "Type": 0} for a, e in froms.items()], "Select": selects}
    if order:
        kind, ent, prop, direction = order
        a = ALIAS[ent]
        if a not in froms: pq["From"].append({"Name": a, "Entity": ent, "Type": 0})
        pq["OrderBy"] = [{"Direction": direction, "Expression": (col(ent, prop, a) if kind == "col" else meas(prop, a))}]
    sv = {"visualType": vtype, "projections": projections, "prototypeQuery": pq, "drillFilterOtherVisuals": True,
          "columnProperties": {s["Name"]: {"displayName": DISPLAY[s["Name"]]} for s in selects if s["Name"] in DISPLAY}}
    vco = {}
    if title:
        vco["title"] = [{"properties": {"show": lit("true"), "text": lit("'" + title.replace("'", "''") + "'"),
                                        "alignment": lit("'right'"), "fontSize": lit("12D"),
                                        "fontColor": solid("#252423")}}]
    if vco: sv["vcObjects"] = vco
    if objects: sv["objects"] = objects
    name = uuid.uuid4().hex[:20]
    cfg = {"name": name, "layouts": [{"id": 0, "position": {"x": x, "y": y, "z": z, "width": wdt, "height": hgt}}], "singleVisual": sv}
    return {"x": x, "y": y, "z": z, "width": wdt, "height": hgt, "config": json.dumps(cfg, ensure_ascii=False),
            "filters": json.dumps(filters or [], ensure_ascii=False)}


def solid(hexc):
    return {"solid": {"color": {"expr": {"Literal": {"Value": f"'{hexc}'"}}}}}

def sel(entity, prop, value):
    return {"data": [{"scopeId": {"Comparison": {"ComparisonKind": 0,
            "Left": {"Column": {"Expression": {"SourceRef": {"Entity": entity}}, "Property": prop}},
            "Right": {"Literal": {"Value": "'" + value.replace("'", "''") + "'"}}}}}]}

HOUSE_AR = ['درعة','عساف','الماجد للعود','إبراق','الرصاصي','سويس أرابيان','أجمل','العربية للعود']
def house_colors(default="#BFC3C9"):
    return [{"properties": {"fill": solid(default)}}, {"properties": {"fill": solid("#1D4E89")}, "selector": sel("dim_house", "house_ar", "درعة")},
            {"properties": {"fill": solid("#B23A48")}, "selector": sel("dim_house", "house_ar", "عساف")}]
PPM_COLORS = {'أقل من 1':'#DCE5F0','1 إلى 2':'#9DB6D6','2 إلى 4':'#4F7DB3','4 فأكثر':'#1D3F6E'}
def ppm_colors():
    return [{"properties": {"fill": solid(c)}, "selector": sel("dim_ppm_band", "ppm_band_ar", k)} for k, c in PPM_COLORS.items()]
F_ = FACT
DISPLAY = {"dim_house.house_ar": "الشركة", "dim_ppm_band.ppm_band_ar": "شريحة سعر المل (ريال)", f"{F_}.sub_brand_ar": "العلامة الفرعية",
  f"{F_}.promo_ar": "آلية العرض", f"{F_}.product_name": "العطر",
  f"{F_}.Perfumes": "عدد العطور", f"{F_}.Perfumes Priced per ml": "عطور محسوب سعر ملها", f"{F_}.Median Price per ml": "متوسط سعر المل",
  f"{F_}.Median Price per ml after Bundles": "سعر المل بعد الباقات", f"{F_}.Median List Price per ml": "سعر المل قبل الخصم",
  f"{F_}.P25 Price per ml": "الربع الأول", f"{F_}.P75 Price per ml": "الربع الثالث", f"{F_}.Min Price per ml": "أدنى سعر مل", f"{F_}.Max Price per ml": "أعلى سعر مل",
  f"{F_}.Median Price 100ml": "سعر عبوة 100 مل", f"{F_}.Share Under 1 SAR per ml": "أقل من ريال للمل",
  f"{F_}.Share Marked Down": "بسعر مشطوب", f"{F_}.Share with Bundle Offer": "عليها عرض باقة", f"{F_}.Median Markdown Depth": "عمق الشطب",
  f"{F_}.Median Effective Discount": "الخصم الفعلي", f"{F_}.Share of House Perfumes": "حصة من عطور الشركة"}

def house_filter(value="Deraah"):
    return [{"name": uuid.uuid4().hex[:20], "expression": {"Column": {"Expression": {"SourceRef": {"Entity": F_}}, "Property": "house"}},
             "filter": {"Version": 2, "From": [{"Name": "f", "Entity": F_, "Type": 0}],
                        "Where": [{"Condition": {"In": {"Expressions": [col(F_, "house", "f")],
                                                        "Values": [[{"Literal": {"Value": f"'{value}'"}}]]}}}]},
             "type": "Categorical", "howCreated": 1}]

def textbox(x, y, wdt, hgt, paragraphs, z=0):
    paras = [{"textRuns": [{"value": t, "textStyle": {"fontSize": f"{s}pt", **({"fontWeight": "bold"} if b else {})}}], "horizontalTextAlignment": "right"} for t, s, b in paragraphs]
    cfg = {"name": uuid.uuid4().hex[:20], "layouts": [{"id": 0, "position": {"x": x, "y": y, "z": z, "width": wdt, "height": hgt}}],
           "singleVisual": {"visualType": "textbox", "drillFilterOtherVisuals": True, "objects": {"general": [{"properties": {"paragraphs": paras}}]}}}
    return {"x": x, "y": y, "z": z, "width": wdt, "height": hgt, "config": json.dumps(cfg, ensure_ascii=False), "filters": "[]"}

def card(x, y, measure, label, filters=None):
    objs = {"categoryLabels": [{"properties": {"show": lit("true")}}], "labels": [{"properties": {"fontSize": lit("24D")}}]}
    return visual("card", x, y, 290, 110, {"Values": [("meas", F_, measure)]}, title=label, filters=filters, objects=objs)

def m(x): return ("meas", F_, x)
H_AR = ("col", "dim_house", "house_ar")
B_AR = ("col", "dim_ppm_band", "ppm_band_ar")
DER = house_filter(); ASF = house_filter("Assaf")
LBL = [{"properties": {"show": lit("true"), "color": solid("#252423")}}]
GRID_OFF = [{"properties": {"gridlineShow": lit("false")}}]
LEG_TOP = [{"properties": {"position": lit("'Top'")}}]

pages = []
pages.append(("الملخص", [
 textbox(20, 10, 1240, 75, [("درعة مقابل المنافسين: أسعار العطور وعروضها", 20, True),
   ("1,223 عطراً من المتاجر الإلكترونية لثماني شركات، 25 نوفمبر 2026. درعة بالأزرق وعساف بالأحمر. سعر المل لعطور البخاخ المفردة من 20 إلى 300 مل.", 11, False)]),
 card(970, 95, "Median Price per ml", "درعة: متوسط سعر المل (ريال)", DER),
 card(660, 95, "Median Price per ml", "عساف: متوسط سعر المل (ريال)", ASF),
 card(350, 95, "Share Under 1 SAR per ml", "درعة: عطور بأقل من ريال للمل", DER),
 card(40, 95, "Median Effective Discount", "درعة: متوسط الخصم الفعلي", DER),
 visual("clusteredBarChart", 650, 225, 610, 470, {"Category": [H_AR], "Y": [m("Median Price per ml")]},
        title="متوسط سعر المل (ريال): عساف أرخص من درعة", order=("meas", F_, "Median Price per ml", 1),
        objects={"labels": LBL, "dataPoint": house_colors(), "valueAxis": GRID_OFF}),
 visual("clusteredBarChart", 20, 225, 610, 470, {"Category": [H_AR], "Y": [m("Median Effective Discount")]},
        title="متوسط الخصم الفعلي على العطور", order=("meas", F_, "Median Effective Discount", 2),
        objects={"labels": LBL, "dataPoint": house_colors(), "valueAxis": GRID_OFF}),
]))
pages.append(("مستوى السعر", [
 textbox(20, 10, 1240, 50, [("مستوى السعر: عساف يبيع أرخص من درعة، والماجد للعود بسعر درعة نفسه", 18, True)]),
 visual("tableEx", 20, 70, 1240, 300, {"Values": [H_AR, m("Perfumes Priced per ml"), m("Median Price per ml"), m("P25 Price per ml"), m("P75 Price per ml"),
        m("Median Price per ml after Bundles"), m("Median Price 100ml"), m("Share Under 1 SAR per ml")]}, title="مؤشرات سعر العطور حسب الشركة (ريال)",
        order=("meas", F_, "Median Price per ml", 1)),
 visual("hundredPercentStackedBarChart", 20, 385, 1240, 320, {"Category": [H_AR], "Series": [B_AR], "Y": [m("Perfumes Priced per ml")]},
        title="توزيع العطور على شرائح سعر المل", objects={"dataPoint": ppm_colors(), "legend": LEG_TOP}),
]))
pages.append(("علامات درعة", [
 textbox(20, 10, 1240, 50, [("العلامات الفرعية لعطور درعة: 13 من 19 علامة بين 1.0 و1.35 ريال للمل", 18, True)]),
 visual("clusteredBarChart", 650, 70, 610, 635, {"Category": [("col", F_, "sub_brand_ar")], "Y": [m("Median Price per ml")]},
        title="متوسط سعر المل لكل علامة (ريال)", filters=DER, order=("meas", F_, "Median Price per ml", 1),
        objects={"labels": LBL, "dataPoint": [{"properties": {"fill": solid("#1D4E89")}}], "valueAxis": GRID_OFF}),
 visual("tableEx", 20, 70, 610, 635, {"Values": [("col", F_, "sub_brand_ar"), m("Perfumes Priced per ml"), m("Median Price per ml"), m("Min Price per ml"), m("Max Price per ml"),
        m("Median Markdown Depth")]}, title="العلامات الفرعية: العدد والسعر", filters=DER, order=("meas", F_, "Median Price per ml", 1)),
]))
pages.append(("الخصومات", [
 textbox(20, 10, 1240, 50, [("الخصومات: معظم الشركات تخصم النصف على كل العطور تقريباً، والفرق في آلية العرض", 18, True)]),
 visual("hundredPercentStackedBarChart", 650, 70, 610, 330, {"Category": [H_AR], "Series": [("col", F_, "promo_ar")], "Y": [m("Perfumes")]},
        title="آلية العرض (حصة من عطور الشركة)", objects={"legend": LEG_TOP}),
 visual("clusteredBarChart", 20, 70, 610, 330, {"Category": [H_AR], "Y": [m("Median List Price per ml"), m("Median Price per ml")]},
        title="سعر المل قبل الخصم وبعده (ريال)", order=("meas", F_, "Median Price per ml", 1),
        objects={"labels": LBL, "legend": LEG_TOP, "valueAxis": GRID_OFF,
                 "dataPoint": [{"properties": {"fill": solid("#BFC3C9")}, "selector": {"metadata": f"{F_}.Median List Price per ml"}},
                               {"properties": {"fill": solid("#1D4E89")}, "selector": {"metadata": f"{F_}.Median Price per ml"}}]}),
 visual("tableEx", 20, 415, 1240, 290, {"Values": [H_AR, m("Perfumes"), m("Share Marked Down"), m("Share with Bundle Offer"), m("Median Markdown Depth"),
        m("Median Effective Discount"), m("Median List Price per ml"), m("Median Price per ml")]}, title="الشطب والباقات والخصم الفعلي",
        order=("meas", F_, "Median Effective Discount", 2)),
]))
pages.append(("المنهجية", [textbox(20, 10, 1240, 690, [
 ("المنهجية والحدود", 20, True),
 ("المصادر: المتاجر الإلكترونية الرسمية لدرعة وعساف والماجد للعود وإبراق (إبراهيم القرشي) والرصاصي وسويس أرابيان وأجمل والعربية للعود، جُمعت في 25 نوفمبر 2026. يقتصر التحليل على العطور.", 11, False),
 ("سعر المل = السعر ÷ الحجم لعطور البخاخ المفردة من 20 إلى 300 مل. الحجم من اسم المنتج أو صفحته، ولدرعة من رمز المنتج (تطابق 99.3% مع الحجم المذكور في 411 حالة).", 11, False),
 ("الخصم الفعلي: السعر المشطوب أو الشارة = الفرق بين السعرين؛ «3 بسعر 2» = 33%؛ «الثاني بنصف السعر» = 25%؛ وحين يجتمع الشطب والباقة يُحتسب الأثران معاً.", 11, False),
 ("الماجد للعود: السعر قبل الخصم مشتق من شارة النسبة (تحقق يدوي: 149 ريالاً مع 50% = 298 ريالاً).", 11, False),
 ("الحدود: لقطة واحدة من موسم عروض نوفمبر. سويس أرابيان تنشر الحجم لـ11 عطراً فقط. لم يُشمل عبدالصمد القرشي ودخون لتعذّر الوصول إلى متجريهما.", 11, False),
 ("إعداد: عثمان عبدالماجد", 11, True)])]))

sections = []
for i, (pname, vcs) in enumerate(pages):
    sections.append({"name": f"ReportSection{uuid.uuid4().hex[:18]}", "displayName": pname, "displayOption": 1,
                     "width": 1280, "height": 720, "ordinal": i, "config": "{}", "filters": "[]", "visualContainers": vcs})

report = {"config": json.dumps({"version": "5.43", "themeCollection": {}, "activeSectionIndex": 0,
                                "defaultDrillFilterOtherVisuals": True, "linguisticSchemaSyncVersion": 0,
                                "settings": {"useNewFilterPaneExperience": True, "allowChangeFilterTypes": True,
                                             "useStylableVisualContainerHeader": True, "exportDataMode": 1}}),
          "layoutOptimization": 0, "sections": sections, "filters": "[]"}
w(f"{RP}/report.json", json.dumps(report, ensure_ascii=False, indent=2))

for root, _, files in os.walk(OUT):
    for f in files: print(os.path.relpath(os.path.join(root, f), OUT))
