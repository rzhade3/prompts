---
name: secondhand-goods-research
description: Researches secondhand/used goods online to find the best deals. Use when the user wants to buy something used or secondhand, compare prices on a used item, find deals on marketplaces (eBay, Craigslist, Facebook Marketplace, etc.), or work out a fair price for a pre-owned product. Trigger on mentions of buying "used", "secondhand", "pre-owned", or "refurbished" items.
allowed-tools: web_search web_fetch
---

# Secondhand Goods Research

Help the user buy a used item well: find current listings, establish a fair price for the condition, and flag scams — grounded in live web data, not guesses.

## Step 1 — Pin down the item

Get enough to search precisely. Ask only for what's missing and materially changes results:

- **Exact model** — brand, model number, generation/year, size/spec (e.g. "iPhone 13 Pro 256GB", not "an iPhone").
- **Budget and location** — location drives local marketplaces, shipping, and taxes; ask if the user wants local pickup vs. shipped.
- **Condition floor** — acceptable condition (e.g. "good or better", cosmetic wear OK, must be functional).

## Step 2 — Research

1. **Establish fair market value first.** Use `web_search` for the model plus terms like "used price", "resale value", or "sold listings" so you have a baseline before judging any individual listing. Note new price too, so the used discount is meaningful.
2. **Pull current listings** from the marketplaces that fit the item and location — general resale (eBay, Facebook Marketplace, Craigslist, OfferUp, Mercari) and category-specific sites where they beat the generalists (e.g. Swappa/Back Market for electronics, Poshmark/Depop/TheRealReal for fashion/luxury, Reverb for gear, Chrono24 for watches). Prefer **sold/completed** prices over asking prices — asking prices are aspirational.
3. **Open the most promising listings** with `web_fetch` to confirm condition, photos, price, and shipping before recommending them.

Model-specific gotchas to check: common failure points and known-bad model years, which trim/generation to prefer, and any authentication concerns for high-value or counterfeit-prone items (verify serials/receipts).

## Step 3 — Report

Always cite listing sources and prices. Keep it skimmable:

- **Summary** — the item, its typical used price range, and the new-vs-used gap.
- **Best deals** — top 3-5 current listings: price, condition, source, link, and a one-line "why this one".
- **Price range by condition** — fair, good, excellent (with sources).
- **Red flags to avoid** — scams and issues specific to this item (too-cheap outliers, no photos, off-platform payment, known defects).
- **Buying tips** — factor in shipping/fees for total cost, what to inspect, and how to verify authenticity.

## Guardrails

- Verify listings are current — check dates; used-goods listings go stale fast.
- Be skeptical of prices well below market; call out likely scams explicitly.
- Prioritize listings with detailed photos, described condition, and buyer protection.
