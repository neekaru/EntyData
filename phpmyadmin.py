import json

class PhpMyAdminScrape:
    def __init__(self):
        self.versions = [
            "5.1.0", "5.1.1", "5.1.2", "5.1.3", "5.1.4",
            "5.2.0", "5.2.1", "5.2.2"
        ]

    def get_versions(self):
        result = []
        for v in self.versions:
            base_url = f"https://files.phpmyadmin.net/phpMyAdmin/{v}/phpMyAdmin-{v}"
            result.append({
                "version": v,
                "downloads": [
                    {
                        "type": "all-languages",
                        "url": f"{base_url}-all-languages.zip"
                    },
                    {
                        "type": "english",
                        "url": f"{base_url}-english.zip"
                    }
                ]
            })
        return {"phpmyadmin": result}

if __name__ == "__main__":
    data = PhpMyAdminScrape().get_versions()
    with open("phpmyadmin.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print("Saved to phpmyadmin.json")