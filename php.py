import httpx
import re
from bs4 import BeautifulSoup


class PhpWinScrape:
    def __init__(self):
        self.php_url = "https://windows.php.net/download/"
        self.php_min_version = "8.1.0"

    def scraper(self):
        bs = BeautifulSoup(httpx.get(self.php_url).text, "html.parser")
        versions_data = []
        
        for h3 in bs.find_all("h3", class_="summary entry-title"):
            display = h3.text.strip()
            # Extract version number from display, e.g. "PHP 8.4 (8.4.10)" -> "8.4.10"
            m = re.search(r'\(([^)]+)\)', display)
            version = m.group(1) if m else display.split()[-1]
            block = h3.find_parent("div", class_="block")
            if not block:
                continue
            
            # Find both thread-safe and non-thread-safe builds for this version
            builds_found = []
            for innerbox in block.find_all("div", class_="innerbox"):
                h4 = innerbox.find("h4")
                if not h4:
                    continue
                build_title = h4.text.strip()
                vs = "vs17" if "vs17" in build_title.lower() else ("vs16" if "vs16" in build_title.lower() else None)
                arch = "x64" if "x64" in build_title.lower() else ("x86" if "x86" in build_title.lower() else None)
                nts = True if "non thread safe" in build_title.lower() else False
                
                # Look for Release zip files
                for a in innerbox.find_all("a"):
                    label = a.text.strip().lower()
                    if not self.filter_version(label):
                        continue
                    if "zip" in label and "debug pack" not in label:
                        link = a.get("href")
                        if link and link.startswith("/"):
                            link = "https://windows.php.net" + link
                        # Collect x64 builds (both thread-safe and non-thread-safe)
                        if arch == "x64":
                            builds_found.append({
                                "link": link,
                                "nts": nts,
                                "vs": vs
                            })
                            break
            
            # Add all found builds for this version
            for build in builds_found:
                versions_data.append({
                    "version": version,
                    "link": build["link"]
                })
        
        # Sort versions in descending order
        def version_key(item):
            v = item["version"]
            return tuple(int(x) if x.isdigit() else 0 for x in v.split(".")) if v else (0,)
        
        sorted_versions = sorted(versions_data, key=version_key, reverse=True)
        
        # Create data for Windows only
        os_data = []
        
        # Windows data (from scraped data)
        windows_data = []
        for item in sorted_versions:
            windows_data.append({
                "version": item["version"],
                "gpg": "",  # PHP Windows builds don't provide GPG signatures
                "link": item["link"]
            })
        os_data.append({"os": "Windows", "data": windows_data})
        
        return {"php": os_data}

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

if __name__ == "__main__":
    import json
    
    scraper = PhpWinScrape()
    result = scraper.scraper()
    
    # Save to JSON file like mysql.py does
    with open("assets/php.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    print("Saved all PHP download info to assets/php.json")
    print(json.dumps(result, indent=2, ensure_ascii=False))