
import httpx
from utils import v2tuple, version_key, SimpleVersion

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

        nodejs = []
        for item in data:
            ver = item['version'].replace('v', '')
            if SimpleVersion(ver) >= self.min_version:
                nodejs.append({
                    "version": ver,
                    "files": self.crafted_file_entries(ver)
                })
        return {"nodejs": nodejs}

import json
with open("nodejs.json", "w", encoding="utf-8") as f:
    json.dump(NodeScrape().scrape_version(), f, indent=2)

print("Saved to nodejs.json")