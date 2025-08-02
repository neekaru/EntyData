import httpx
import re
from bs4 import BeautifulSoup
from utils import VersionHandling

class Nginx:
    def __init__(self):
        self.url = "https://nginx.org/en/download.html"
        self.change_log = "https://nginx.org/en/CHANGES"
        self.min_version = (1, 20, 1)  # Minimum version: 1.11.8

    def parse_version(self, text):
        """Extract version number from changelog text"""
        match = re.search(r'Changes with nginx (\d+)\.(\d+)\.(\d+)', text)
        if match:
            return (int(match.group(1)), int(match.group(2)), int(match.group(3)))
        return None

    def compare_versions(self, version1, version2):
        """Compare two version tuples. Returns True if version1 >= version2"""
        return version1 >= version2

    def blacklist_version(self, text):
        """Return True to blacklist versions below 1.20.1"""
        version = self.parse_version(text)
        if version is None:
            return False  # Don't blacklist if we can't parse the version
        
        # Blacklist versions below 1.20.1
        return not self.compare_versions(version, self.min_version)

    def changelog_version(self):
        res = httpx.get(self.change_log)
        soup = BeautifulSoup(res.text, "html.parser")
        text = soup.get_text()
        
        # Find all version patterns in the changelog
        version_pattern = r'Changes with nginx (\d+\.\d+\.\d+)'
        matches = re.findall(version_pattern, text)
        
        versions = []
        for version_str in matches:
            # Create a fake changelog line to test with blacklist
            test_line = f"Changes with nginx {version_str}"
            if not self.blacklist_version(test_line):
                versions.append(version_str)
        
        return versions
    
    
    def show_download(self):
        # Fetch the download page
        versions = self.changelog_version()
        
        # Sort versions in descending order
        sorted_versions = sorted(versions, key=VersionHandling.version_key, reverse=True)
        
        # Create data for each OS
        os_data = []
        
        # Windows data
        windows_data = []
        for version in sorted_versions:
            windows_data.append({
                "version": version,
                "gpg": f"https://nginx.org/download/nginx-{version}.zip.asc",
                "link": f"https://nginx.org/download/nginx-{version}.zip"
            })
        os_data.append({"os": "Windows", "data": windows_data})
        
        # Linux data
        linux_data = []
        for version in sorted_versions:
            linux_data.append({
                "version": version,
                "gpg": f"https://nginx.org/download/nginx-{version}.tar.gz.asc",
                "link": f"https://nginx.org/download/nginx-{version}.tar.gz"
            })
        os_data.append({"os": "Linux", "data": linux_data})
        
        # macOS data
        macos_data = []
        for version in sorted_versions:
            macos_data.append({
                "version": version,
                "gpg": f"https://nginx.org/download/nginx-{version}.tar.gz.asc",
                "link": f"https://nginx.org/download/nginx-{version}.tar.gz"
            })
        os_data.append({"os": "macOS", "data": macos_data})
        
        return {"nginx": os_data}

    
if __name__ == "__main__":
    import json
    
    nginx = Nginx()
    result = nginx.show_download()
    print(nginx.changelog_version())
    
    # Save to JSON file like mysql.py does
    with open("assets/nginx.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    print("Saved all Nginx download info to assets/nginx.json")
    print(json.dumps(result, indent=2, ensure_ascii=False))
