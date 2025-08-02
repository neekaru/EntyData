import json
from utils import VersionHandling

class PhpMyAdminScrape:
    def __init__(self):
        self.versions = [
            "5.1.0", "5.1.1", "5.1.2", "5.1.3", "5.1.4",
            "5.2.0", "5.2.1", "5.2.2"
        ]

    def get_versions(self):
        # Sort versions in descending order       
        sorted_versions = sorted(self.versions, key=VersionHandling.version_key, reverse=True)
        
        # Create data for each OS
        os_data = []
        
        # Windows data
        windows_data = []
        for v in sorted_versions:
            base_url = f"https://files.phpmyadmin.net/phpMyAdmin/{v}/phpMyAdmin-{v}"
            windows_data.append({
                "version": v,
                "gpg": "",  # PhpMyAdmin doesn't provide GPG signatures
                "link": f"{base_url}-all-languages.zip"
            })
        os_data.append({"os": "Windows", "data": windows_data})
        
        # Linux data
        linux_data = []
        for v in sorted_versions:
            base_url = f"https://files.phpmyadmin.net/phpMyAdmin/{v}/phpMyAdmin-{v}"
            linux_data.append({
                "version": v,
                "gpg": "",  # PhpMyAdmin doesn't provide GPG signatures
                "link": f"{base_url}-all-languages.tar.gz"
            })
        os_data.append({"os": "Linux", "data": linux_data})
        
        # macOS data
        macos_data = []
        for v in sorted_versions:
            base_url = f"https://files.phpmyadmin.net/phpMyAdmin/{v}/phpMyAdmin-{v}"
            macos_data.append({
                "version": v,
                "gpg": "",  # PhpMyAdmin doesn't provide GPG signatures
                "link": f"{base_url}-all-languages.tar.gz"
            })
        os_data.append({"os": "macOS", "data": macos_data})
        
        return {"phpmyadmin": os_data}

if __name__ == "__main__":
    data = PhpMyAdminScrape().get_versions()
    with open("assets/phpmyadmin.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print("Saved all PhpMyAdmin download info to assets/phpmyadmin.json")
    print(json.dumps(data, indent=2, ensure_ascii=False))