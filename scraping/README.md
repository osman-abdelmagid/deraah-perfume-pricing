# How the stores were captured

All eight stores were read on 25 November 2026 from their public category pages, in a normal browser session, one category at a time. No login, no private API. Each capture was saved and turned into a TSV in `data/raw/` (`extract_dump.py` does that conversion).

| House | Store | Platform | How the product tiles were read |
|---|---|---|---|
| Deraah | deraahstore.com/ar_sa | Salesforce Commerce Cloud | Category pages fetched with a large page size (`?sz=`) and parsed: `.product[data-pid]` tiles, sale price in `.b-price__type-sales .value[content]`, list price in `.b-price__type-list .value`, sub-brand in `.tile-body__brand`. Product codes end in the bottle size (see main README) |
| Assaf | 3saf.com | Salla | `salla_scrape.js` |
| Al Majed Oud | sa.almajed4oud.com | Salla | `salla_scrape.js`. The card shows a % badge, not the old price |
| Ibraq (Ibrahim Al Qurashi) | saudi.ibraqperfumes.com | Salla | `salla_scrape.js`; sizes missing from names were read from product pages (`ibraq_sizes.tsv`) |
| Rasasi | store.rasasi.com.sa | Salla | `salla_scrape.js`; offers are "buy 2 get 1", read from the promotion label |
| Arabian Oud | sa.arabianoud.com | Salla | `salla_scrape.js` |
| Ajmal | Ajmal Saudi online store | Shopify | Collection pages parsed from `marmeto-product-card`; sizes missing from names read from product pages (`ajmal_sizes_supp.tsv`) |
| Swiss Arabian | Swiss Arabian Saudi online store | Shopify | Collection pages parsed from `.product-block` |

`salla_scrape.js` is pasted into the browser console on a Salla category page. It scrolls until no new products load, then returns one tab-separated line per product card: id, name, sale price, list price, rating, promotion label, subtitle, URL.

Deraah's tiles also show "viewed recently" and "sold recently" counters. They were captured but are not used: the time window is not stated and no competitor shows them. They are removed from `data/raw/deraah_raw.tsv`.
