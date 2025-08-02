
import httpx
from utils import SimpleVersion

class NodeScrape:
    def __init__(self):
        self.json_release = "https://nodejs.org/dist/index.json"
        self.min_version = SimpleVersion("18.0.0")

    @staticmethod
    def crafted_file_entries(version_str):
        base_url = f"https://nodejs.org/dist/v{version_str}"
        gpg_url = f"{base_url}/SHASUMS256.txt.asc"
        files = [
            {
                "os": "Linux",
                "arch": "x64",
                "type": "tar.xz",
                "link": f"{base_url}/node-v{version_str}-linux-x64.tar.xz",
                "gpg": gpg_url
            },
            {
                "os": "Windows",
                "arch": "x64",
                "type": "zip",
                "link": f"{base_url}/node-v{version_str}-win-x64.zip",
                "gpg": gpg_url
            },
            {
                "os": "macOS",
                "arch": "arm64",
                "type": "tar.xz",
                "link": f"{base_url}/node-v{version_str}-darwin-arm64.tar.xz",
                "gpg": gpg_url
            }
        ]
        # Not all versions have all files, but for simplicity, always include these entries
        return files
    
    def scrape_version(self):
        try:
            response = httpx.get(self.json_release)
            response.raise_for_status()
            data = response.json()
        except httpx.RequestError as e:
            print(f"An error occurred while fetching the data: {e}")
            return {}

        # Collect all versions that meet the minimum version requirement
        versions = []
        for item in data:
            ver = item['version'].replace('v', '')
            if SimpleVersion(ver) >= self.min_version:
                versions.append(ver)
        
        # Create data for each OS
        os_data = []
        
        # Windows data
        windows_data = []
        for ver in versions:
            base_url = f"https://nodejs.org/dist/v{ver}"
            windows_data.append({
                "version": ver,
                "gpg": f"{base_url}/SHASUMS256.txt.asc",
                "link": f"{base_url}/node-v{ver}-win-x64.zip"
            })
        os_data.append({"os": "Windows", "data": windows_data})
        
        # Linux data
        linux_data = []
        for ver in versions:
            base_url = f"https://nodejs.org/dist/v{ver}"
            linux_data.append({
                "version": ver,
                "gpg": f"{base_url}/SHASUMS256.txt.asc",
                "link": f"{base_url}/node-v{ver}-linux-x64.tar.xz"
            })
        os_data.append({"os": "Linux", "data": linux_data})
        
        # macOS data
        macos_data = []
        for ver in versions:
            base_url = f"https://nodejs.org/dist/v{ver}"
            macos_data.append({
                "version": ver,
                "gpg": f"{base_url}/SHASUMS256.txt.asc",
                "link": f"{base_url}/node-v{ver}-darwin-arm64.tar.xz"
            })
        os_data.append({"os": "macOS", "data": macos_data})
        
        return {"nodejs": os_data}

if __name__ == "__main__":
    import json
    
    scraper = NodeScrape()
    result = scraper.scrape_version()
    
    # Save to JSON file like mysql.py does
    with open("assets/nodejs.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    print("Saved all Node.js download info to assets/nodejs.json")
    print(json.dumps(result, indent=2, ensure_ascii=False))