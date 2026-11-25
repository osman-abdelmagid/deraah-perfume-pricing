"""Build one clean product table from the raw catalogue pulls of eight perfume houses (scraped 25 Nov 2026).

Run from the repository root:  python src/clean.py
Reads data/raw/*.tsv, writes data/clean/products.csv
"""
import os, re, pandas as pd, numpy as np
from pathlib import Path
os.chdir(Path(__file__).resolve().parents[1] / "data")

SCRAPE_DATE = "2026-11-25"
AR_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")

# ---------- helpers ----------
def norm(s):
    return str(s or "").translate(AR_DIGITS).replace("،", ",")

ML = r"(?:مل|ملي|ml|mL|ML|Ml)"
GR = r"(?:جم|جرام|غرام|غم|gm|GM|gms|g|G|grams)"

def parse_size(name, extra=""):
    t = norm(name) + " " + norm(extra)
    # multi-packs: "3 x 75مل", "2 x 50 ml", "3GM*8PCS"
    m = re.search(r"(\d+)\s*[x×*]\s*(\d+(?:\.\d+)?)\s*" + ML, t)
    if m:
        return float(m.group(2)), "ml", int(m.group(1))
    m = re.search(r"(\d+(?:\.\d+)?)\s*" + GR + r"\s*[x×*]\s*(\d+)", t)
    if m:
        return float(m.group(1)), "g", int(m.group(2))
    m = re.search(r"(\d+(?:\.\d+)?)\s*" + ML + r"(?![a-zA-Z])", t)
    if m:
        units = 1
        pk = re.search(r"(\d+)\s*(?:pcs|pieces|حبات|حبة|قطع|قطعة)", t, re.I)
        if pk: units = int(pk.group(1))
        return float(m.group(1)), "ml", units
    m = re.search(r"(\d+(?:\.\d+)?)\s*" + GR + r"(?![a-zA-Z])", t)
    if m:
        return float(m.group(1)), "g", 1
    return np.nan, None, 1

KW = [  # (category, regex on name) - order matters; used as fallback / override
    ("Mini / favors", r"توزيعات|tawziyat|giveaway|ميني|mini\b"),
    ("Body & hair mist", r"عطر الشعر|معطر الشعر|معطر شعر|معطر الجسم|الشعر و الجسم|الشعر والجسم|بخاخ الشعر|hair mist|body mist|body spray|معطر جسم|مفرش|bedspread"),
    ("Gift sets & bundles", r"طقم|بكج|باقة|\bset\b|gift|هدية|هدايا|بوكس|box|صندوق|توين|twin|\d+\s*[x×*]\s*\d+"),
    ("Incense burners", r"مبخر|مبخرة|mabkhara|burner|فواحة كهربائية|steamer"),
    ("Bakhoor & incense", r"بخور|معمول|bakhoor|bukhoor|incense|عود كمبودي|عود معتق|agarwood|كسرات|crew|mamul|oud wood|dakhoon|moattar|muri\b|معطر عود"),
    ("Perfume oil & dehn", r"دهن|dahan|dehn|زيت|oil|مخلط|mukhallat|خلطة"),
    ("Home fragrance", r"منزل|فواح|شمع|candle|diffuser|room spray|معطر جو"),
    ("Body care", r"لوشن|lotion|شاور|shower|زبدة|butter|كريم|cream|صابون|powder|بودرة"),
    ("Accessories & fashion", r"شماغ|shemagh|ساعة|watch|خاتم|ring\b|كبك|cufflink|نظار|sunglass|قلم|pen\b|مسبحة|rosary|محفظة|wallet|شنطة|حقيبة|bag|شماغ|غترة|عصا"),
    ("Perfume", r"عطر|perfume|parfum|edp|edt|بخاخ|spray|cologne|كولون|\d+\s*مل|\d+\s*ml"),
]

def kw_cat(name):
    n = norm(name).lower()
    for cat, rx in KW:
        if re.search(rx, n, re.I):
            return cat
    return "Other"

def gender_from(text):
    t = text.lower()
    if re.search(r"unisex|للجنسين|للحنسين|-un\b|unisex-", t): return "Unisex"
    if re.search(r"women|female|-f\b|نسائ|للنساء|her\b|for-her|gifts-women|حريم", t): return "Women"
    if re.search(r"\bmen\b|men-|-m\b|رجال|للرجال|him\b|for-him|gifts-men", t): return "Men"
    return "Not specified"

# ---------- Deraah ----------
def deraah():
    d = pd.read_csv("raw/deraah_raw.tsv", sep="\t", dtype=str)
    def cat(r):
        paths = [(r.url or "").rsplit("/", 1)[0]] + (r.categories or "").split("|")
        joined = " ".join(paths)
        for p in paths:
            if p.startswith("perfumes"): return "Perfume"
            if p.startswith("body-care/labeaute/eaudetoilet"): return "Perfume"
            if p.startswith("oud/oriental-perfumes"): return "Perfume"
            if re.match(r"oud/(oud-incense|crews|khinjar)", p): return "Bakhoor & incense"
            if re.match(r"oud/(oud-oil|mixtures)", p): return "Perfume oil & dehn"
            if re.match(r"oud/(bedspread|oud-hair|body-mist)", p) or re.match(r"body-care/labeaute/(body|hair)-fresheners", p): return "Body & hair mist"
            if p.startswith("oud/steamers"): return "Incense burners"
            if p.startswith("body-care"): return "Body care"
            if p.startswith("accessories") or p.startswith("watches") or p.startswith("women-acc"): return "Accessories & fashion"
            if p.startswith("waves"): return "Hair tools & care"
            if p.startswith("home-care"): return "Home fragrance"
            if p.startswith("gifts") or p.startswith("bundles"): return "Gift sets & bundles"
            if p.startswith("makeup"): return "Makeup"
            if p.startswith("distributions"): return "Mini / favors"
        return kw_cat(r.name)
    out = pd.DataFrame({
        "house": "Deraah",
        "product_id": d.pid,
        "sub_brand": d.brand.str.strip().str.upper().str.replace("`", "'", regex=False),
        "product_name": d.name,
        "price_sar": pd.to_numeric(d.price, errors="coerce"),
        "list_price_sar": pd.to_numeric(d.list_price, errors="coerce"),
        "rating": np.nan,
        "recent_views": np.nan,
        "recent_sold": np.nan,
        "promo_label": "",
        "source_categories": d.categories,
        "url": "https://www.deraahstore.com/ar_sa/" + d.url.fillna(""),
    })
    out["category"] = [cat(r) for r in d.itertuples()]
    # gift/set override when name says so and it sits outside accessories
    nm = out.product_name.fillna("")
    isset = nm.str.contains(r"طقم|بكج|باقة|بوكس|صندوق|\bset\b|مجموعة .*\d+\s*[x×]", case=False, regex=True)
    out.loc[isset & out.category.isin(["Perfume", "Other"]), "category"] = "Gift sets & bundles"
    mist = nm.str.contains(r"معطر مفارش|معطر جسم|معطر شعر|بخاخ الشعر|body mist|hair mist", case=False, regex=True)
    out.loc[mist, "category"] = "Body & hair mist"
    out["gender"] = [gender_from((r.url or "") + " " + (r.categories or "") + " " + (r.name or "")) for r in d.itertuples()]
    out["oriental_line"] = d.url.fillna("").str.startswith("oud/") | out.sub_brand.isin(["DERAAH OUD", "MAISON D'ORIENT", "INCENSE"])
    return out

# ---------- Salla stores (Arabian Oud, Ibraq) ----------
def salla(path, house, catmap, size_from_subtitle=False):
    d = pd.read_csv(path, sep="\t", dtype=str).fillna("")
    g = d.groupby("id")
    first = g.first()
    cats = g["cat"].agg(lambda s: "|".join(sorted(set(s))))
    paths = g["path"].agg(lambda s: "|".join(sorted(set(s))))
    sale = pd.to_numeric(first.sale_price, errors="coerce")
    pol = pd.to_numeric(first.price_or_list, errors="coerce")
    price = sale.where(sale.notna(), pol)
    lst = pol.where(sale.notna(), np.nan)
    out = pd.DataFrame({
        "house": house, "product_id": first.index, "sub_brand": house,
        "product_name": first["name"], "price_sar": price.values, "list_price_sar": lst.values,
        "rating": pd.to_numeric(first.rating, errors="coerce").values,
        "recent_views": np.nan, "recent_sold": np.nan,
        "promo_label": first.promo.values, "source_categories": cats.values, "url": first.url.values,
    }).reset_index(drop=True)
    def c(row):
        cs = row.source_categories
        for key, val in catmap:
            if key in cs: return val
        return kw_cat(row.product_name)
    out["category"] = out.apply(c, axis=1)
    kc = out.product_name.map(kw_cat)
    # name-level overrides for sets / minis / mists that live inside broad categories
    for k in ["Gift sets & bundles", "Body & hair mist", "Mini / favors"]:
        out.loc[(kc == k) & out.category.isin(["Perfume"]), "category"] = k
    out.loc[(kc == "Body & hair mist") & (out.category == "Home fragrance"), "category"] = "Body & hair mist"
    out["gender"] = [gender_from(a + " " + b) for a, b in zip(out.source_categories, paths.values)]
    out["oriental_line"] = out.product_name.str.contains(r"عود|oud|مسك|musk|عنبر|زعفران|بخور", case=False, regex=True)
    if size_from_subtitle:
        out["_size_extra"] = first.subtitle.str.replace("مل", " ml").values
    out.loc[out.promo_label.str.contains("تم الغاء", na=False), "promo_label"] = "Sold Out"
    return out

AO_MAP = [("هدايا", "Gift sets & bundles"), ("مبخرة", "Incense burners"), ("بخور", "Bakhoor & incense"),
          ("| العود", "Bakhoor & incense"), ("زيوت", "Perfume oil & dehn"), ("منزلية", "Home fragrance"),
          ("العطور", "Perfume")]
AS_MAP = [("اكسسوارات", "Accessories & fashion"), ("هدايا", "Gift sets & bundles"), ("عطور", "Perfume")]
IB_MAP = [("هدايا | إكسسوارات", "Accessories & fashion"), ("هدايا", "Gift sets & bundles"), ("توزيعات", "Mini / favors"),
          ("| البخور", "Bakhoor & incense"), ("| مباخر", "Incense burners"), ("زيوت", "Perfume oil & dehn"),
          ("منزلية", "Home fragrance"), ("الجسم والشعر", "Body & hair mist"), ("العطور", "Perfume")]

AM_MAP = [("عود وبخور", "Bakhoor & incense"), ("دهن العود", "Perfume oil & dehn"), ("زيوت عطرية", "Perfume oil & dehn"),
          ("المباخر", "Incense burners"), ("زيت جهاز تعطير", "Home fragrance"), ("أحجام صغيرة", "Mini / favors"),
          ("عطور", "Perfume"), ("المعطرات", "Home fragrance"), ("الهدايا", "Gift sets & bundles")]
RS_MAP = [("معطر منزلي", "Home fragrance"), ("عطور الجسم", "Body & hair mist"), ("عطور الشعر", "Body & hair mist"),
          ("صندوق الهديا", "Gift sets & bundles"), ("دهن", "Perfume oil & dehn"), ("بخور", "Bakhoor & incense"),
          ("عود", "Bakhoor & incense"), ("عطور رجالية", "Perfume"), ("عطور نسائية", "Perfume"), ("للحنسين", "Perfume")]

# ---------- Swiss Arabian (Shopify) ----------
def swiss():
    d = pd.read_csv("raw/swissarabian_raw.tsv", sep="\t", dtype=str).fillna("")
    price = pd.to_numeric(d.price.str.replace(",", ""), errors="coerce")
    cmp = pd.to_numeric(d["compare"].str.replace(",", ""), errors="coerce")
    lst = cmp.where(cmp > price + 0.01, np.nan)
    out = pd.DataFrame({
        "house": "Swiss Arabian", "product_id": d.pid.where(d.pid != "", d.handle), "sub_brand": "Swiss Arabian",
        "product_name": d.title, "price_sar": price, "list_price_sar": lst, "rating": np.nan,
        "recent_views": np.nan, "recent_sold": np.nan, "promo_label": d.labels, "source_categories": d.colls,
        "url": "https://ksa.swissarabian.com/products/" + d.handle,
    })
    def c(r):
        cs = r.colls.split("|"); k = kw_cat(r.title)
        if k in ("Gift sets & bundles", "Mini / favors", "Body & hair mist", "Incense burners"): return k
        if "gifting-collection" in cs: return "Gift sets & bundles"
        if "mini" in cs: return "Mini / favors"
        if "hair-mist" in cs: return "Body & hair mist"
        if any(x in cs for x in ["incense", "oud-collection"]): return "Bakhoor & incense"
        if any(x in cs for x in ["perfume-oil", "concentrated", "dehn-el-oud-collection", "malaki-collection"]): return "Perfume oil & dehn"
        if any(x in cs for x in ["perfumes", "men", "women", "unisex", "new-launches", "best-sellers"]): return "Perfume"
        return k
    out["category"] = [c(r) for r in d.itertuples()]
    out["gender"] = [gender_from(x) for x in d.colls.str.replace("|", " ")]
    out["oriental_line"] = out.product_name.str.contains(r"oud|musk|amber|bakhoor|incense|oudh", case=False, regex=True)
    sz = d["size"].str.split("/").str[0]
    out["_size_extra"] = d.handle.str.replace("-", " ") + " " + sz.str.replace("ml", " ml").str.replace("gm", " g")
    return out

# ---------- Ajmal (Shopify) ----------
def ajmal():
    d = pd.read_csv("raw/ajmal_raw.tsv", sep="\t", dtype=str).fillna("")
    price = pd.to_numeric(d.price.str.replace(",", ""), errors="coerce")
    cmp = pd.to_numeric(d["compare"].str.replace(",", ""), errors="coerce")
    lst = cmp.where(cmp > price + 0.01, np.nan)
    out = pd.DataFrame({
        "house": "Ajmal", "product_id": d.id, "sub_brand": "Ajmal", "product_name": d.title,
        "price_sar": price, "list_price_sar": lst, "rating": np.nan, "recent_views": np.nan, "recent_sold": np.nan,
        "promo_label": d.badge, "source_categories": d.colls,
        "url": "https://sa.ajmal.com/en/products/" + d.handle,
    })
    def c(r):
        cs = r.colls.split("|"); t = r.type.lower(); n = r.title
        k = kw_cat(n)
        if k in ("Gift sets & bundles", "Mini / favors", "Body & hair mist", "Incense burners"): return k
        if "gift-set" in cs: return "Gift sets & bundles"
        if "tawziyat" in cs: return "Mini / favors"
        if "hair-mist" in cs: return "Body & hair mist"
        if "crystal" in cs: return "Incense burners"
        if "powder" in cs: return "Body care"
        if any(x in cs for x in ["%D8%A8%D8%AE%D9%88%D8%B1-%D9%A1", "agarwood-1"]): return "Bakhoor & incense"
        if any(x in cs for x in ["perfume-oil", "d-oudh", "mukhallat"]) or "oil" in t or "dehn" in t: return "Perfume oil & dehn"
        if any(x in cs for x in ["perfumes", "men", "women", "unisex", "european"]) or "edp" in t or "parfum" in t: return "Perfume"
        return k
    out["category"] = [c(r) for r in d.itertuples()]
    out["gender"] = [gender_from(x) for x in d.colls.str.replace("|", " ")]
    out["oriental_line"] = ~d.colls.str.contains("european") & out.category.isin(["Perfume", "Perfume oil & dehn", "Bakhoor & incense"])
    out["_size_extra"] = d["size"] + " " + d["opts"]
    return out

# ---------- assemble ----------
df = pd.concat([deraah(), salla("raw/arabianoud_raw.tsv", "Arabian Oud", AO_MAP),
                salla("raw/ibraq_raw.tsv", "Ibraq (Ibrahim Al Qurashi)", IB_MAP), ajmal(),
                salla("raw/almajed_raw.tsv", "Al Majed Oud", AM_MAP), salla("raw/rasasi_raw.tsv", "Rasasi", RS_MAP), swiss(),
                salla("raw/assaf_raw.tsv", "Assaf", AS_MAP, size_from_subtitle=True)], ignore_index=True)
df["_size_extra"] = df.get("_size_extra", "").fillna("")
# Assaf uses "مجموعة"/"ثلاثية"/"Collection" or "+" for multi-bottle sets (unlike Deraah, where مجموعة names a line)
asset = (df.house == "Assaf") & df.product_name.fillna("").str.contains(r"^مجموعة|^المجموعة|ثلاثية|نخبة|collection|\+", case=False, regex=True)
df.loc[asset & (df.category == "Perfume"), "category"] = "Gift sets & bundles"
ibs = pd.read_csv("raw/ibraq_sizes.tsv", sep="\t", dtype=str).set_index("id").size_ml
m = df.house.str.startswith("Ibraq") & df.product_id.isin(ibs.index)
df.loc[m, "_size_extra"] = df.loc[m, "product_id"].map(ibs) + " ml"
ajs = pd.read_csv("raw/ajmal_sizes_supp.tsv", sep="\t", dtype=str).set_index("id")["size"]
m = (df.house == "Ajmal") & df.product_id.isin(ajs.index)
df.loc[m, "_size_extra"] = df.loc[m, "product_id"].map(ajs).str.replace("ml", " ml").str.replace("g", " g")
sz = [parse_size(n, e) for n, e in zip(df.product_name, df._size_extra)]
df["size_value"] = [s[0] for s in sz]
df["size_unit"] = [s[1] for s in sz]
df["units_in_pack"] = [s[2] for s in sz]
df = df.drop(columns="_size_extra")
# Deraah product codes end in a 3-digit size (validated: 99.3% match vs sizes stated in names, n=411)
isd = (df.house == "Deraah") & df.category.isin(["Perfume", "Body & hair mist", "Perfume oil & dehn"])
code = pd.to_numeric(df.product_id.str.replace("M-", "", regex=False).str.split("-").str[0].str[-3:], errors="coerce")
fill = isd & (code >= 20) & (df.size_value.isna() | (df.size_value < 20))
df.loc[fill, ["size_value", "size_unit", "units_in_pack"]] = [None, "ml", 1]
df.loc[fill, "size_value"] = code[fill]
df["size_source"] = np.where(fill, "product code", np.where(df.size_value.notna(), "name/page", ""))

# Al Majed: card shows sale price + "% off" badge; struck-through price sits in a span the reader skipped.
# Derive list price from the badge (spot-checked: 149 SAR with 50% badge -> 298 shown on site).
am = (df.house == "Al Majed Oud") & (df.list_price_sar.isna() | (df.list_price_sar <= df.price_sar))
pct = pd.to_numeric(df.promo_label.str.extract(r"(\d{2})\s*%")[0], errors="coerce")
df.loc[am & pct.notna(), "list_price_sar"] = (df.price_sar / (1 - pct / 100)).round(0)
df["list_price_source"] = np.where(am & pct.notna(), "derived from % badge", np.where(df.list_price_sar.notna(), "shown on site", ""))
# ---- AUDIT FIXES ----
# 1) sub-brand naming
df["sub_brand"] = df.sub_brand.replace({"PRIVATE": "DERAAH PRIVATE", "Q AND A": "Q&A"})
# 2) collapse size/colour variants listed as separate products (same house, name, size, price).
#    Deraah lists a master item ("M-" id) whose counters equal the sum of its variants -> keep master counters, else sum.
df["_nn"] = df.product_name.fillna("").str.replace(r"\s+", " ", regex=True).str.strip()
df["_m"] = df.product_id.astype(str).str.startswith("M-")
key = ["house", "_nn", "size_value", "price_sar"]
df["_g"] = df.groupby(key, dropna=False, sort=False).ngroup()
df["_n"] = df.groupby("_g")["_g"].transform("size")
mast = df[df._m].groupby("_g")[["recent_sold", "recent_views"]].max()
summ = df.groupby("_g")[["recent_sold", "recent_views"]].sum(min_count=1)
cats = df.groupby("_g").source_categories.agg(lambda x: "|".join(sorted(set("|".join(x.fillna("")).split("|")) - {""})))
df = df.sort_values(["_g", "_m"], ascending=[True, False]).drop_duplicates("_g", keep="first").set_index("_g")
for c in ["recent_sold", "recent_views"]:
    df[c] = mast[c].reindex(df.index).where(mast[c].reindex(df.index).notna(), summ[c].reindex(df.index))
df["source_categories"] = cats.reindex(df.index)
df["variants"] = df._n
df = df.reset_index(drop=True).drop(columns=["_n"])
df = df.drop(columns=["_nn", "_m"])
# 3) promotion mechanics -> one comparable "effective discount"
pl = df.promo_label.fillna("")
df["in_stock"] = ~pl.str.contains("Sold Out", case=False)
df["promo_label"] = pl.str.replace(r"\|?Sold Out\|?", "", regex=True).str.strip("|")
df["on_markdown"] = df.list_price_sar.notna() & (df.list_price_sar > df.price_sar + 0.5)
df["discount_pct"] = np.where(df.on_markdown, 1 - df.price_sar / df.list_price_sar, 0.0).round(3)

bundle_b2g1 = df.promo_label.fillna("").str.contains(r"2\s*\+\s*1|احصل على 1", regex=True)
bundle_2nd50 = df.promo_label.fillna("").str.contains("2nd at 50", case=False)
df["promo_type"] = np.select([df.on_markdown, bundle_b2g1, bundle_2nd50],
                             ["Price cut (struck-through / % badge)", "Buy 2 get 1 free", "2nd item at 50% off"], "No promotion")
df["effective_discount"] = np.select([df.on_markdown & bundle_b2g1, df.on_markdown, bundle_b2g1, bundle_2nd50],
                                     [1 - (1 - df.discount_pct) * 2 / 3, df.discount_pct, 1/3, 0.25], 0.0).round(3)
df.loc[df.on_markdown & bundle_b2g1, "promo_type"] = "Price cut + buy 2 get 1"
single_perfume = (df.category == "Perfume") & (df.size_unit == "ml") & (df.units_in_pack == 1) & df.size_value.between(20, 300)
df["price_per_ml"] = np.where(single_perfume, df.price_sar / df.size_value, np.nan).round(2)
df["list_price_per_ml"] = np.where(single_perfume & df.on_markdown, df.list_price_sar / df.size_value, np.nan).round(2)

bins = [0, 99.99, 199.99, 299.99, 499.99, 1e9]
labels = ["<100", "100-199", "200-299", "300-499", "500+"]
df["price_band_sar"] = pd.cut(df.price_sar, bins=bins, labels=labels).astype(str)
df["ppm_band"] = pd.cut(df.price_per_ml, bins=[0, 1, 2, 4, 7, 1e9], labels=["<1", "1-2", "2-4", "4-7", "7+"]).astype(str).replace("nan", "")
df["scrape_date"] = SCRAPE_DATE
df = df[df.price_sar.notna() & (df.price_sar > 1)].copy()  # drop unreadable zero prices (13 Assaf items)

cols = ["house", "sub_brand", "product_id", "product_name", "category", "gender", "oriental_line",
        "size_value", "size_unit", "units_in_pack", "size_source", "price_sar", "list_price_sar", "list_price_source", "on_markdown", "discount_pct", "promo_type", "effective_discount", "in_stock", "variants",
        "price_per_ml", "list_price_per_ml", "price_band_sar", "ppm_band", "rating",
        "promo_label", "source_categories", "url", "scrape_date"]
df = df[cols]
import os; os.makedirs("clean", exist_ok=True)
df.to_csv("clean/products.csv", index=False, encoding="utf-8-sig")
print(df.groupby("house").size())
print(pd.crosstab(df.category, df.house))
print(df[df.category == "Perfume"].groupby("house").agg(n=("price_sar", "size"), with_ppm=("price_per_ml", "count")))
