#!/usr/bin/env python3
"""
CRT Database scraper for a CRT guessing game.

Plays by crtdatabase.com's posted robots.txt:
  - checks every URL against robots.txt before fetching
  - honors Crawl-delay (3s) between live requests
  - only visits the brand index, brand pages, and individual CRT pages
  - never touches /search, /crt-discovery-tool, submissions, etc.

Caches every page it downloads in ./crtdb_cache so you can stop/restart
(Ctrl+C is safe) without re-hitting the site.

Usage:
  pip install requests beautifulsoup4
  python crtdb_scrape.py --test https://crtdatabase.com/crts/sony/sony-pvm-2950q
  python crtdb_scrape.py --limit 50          # quick trial run
  python crtdb_scrape.py                     # full run (~2-2.5 hours)

Output: crts.json

Data from CRT Database (crtdatabase.com), licensed CC BY-NC-SA 4.0.
Keep any game built from it free and credited.
"""

import argparse
import hashlib
import json
import os
import re
import sys
import time
import urllib.robotparser
from urllib.parse import urljoin, urlparse

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    sys.exit("Missing packages. Run:  pip install requests beautifulsoup4")

BASE = "https://crtdatabase.com"
UA = "CRTdle-fan-game-scraper/1.0 (non-commercial; honors robots.txt)"
CACHE_DIR = "crtdb_cache"
OUT_FILE = "crts.json"

session = requests.Session()
session.headers["User-Agent"] = UA

robots = urllib.robotparser.RobotFileParser()
robots.set_url(BASE + "/robots.txt")
# Fetch robots.txt with our own session (the stdlib reader uses a default
# user agent some hosts reject, which makes it silently disallow everything).
try:
    _r = session.get(BASE + "/robots.txt", timeout=30)
except requests.RequestException as e:
    sys.exit(f"Could not fetch robots.txt: {e}")
if _r.status_code != 200:
    sys.exit(f"robots.txt returned HTTP {_r.status_code}; stopping to be safe.")
robots.parse(_r.text.splitlines())
print("robots.txt rules:\n  " + "\n  ".join(l for l in _r.text.splitlines() if l.strip()))
DELAY = robots.crawl_delay(UA) or robots.crawl_delay("*") or 3
DELAY = max(float(DELAY), 3.0)
_last_live = 0.0


def fetch(url):
    """Return HTML for url, from cache if possible, else politely from the site."""
    global _last_live
    if not robots.can_fetch(UA, url):
        print(f"  skip (robots.txt): {url}")
        return None
    os.makedirs(CACHE_DIR, exist_ok=True)
    key = hashlib.sha1(url.encode()).hexdigest()
    path = os.path.join(CACHE_DIR, key + ".html")
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return f.read()
    wait = DELAY - (time.time() - _last_live)
    if wait > 0:
        time.sleep(wait)
    for attempt in range(3):
        try:
            r = session.get(url, timeout=30)
            _last_live = time.time()
            if r.status_code == 429 or r.status_code >= 500:
                backoff = 30 * (attempt + 1)
                print(f"  {r.status_code} on {url}, backing off {backoff}s")
                time.sleep(backoff)
                continue
            if r.status_code != 200:
                print(f"  {r.status_code}: {url}")
                return None
            with open(path, "w", encoding="utf-8") as f:
                f.write(r.text)
            return r.text
        except requests.RequestException as e:
            print(f"  error {e} on {url}, retrying")
            time.sleep(15)
    return None


# ---------- discovery ----------

BRAND_RE = re.compile(r"^/crts/[^/]+/?$")
CRT_RE = re.compile(r"^/crts/[^/]+/[^/]+/?$")


def brand_pages():
    html = fetch(BASE + "/")
    soup = BeautifulSoup(html, "html.parser")
    urls = []
    for a in soup.find_all("a", href=True):
        p = urlparse(urljoin(BASE, a["href"]))
        if p.netloc != "crtdatabase.com":
            continue
        if BRAND_RE.match(p.path) or (p.path == "/taxonomy" and "manufacturer" in p.query):
            u = urljoin(BASE, p.path + ("?" + p.query if p.query else ""))
            if u not in urls:
                urls.append(u)
    return urls


def crt_pages(brand_url):
    html = fetch(brand_url)
    if not html:
        return []
    soup = BeautifulSoup(html, "html.parser")
    urls = []
    for a in soup.find_all("a", href=True):
        p = urlparse(urljoin(BASE, a["href"]))
        if p.netloc == "crtdatabase.com" and CRT_RE.match(p.path):
            u = BASE + p.path.rstrip("/")
            if u not in urls:
                urls.append(u)
    return urls


# ---------- parsing ----------

def cell_values(td):
    links = [a.get_text(" ", strip=True) for a in td.find_all("a")]
    links = [t for t in links if t]
    if links:
        return links
    txt = td.get_text(" ", strip=True)
    return [txt] if txt else []


def parse_specs(soup):
    specs = {}
    for tr in soup.find_all("tr"):
        cells = tr.find_all(["td", "th"])
        if len(cells) < 2:
            continue
        label = cells[0].get_text(" ", strip=True).rstrip(":").strip()
        if not label or label.lower() == "specifications":
            continue
        vals = cell_values(cells[1])
        if vals:
            specs[label] = vals
    # fallback for definition-list layouts
    if not specs:
        for dt in soup.find_all("dt"):
            dd = dt.find_next_sibling("dd")
            if dd:
                specs[dt.get_text(strip=True).rstrip(":")] = cell_values(dd)
    return specs


def first_num(vals):
    for v in vals or []:
        m = re.search(r"(\d+(?:\.\d+)?)", v)
        if m:
            return float(m.group(1))
    return None


def parse_crt(url):
    html = fetch(url)
    if not html:
        return None
    soup = BeautifulSoup(html, "html.parser")
    h1 = soup.find("h1")
    name = h1.get_text(" ", strip=True) if h1 else url.rsplit("/", 1)[-1]
    specs = parse_specs(soup)
    if not specs:
        return None
    og = soup.find("meta", property="og:image")
    g = lambda k: specs.get(k, [])
    tube = g("Tube")
    weight_txt = " ".join(g("Weight"))
    wm = re.search(r"(\d+(?:\.\d+)?)\s*lbs", weight_txt)
    return {
        "id": url.rsplit("/", 1)[-1],
        "name": name,
        "url": url,
        "brand": (g("Brand") or g("Manufacturer") or [""])[0],
        "series": (g("Series") or [""])[0],
        "model": (g("Model") or [""])[0],
        "size_in": first_num(g("Viewable Size")),
        "aspect": (g("Aspect") or [""])[0],
        "inputs": g("Input Signals"),
        "sync": g("Sync"),
        "resolutions": g("Native Resolutions"),
        "tvl": first_num(g("Linecount")),
        "h_scan": g("Horizontal Scan Range"),
        "v_scan": g("Vertical Scan Range"),
        "formats": g("Formats"),
        "tube_brand": tube[0] if tube else "",
        "tube_model": tube[1] if len(tube) > 1 else "",
        "mask": (g("Mask") or [""])[0],
        "deflection": first_num(g("Deflection")),
        "tint": (g("Tint") or [""])[0],
        "weight_lbs": float(wm.group(1)) if wm else None,
        "application": (g("Application") or [""])[0],
        "country": (g("Country of Manufacture") or [""])[0],
        "mounting": g("Mounting"),
        "tags": g("Tag"),
        "image": og["content"] if og and og.get("content") else "",
        "raw": specs,
    }


# ---------- main ----------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, help="stop after N CRT pages")
    ap.add_argument("--test", help="parse one CRT page URL and print it")
    args = ap.parse_args()

    if args.test:
        print(json.dumps(parse_crt(args.test), indent=2))
        return

    print(f"Crawl delay: {DELAY}s")
    brands = brand_pages()
    print(f"{len(brands)} brand pages")
    crt_urls = []
    for i, b in enumerate(brands, 1):
        found = crt_pages(b)
        crt_urls += [u for u in found if u not in crt_urls]
        print(f"[brand {i}/{len(brands)}] {b} -> {len(found)} (total {len(crt_urls)})")
        if args.limit and len(crt_urls) >= args.limit:
            break
    if args.limit:
        crt_urls = crt_urls[: args.limit]

    results = []
    try:
        for i, u in enumerate(crt_urls, 1):
            d = parse_crt(u)
            if d:
                results.append(d)
            if i % 25 == 0 or i == len(crt_urls):
                print(f"[crt {i}/{len(crt_urls)}] parsed {len(results)}")
                with open(OUT_FILE, "w", encoding="utf-8") as f:
                    json.dump(results, f, indent=1)
    except KeyboardInterrupt:
        print("\nStopped. Progress is cached; rerun to resume.")
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=1)
    print(f"Wrote {len(results)} CRTs to {OUT_FILE}")


if __name__ == "__main__":
    main()
