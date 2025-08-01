
import httpx
from bs4 import BeautifulSoup
import re
from utils import VersionHandling
import json
import os

class ApacheScrape:
    def __init__(self):
        self.url = "https://archive.apache.org/dist/httpd/"
        self.changelog_url = "https://www.apachelounge.com/Changelog-2.4.html"
        self.min_version = "2.4.51"
        self.max_version = "2.4.65"
        self.last_v16_version = "2.4.57"

    def date_converter(self, text):
        """
        Extracts date from a string like "07-February-2025 Changes with Apache 2.4.63 - Announcement"
        and converts it to YYMMDD format, e.g., "250207".
        """
        months = {
            "January": "01", "February": "02", "March": "03", "April": "04",
            "May": "05", "June": "06", "July": "07", "August": "08",
            "September": "09", "October": "10", "November": "11", "December": "12"
        }
        match = re.match(r"(\d{2})-([A-Za-z]+)-(\d{4})", text)
        if match:
            day, month_str, year = match.groups()
            month = months.get(month_str, "01")
            return year[2:] + month + day
        return None
    
    def remove_date_size(self, text):
        """
        Removes trailing date/size info from a line, e.g.,
        'httpd-2.4.63.tar.bz2                2025-01-23 20:00  7.2M' -> 'httpd-2.4.63.tar.bz2'
        """
        # Remove everything from the first date pattern to the end
        return re.sub(r'\s+\d{4}-\d{2}-\d{2} \d{2}:\d{2}\s+\S+$', '', text.strip())
    
    def filter_version(self, text):
        """
        Exclude unwanted entries based on specific keywords, file extensions, [TXT] labels.
        """
        exclude_keywords = [
            "Announcement", "CHANGES", "CURRENT-IS-", "KEYS", "META",
            ".asc", ".tar.gz", ".Z", ".tar_Z.asc", "os2.zip", ".md5",
            "-src", "sha1", "-beta", "-alpha", "-deps", "-netware",
            "apache", "[TXT]", ".sha256", ".png", ".sha512"
        ]
        if "httpd" not in text.lower():
            return False
        for keyword in exclude_keywords:
            if keyword.lower() in text.lower():
                return False
        return True

    def version_in_range(self, version):
        v2tuple = VersionHandling.v2tuple
        return v2tuple(self.min_version) <= v2tuple(version) <= v2tuple(self.max_version)

    def scrape_version(self, html=None):
        # If html is provided, use it (for testing); otherwise fetch from the web
        if html is None:
            response = httpx.get(self.url)
            html = response.text
        bs = BeautifulSoup(html, "html.parser")
        results = []
        for pre in bs.find_all('pre'):
            for line in pre.text.splitlines():
                if self.filter_version(line):
                    clean = self.remove_date_size(line)
                    # Extract version from filename
                    m = re.search(r'httpd-(2\.4\.\d+)\.tar\.bz2', clean)
                    if m:
                        version = m.group(1)
                        if self.version_in_range(version):
                            # Strip .tar.bz2 from the filename
                            clean = re.sub(r'\.tar\.bz2$', '', clean)
                            results.append(clean)
            return results
    

    def scrape_changelog(self, html=None):
        """Scrape Apache versions and dates from changelog HTML."""
        header = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3",
            "referer": "https://www.apachelounge.com/viewtopic.php?p=43274",
            "accept-language": "en-US,en;q=0.8",
            "cache-control": "max-age=0",
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
            "upgrade-insecure-requests": "1",
            "priority": "u=0, i"
        }
        if html is None:
            rs = httpx.get(self.changelog_url, headers=header)
            html = rs.text
            print("[DEBUG] changelog HTML preview:")
            print(html[:500])
        print(f"[DEBUG] changelog HTML length: {len(html)}")
        bs = BeautifulSoup(html, "html.parser")
        results = []
        match_count = 0
        # Find all <b> tags with text like '07-October-2021 Changes with Apache 2.4.51'
        for b in bs.find_all('b'):
            text = b.get_text(strip=True)
            # Match pattern: '07-October-2021 Changes with Apache 2.4.51'
            m = re.match(r"(\d{2}-[A-Za-z]+-\d{4}) Changes with Apache (2\.4\.\d+)", text)
            if m:
                match_count += 1
                date_str, version = m.groups()
                if self.version_in_range(version):
                    date_conv = self.date_converter(date_str)
                    results.append({"version": version, "date": date_conv})
        print(f"[DEBUG] changelog matches found: {match_count}, in-range: {len(results)}")
        return results


    def scrape(self, version_list=None, changelog_list=None):
        """
        Generate download links for each version using scrape_version and scrape_changelog.
        Returns data in mysql.py format with multiple entries per version (like php.py).
        """
        v2tuple = VersionHandling.v2tuple
        # If not provided, get from methods
        if version_list is None:
            version_list = self.scrape_version()
        if changelog_list is None:
            changelog_list = self.scrape_changelog()

        # Build a map from version to date code
        version_date = {entry['version']: entry['date'] for entry in changelog_list if entry.get('date')}

        # Collect all builds for all versions
        builds_data = []
        for vstr in version_list:
            # vstr is like 'httpd-2.4.63', extract version
            m = re.match(r'httpd-(2\.4\.\d+)', vstr)
            if not m:
                continue
            version = m.group(1)
            date_code = version_date.get(version)
            if not date_code:
                continue
            
            # VS17 builds (always available)
            builds_data.append({
                "version": version,
                "link": f"https://www.apachelounge.com/download/VS17/binaries/httpd-{version}-{date_code}-win64-VS17.zip"
            })
            builds_data.append({
                "version": version,
                "link": f"https://www.apachelounge.com/download/VS17/binaries/httpd-{version}-{date_code}-win32-VS17.zip"
            })
            
            # VS16 builds (only for versions <= last_v16_version)
            if v2tuple(version) <= v2tuple(self.last_v16_version):
                builds_data.append({
                    "version": version,
                    "link": f"https://www.apachelounge.com/download/vs16/binaries/httpd-{version}-{date_code}-win64-vs16.zip"
                })
                builds_data.append({
                    "version": version,
                    "link": f"https://www.apachelounge.com/download/vs16/binaries/httpd-{version}-{date_code}-win32-vs16.zip"
                })
        
        # Sort builds by version in descending order
        def version_key(item):
            v = item["version"]
            return tuple(int(x) if x.isdigit() else 0 for x in v.split(".")) if v else (0,)
        
        sorted_builds = sorted(builds_data, key=version_key, reverse=True)
        
        # Create data for Windows only (Apache builds are Windows-specific from ApacheLounge)
        os_data = []
        
        # Windows data (all builds)
        windows_data = []
        for build in sorted_builds:
            windows_data.append({
                "version": build["version"],
                "gpg": "",  # Apache builds from ApacheLounge don't provide GPG signatures
                "link": build["link"]
            })
        os_data.append({"os": "Windows", "data": windows_data})
        
        return {"apache": os_data}

if __name__ == "__main__":
    print("Scraping Apache versions...")
    scraper = ApacheScrape()

    # Try to load changelog HTML from file, else fetch and save it
    changelog_path = "test_changelog.txt"
    if os.path.exists(changelog_path):
        with open(changelog_path, "r", encoding="utf-8") as f:
            changelog_html = f.read()
    else:
        with httpx.Client() as session:
            header = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3",
                "referer": "https://www.apachelounge.com/viewtopic.php?p=43274",
                "accept-language": "en-US,en;q=0.8",
                "cache-control": "max-age=0",
                "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
                "upgrade-insecure-requests": "1",
                "priority": "u=0, i"
            }
            # First, go to a page that sets the cookies
            session.get("https://www.apachelounge.com/viewtopic.php?p=43274")
            # Then, fetch the changelog HTML and save for future use
            changelog_html = session.get(scraper.changelog_url, headers=header).text
            with open(changelog_path, "w", encoding="utf-8") as f:
                f.write(changelog_html)

    version_list = scraper.scrape_version()
    changelog_list = scraper.scrape_changelog(html=changelog_html)  # Use real online data
    result = scraper.scrape(version_list=version_list, changelog_list=changelog_list)
    
    # Save to JSON file like mysql.py does
    with open("assets/apache.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    print("Saved all Apache download info to assets/apache.json")
    print(json.dumps(result, indent=2, ensure_ascii=False))

    