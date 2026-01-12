import re
import json
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup


def same_domain(a, b):
    return urlparse(a).netloc == urlparse(b).netloc


def is_html(resp):
    return "text/html" in resp.headers.get("content-type", "")


def normalize(u):
    u = u.split("#")[0]
    return re.sub(r"/+$", "/", u)


def crawl(start_url, max_pages=200):
    start_url = normalize(start_url)
    q = [start_url]
    seen = set()

    while q and len(seen) < max_pages:
        url = normalize(q.pop(0))
        if url in seen:
            continue
        seen.add(url)

        r = requests.get(url, timeout=30)
        if r.status_code != 200 or not is_html(r):
            continue

        soup = BeautifulSoup(r.text, "html.parser")
        yield url, r.text, (
            soup.title.string.strip() if soup.title and soup.title.string else ""
        )

        for a in soup.select("a[href]"):
            href = a.get("href")
            if not href:
                continue
            nxt = normalize(urljoin(url, href))
            if same_domain(start_url, nxt):
                q.append(nxt)


if __name__ == "__main__":
    start = "https://gta-fcba.incovar.com/Incotec/Incovar/Help/fr-FR/PORTAIL/topics/LOGIN.html"
    out_path = "data/raw/pages.jsonl"
    with open(out_path, "w", encoding="utf-8") as f:
        for url, html, title in crawl(start):
            f.write(
                json.dumps(
                    {"url": url, "title": title, "html": html}, ensure_ascii=False
                )
                + "\n"
            )
            print(url)
