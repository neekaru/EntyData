# -*- coding: utf-8 -*-

import httpx
from bs4 import BeautifulSoup
from utils import VersionHandling

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
            v2tuple = VersionHandling.v2tuple
            return v2tuple(self.min_version.lstrip('v')) <= v2tuple(version.lstrip('v')) <= v2tuple(self.max_version.lstrip('v'))

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
        v2tuple = VersionHandling.v2tuple
        # Only include versions in the min-max range
        if text.startswith("v12."):
            version = text.split()[0]
            if v2tuple(self.min_version.lstrip('v')) <= v2tuple(version.lstrip('v')) <= v2tuple(self.max_version.lstrip('v')):
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


if __name__ == "__main__":
    import json
    
    scraper = HeldiSqlScrape()
    result = scraper.scrape()
    
    if result:
        v2tuple = VersionHandling.v2tuple
        
        # Create data for Windows only
        os_data = []
        windows_data = []
        
        # Sort versions in descending order and create entries for each download
        for v, downloads in sorted(result.items(), key=lambda x: v2tuple(x[0].lstrip('v')), reverse=True):
            version = v.lstrip('v')
            
            # Add 64-bit version if available
            if '64bit' in downloads:
                windows_data.append({
                    "version": version,
                    "gpg": "",  # HeidiSQL doesn't provide GPG signatures
                    "link": downloads['64bit']
                })
            
            # Add 32-bit version if available
            if '32bit' in downloads:
                windows_data.append({
                    "version": version,
                    "gpg": "",  # HeidiSQL doesn't provide GPG signatures
                    "link": downloads['32bit']
                })
        
        os_data.append({"os": "Windows", "data": windows_data})
        
        output = {"heidisql": os_data}
        
        # Save to JSON file like mysql.py does
        with open("assets/heldisql.json", "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        
        print("Saved all HeidiSQL download info to assets/heldisql.json")
        print(json.dumps(output, indent=2, ensure_ascii=False))
    else:
        print(json.dumps({"error": "No portable releases found or connection error."}, ensure_ascii=False))
