"""Perfume price and discount metrics, plus the tables Power BI reads.

Run from the repository root:  python src/metrics.py
Reads data/clean/products.csv; writes outputs/metrics.json and data/powerbi/*.csv
"""
import os, pandas as pd, numpy as np, json
from pathlib import Path
os.chdir(Path(__file__).resolve().parents[1])
d=pd.read_csv('data/clean/products.csv')
H=['Deraah','Assaf','Al Majed Oud','Ibraq (Ibrahim Al Qurashi)','Rasasi','Swiss Arabian','Ajmal','Arabian Oud']
P=d[d.category=='Perfume'].copy()
bund=np.where(P.promo_type.str.contains('buy 2 get 1',case=False),1/3,np.where(P.promo_type.str.contains('2nd item'),.25,0))
P['eff_price_per_ml']=(P.price_per_ml*(1-bund)).round(2)
P['bundle']=bund>0
pm=P[P.price_per_ml.notna()]
M={}
M['n_perf']=len(P); M['perf_n']=P.groupby('house').size().reindex(H).to_dict(); M['ppm_n']=pm.groupby('house').size().reindex(H).fillna(0).astype(int).to_dict()
g=pm.groupby('house').price_per_ml
M['ppm']={h:{'med':round(g.median()[h],2),'p25':round(g.quantile(.25)[h],2),'p75':round(g.quantile(.75)[h],2)} for h in H}
M['eff_ppm']=pm.groupby('house').eff_price_per_ml.median().reindex(H).round(2).to_dict()
M['list_ppm']=pm.groupby('house').list_price_per_ml.median().reindex(H).round(2).to_dict()
bands=pd.cut(pm.price_per_ml,[0,1,2,4,1e9],right=False,labels=['<1','1-2','2-4','4+'])
M['bands']=pd.crosstab(pm.house,bands,normalize='index').reindex(H).round(3).to_dict(orient='index')
M['under1']={h:M['bands'][h]['<1'] for h in H}
M['med_price_100']=pm[pm.size_value==100].groupby('house').price_sar.median().reindex(H).to_dict()
M['share_promo']=P.groupby('house').apply(lambda x:(x.effective_discount>0).mean()).reindex(H).round(3).to_dict()
M['share_markdown']=P.groupby('house').on_markdown.mean().reindex(H).round(3).to_dict()
M['share_bundle']=P.groupby('house').bundle.mean().reindex(H).round(3).to_dict()
M['eff_disc']=P.groupby('house').effective_discount.median().reindex(H).round(3).to_dict()
md=P[P.on_markdown]
M['md_disc']=md.groupby('house').discount_pct.median().reindex(H).round(3).to_dict()
dd=pd.cut(P.effective_discount,[-.01,0.001,.3,.45,.55,1],labels=['none','<30','30-45','45-55','55+'])
M['disc_dist']=pd.crosstab(P.house,dd,normalize='index').reindex(H).round(3).to_dict(orient='index')
D=pm[pm.house=='Deraah']
M['deraah_above_assaf']=round((D.price_per_ml>M['ppm']['Assaf']['med']).mean(),3)
M['deraah_list_over_assaf_sale']=None
sb=D.groupby('sub_brand').price_per_ml.agg(['size','median','min','max']).query('size>=4').sort_values('median').round(2)
M['subbrands']=sb.to_dict(orient='index'); M['n_labels']=int(D.sub_brand.nunique()); M['n_labels4']=len(sb)
M['n_band']=int(((sb['median']>=1.0)&(sb['median']<=1.35)).sum())
# Deraah: share of perfumes where list price >= 2x sale
M['deraah_half']=round(((P.house=='Deraah')&(P.discount_pct.between(.45,.55))).sum()/ (P.house=='Deraah').sum(),3)
json.dump(M,open('outputs/metrics.json','w'),ensure_ascii=False,indent=1,default=float)
# ---------- Power BI tables ----------
cols=['house','sub_brand','product_id','product_name','gender','size_value','size_unit','units_in_pack','price_sar','list_price_sar','on_markdown','discount_pct','promo_type','effective_discount','price_per_ml','list_price_per_ml','eff_price_per_ml','ppm_band','price_band_sar','url','scrape_date']
f=P[cols].copy()
f['ppm_band']=f.ppm_band.replace({'4-7':'4+','7+':'4+'})
PA={'Price cut (struck-through / % badge)':'سعر مشطوب','Price cut + buy 2 get 1':'سعر مشطوب + ٣ بسعر ٢','Buy 2 get 1 free':'٣ بسعر ٢','2nd item at 50% off':'الثاني بنصف السعر','No promotion':'بلا عرض'}
f['promo_ar']=f.promo_type.map(PA)
f['is_bundle']=f.promo_type.isin(['Price cut + buy 2 get 1','Buy 2 get 1 free','2nd item at 50% off'])
SB={"AL GAZIRA":"الجزيرة","H2O":"إتش تو أو","RING":"رينج","GINGLE":"جينجل","ONE LOVE":"ون لوف","MAIOS":"مايوس","LABEAUTE":"لابوتيه","LINK":"لينك","POUR MOI":"بور موا","V.S":"في إس","Q&A":"كيو آند إيه","CAGE":"كيج","PROUD":"براود","JADDID":"جديد","DERAAH OUD":"درعة عود","PAPILLON":"بابيون","DERAAH PRIVATE":"درعة برايفت","MAISON D'ORIENT":"ميزون دورينت","MON BOUQUET":"مون بوكيه","DERAAH":"درعة"}
f['sub_brand_ar']=f.sub_brand.map(SB).fillna(f.sub_brand)
f.to_csv('data/powerbi/fact_perfumes.csv',index=False,encoding='utf-8-sig')
pd.DataFrame({'ppm_band':['<1','1-2','2-4','4+'],'ppm_band_ar':['أقل من 1','1 إلى 2','2 إلى 4','4 فأكثر'],'ppm_sort':[1,2,3,4]}).to_csv('data/powerbi/dim_ppm_band.csv',index=False,encoding='utf-8-sig')
print(f"{len(P)} perfumes; Deraah median {M['ppm']['Deraah']['med']} SAR/ml, Assaf {M['ppm']['Assaf']['med']}")
