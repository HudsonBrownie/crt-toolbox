# CRT Toolbox

A free reference site for CRT collectors and repair folks, built on data from [CRT Database](https://crtdatabase.com/).

**Live site:** https://hudsonbrownie.github.io/crt-toolbox/

## Tools

- **Lookup:** search 1,957 sets by brand, model, series, or chassis and open a full spec sheet (inputs, resolutions, sync, tube, mask, launch year, MSRP, power, and more).
- **Mod finder:** see a set's jungle IC and any documented mods (RGB via mux, direct, or CC; S-Video; component), then browse every other set on the same chip.
- **Parts:** cross-reference chassis, jungle IC, flyback, yoke, tube model, vertical output IC, and remote. Matching ignores dashes and spaces.
- **Twins:** sets that are likely the same TV or monitor under different model numbers (rebadges, retailer variants, OEM builds). Grouped when they match on screen size plus at least three of chassis, tube, flyback, yoke, and jungle IC.
- **Picker:** filter by size, weight, type, mask, power standard, launch year, and must-have inputs or resolutions to build a shortlist.
- **Collection:** mark sets as Own or Want and see totals by tube and brand. Saved in your browser, with export and import for backups.

Every part number on a spec sheet is clickable and jumps to all the other sets that share it.

## Data and license

All CRT data comes from [CRT Database](https://crtdatabase.com/) and is licensed
[CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/).
This is a free, non-commercial fan tool and is not affiliated with CRT Database.
This repo's data and derived files are shared under the same license.

Parts fields are only filled in for about half to 60% of sets. If a set is missing something, add it on that set's CRT Database page so everyone benefits.

## Files

- `index.html`: the whole site, data included. Served by GitHub Pages.
- `data/crtdb_scrape.py`: polite scraper (follows robots.txt, 3 second crawl delay, caches pages)
- `data/crts.json`: the scraped dataset
- `data/build_tools_data.py` and `data/template.html`: rebuild the site from fresh data

## Refreshing the data

```
cd data
py crtdb_scrape.py                    # updates crts.json (cached pages are reused)
py build_tools_data.py crts.json      # writes data.js
```

Paste `data.js` into `template.html` in place of `/*DATA*/`, set `/*FLAGS*/` to `window.SHOW_IMG=true;`, and save the result as `index.html`.

## Related

- [CRTdle](https://hudsonbrownie.github.io/CRTdle/): a daily guessing game built on the same data.
