import httpx
import re
from bs4 import BeautifulSoup


class PhpWinScrape:
    def __init__(self):
        self.php_url = "https://windows.php.net/download/"
        self.php_min_version = "8.1.0"

    def scraper(self):
        bs = BeautifulSoup(httpx.get(self.php_url).text, "html.parser")
        php = []
        for h3 in bs.find_all("h3", class_="summary entry-title"):
            display = h3.text.strip()
            # Extract version number from display, e.g. "PHP 8.4 (8.4.10)" -> "8.4.10"
            m = re.search(r'\(([^)]+)\)', display)
            version = m.group(1) if m else display.split()[-1]
            block = h3.find_parent("div", class_="block")
            if not block:
                continue
            builds = []
            # Find all innerbox blocks for builds
            for innerbox in block.find_all("div", class_="innerbox"):
                # Get build info from h4 title, e.g. "VS16 x64 Non Thread Safe (2025-Jul-01 17:47:58)"
                h4 = innerbox.find("h4")
                if not h4:
                    continue
                build_title = h4.text.strip()
                vs = "vs17" if "vs17" in build_title.lower() else ("vs16" if "vs16" in build_title.lower() else None)
                arch = "x64" if "x64" in build_title.lower() else ("x86" if "x86" in build_title.lower() else None)
                nts = True if "non thread safe" in build_title.lower() else False
                # Now get links in this innerbox
                for a in innerbox.find_all("a"):
                    label = a.text.strip().lower()
                    if not self.filter_version(label):
                        continue
                    link = a.get("href")
                    if link and link.startswith("/"):
                        link = "https://windows.php.net" + link
                    if "debug pack" in label:
                        typ = "Debug Pack"
                    elif "zip" in label:
                        typ = "Release"
                    else:
                        typ = label
                    builds.append({
                        "arch": arch,
                        "nts": nts,
                        "vs": vs,
                        "type": typ,
                        "link": link
                    })
            if builds:
                php.append({
                    "version": version,
                    "display": display,
                    "builds": builds
                })
        return {"php": php}

    @staticmethod
    def filter_version(label):
        # Exclude source code, test package (phpt), 'no release', and development package
        label = label.lower()
        if (
            'source code' in label
            or 'tests package' in label
            or 'no release' in label
            or 'development package' in label
        ):
            return False
        return True

import json
with open("php.json", "w", encoding="utf-8") as f:
    json.dump(PhpWinScrape().scraper(), f, indent=2)
print("Saved to php.json")