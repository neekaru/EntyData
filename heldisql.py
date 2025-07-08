# -*- coding: utf-8 -*-
import httpx
from bs4 import BeautifulSoup

class HeldiSqlScrape:
    def __init__(self):
        self.url = "https://www.heidisql.com/download.php#"
        self.min_version = "v12.6" # minimum version (inclusive)
        self.max_version = "v12.11" # maximum version (inclusive)
        self.base_url = "https://www.heidisql.com"

    def get_portable_links(self, releases):
        """
        Given a list of releases (li tags from oldreleases), return a dict of version -> { '32bit': url, '64bit': url }
        Only for versions between self.min_version and self.max_version (inclusive), and only Portable links.
        """
        version_map = {}
        import re
        def version_in_range(version):
            def v2tuple(v):
                return tuple(map(int, v.lstrip('v').split('.')))
            return v2tuple(self.min_version) <= v2tuple(version) <= v2tuple(self.max_version)

        for li in releases:
            li_text = li.get_text()
            m = re.search(r'(v\d+\.\d+)', li_text)
            if not m:
                continue
            version = m.group(1)
            if not version_in_range(version):
                continue
            links = li.find_all('a', class_='download-link')
            for link in links:
                href = link.get('href', '')
                if not href.startswith('http'):
                    href = self.base_url + href
                link_text = link.get_text(strip=True)
                if '32' in link_text and 'Portable' in li_text:
                    if version not in version_map:
                        version_map[version] = {}
                    version_map[version]['32bit'] = href
                elif '64' in link_text and 'Portable' in li_text:
                    if version not in version_map:
                        version_map[version] = {}
                    version_map[version]['64bit'] = href
        return version_map

    def filter_version(self, text):
        # Only include versions in the min-max range
        if text.startswith("v12."):
            version = text.split()[0]
            def v2tuple(v):
                return tuple(map(int, v.lstrip('v').split('.')))
            if v2tuple(self.min_version) <= v2tuple(version) <= v2tuple(self.max_version):
                return True
        return False

    def scrape(self):
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Pragma': 'no-cache',
            'Referer': 'https://www.google.com/',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1',
            'Sec-GPC': '1',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
        }
        try:
            with httpx.Client(headers=headers, http2=True) as session:
                response = session.get(self.url)
                bs = BeautifulSoup(response.text, "html.parser")
                # Only focus on oldreleases section for v12.11 to v12.6 Portable links
                oldreleases = bs.find('ul', class_='oldreleases')
                # print("[DEBUG] oldreleases:", oldreleases)
                if oldreleases:
                    version_links = self.get_portable_links(oldreleases.find_all('li'))
                    # print("[DEBUG] version_links:", version_links)
                    return version_links
                else:
                    return {}
        except httpx.ConnectError as e:
            print(f"Connection error: {e}")
            return None

# print("[DEBUG] Starting HeldiSqlScrape...")
# print("[DEBUG] Initializing HeldiSqlScrape instance...")
# print("[DEBUG] Scraping HeldiSql releases...")
# print(HeldiSqlScrape().scrape())


# Scrape and print only v12.11 to v12.6 Portable links from previous releases as JSON
import json
result = HeldiSqlScrape().scrape()
if result:
    # Output as JSON: { version: { '32bit': url, '64bit': url } }
    print(json.dumps(result, indent=2, ensure_ascii=False))
else:
    print(json.dumps({"error": "No portable releases found or connection error."}, ensure_ascii=False))
with open("test2.txt", "w", encoding="utf-8") as f:
    f.write(str(result))
