

import httpx
from bs4 import BeautifulSoup
import re
from utils import VersionHandling, SimpleVersion

class ComposerScrape:
    def __init__(self):
        self.url = "https://getcomposer.org/download/"
        self.base_url = "https://getcomposer.org"
        self.min_version = "2.2.0"
        self.max_version = "2.8.10"

    def scrape(self):
        response = httpx.get(self.url)
        bs = BeautifulSoup(response.text, "html.parser")
        releases = []
        table = bs.find('table')
        if table:
            for tr in table.find_all('tr'):
                tds = tr.find_all('a', href=True)
                if tds:
                    version = tds[0].text.strip()
                    # Skip RC and alpha versions
                    if re.search(r'-(RC|alpha)(\d*)$', version, re.IGNORECASE):
                        continue
                    # Only include versions in min-max range
                    v2tuple = VersionHandling.v2tuple
                    if version.startswith('2.') and v2tuple(self.min_version) <= v2tuple(version) <= v2tuple(self.max_version):
                        # Find date (second <td>), sha256sum (in <code>), and download link
                        tds_all = tr.find_all('td')
                        date = tds_all[1].text.strip() if len(tds_all) > 1 else ''
                        sha256sum = ''
                        code = tr.find('code', title='sha256 checksum')
                        if code:
                            sha256sum = code.text.strip()
                        # Download link
                        download_url = ''
                        for a in tds:
                            if a['href'].endswith('/composer.phar'):
                                download_url = self.base_url + a['href'] if a['href'].startswith('/') else a['href']
                                break
                        releases.append({
                            "version": version,
                            "date": date,
                            "sha256sum": sha256sum,
                            "download_url": download_url
                        })
        
        # Create data for each OS (Composer is cross-platform)
        os_data = []
        
        # Windows data
        windows_data = []
        for release in releases:
            windows_data.append({
                "version": release["version"],
                "gpg": "",  # Composer doesn't provide GPG signatures, but has sha256
                "link": release["download_url"]
            })
        os_data.append({"os": "Windows", "data": windows_data})
        
        # Linux data
        linux_data = []
        for release in releases:
            linux_data.append({
                "version": release["version"],
                "gpg": "",  # Composer doesn't provide GPG signatures, but has sha256
                "link": release["download_url"]
            })
        os_data.append({"os": "Linux", "data": linux_data})
        
        # macOS data
        macos_data = []
        for release in releases:
            macos_data.append({
                "version": release["version"],
                "gpg": "",  # Composer doesn't provide GPG signatures, but has sha256
                "link": release["download_url"]
            })
        os_data.append({"os": "macOS", "data": macos_data})
        
        return {"composer": os_data}

    def filter_versions(self, version):
        v2tuple = VersionHandling.v2tupl
        # Only include versions that start with '2.' and are not RC or alpha, and in min-max range
        if re.search(r'-(RC|alpha)(\d*)$', version, re.IGNORECASE):
            return False
        if version.startswith('2.') and v2tuple(self.min_version) <= v2tuple(version) <= v2tuple(self.max_version):
            return True
        return False

    
if __name__ == "__main__":
    import json
    
    scraper = ComposerScrape()
    result = scraper.scrape()
    
    # Save to JSON file like mysql.py does
    with open("assets/composer.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    print("Saved all Composer download info to assets/composer.json")
    print(json.dumps(result, indent=2, ensure_ascii=False))