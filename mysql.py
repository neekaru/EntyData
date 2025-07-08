import httpx
from bs4 import BeautifulSoup
import re
from tqdm import tqdm
import logging

class MysqlScrape:
    def __init__(self):
        self.community_url_download = "https://downloads.mysql.com/archives/community/"
        self.latest_mysql_url = "https://dev.mysql.com/downloads/mysql/"
        self.accepted_versions = ["8.2", "8.1", "8.0", "5.7", "5.6", "5.5"]
        self.os_handling = {"win": 3, "linux": 2, "mac": 33}
        self.block_list = ["32-bit", "test", "minimal", "ia-64", "debug"]

    @staticmethod
    def scrape_base(url_base, target_os):
        bs = BeautifulSoup(httpx.get(url_base).text, "html.parser")
        table = bs.find("table").find_all("tr")
        table = [row for row in table if len(row.find_all("td")) == 4]
        results = []
        for row in table:
            td_element = row.find_all("td")
            package_name = td_element[0].text
            if any(block in package_name.lower() for block in MysqlScrape().block_list):
                continue
            url = td_element[3].find("a").get("href")
            next_line = row.find_next_sibling().find_all("td")
            file_name = re.sub(r"[()]", "", next_line[0].text) # fastest way
        
            # Exclude unwanted file extensions globally
            if url.endswith((".msi", ".tar.gz", ".dmg")):
                continue
        
            md5 = next_line[1].find("code", {"class": "md5"}).text
            try:
                gpg = next_line[1].find("a", {"class": "signature"}).get("href")
            except (TypeError, AttributeError):
                print(f"Skipping {file_name} due to missing GPG signature, maybe they are not available yet.")
                continue

            results.append({
                "os": target_os,
                "url": ("https://downloads.mysql.com" + url if url.startswith("/") else url),
                "file_name": file_name,
                "md5": md5,
                "gpg": ("https://downloads.mysql.com" + gpg if gpg.startswith("/") else gpg),
            })
        return results

    def get_mysql_older(self, os):
        import concurrent.futures
        import logging

        release_url = []
        bs = BeautifulSoup(httpx.get(self.community_url_download).text, "html.parser")
        available_versions =  bs.find("label", string="Product Version:").parent.find_all("option")
        available_versions = [version.text for version in available_versions if version.text.startswith(tuple(self.accepted_versions))]
        allowed_versions = [version for version in available_versions if version.startswith(tuple(self.accepted_versions))]
        exclude_keywords = ["rc", "alpha", "beta", "snapshot", "dmr"]
        allowed_versions = [
            version for version in allowed_versions
            if not any(x in version.lower() for x in exclude_keywords)
            and not re.search(r"m([1-9]|1[0-9]|20)\b", version.lower())
        ]
        if os not in self.os_handling:
            raise ValueError(f"Unsupported OS: {os}. Supported OS are: {list(self.os_handling.keys())}")
        os_id = self.os_handling[os]

        def fetch_version(version):
            url = f"{self.community_url_download}?tpl=platform&os={os_id}&version={version}"
            logging.info(f"Fetching version {version} for OS {os}")
            info_pkgs = self.scrape_base(url, os)
            results = []
            if info_pkgs:
                for pkg in info_pkgs:
                    pkg["version"] = version
                    results.append(pkg)
            logging.info(f"Completed version {version} for OS {os} ({len(results)} packages)")
            return results

        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            futures = [executor.submit(fetch_version, version) for version in allowed_versions]
            for future in concurrent.futures.as_completed(futures):
                release_url.extend(future.result())

        return release_url


import json

if __name__ == "__main__":
    # Setup logging to logs.txt with real-time flush
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s: %(message)s",
        handlers=[logging.FileHandler("logs.txt", mode="w", encoding="utf-8")]
    )
    class FlushOnWriteHandler(logging.FileHandler):
        def emit(self, record):
            super().emit(record)
            self.flush()
    for handler in logging.getLogger().handlers:
        if isinstance(handler, logging.FileHandler):
            handler.flush = handler.stream.flush

    scraper = MysqlScrape()
    all_data = []
    os_list = ["win", "linux", "mac"]
    for os_name in tqdm(os_list, desc="OS Progress"):
        logging.info(f"Start scraping for OS: {os_name}")
        try:
            # Prepare version list for progress bar
            bs = BeautifulSoup(httpx.get(scraper.community_url_download).text, "html.parser")
            available_versions =  bs.find("label", string="Product Version:").parent.find_all("option")
            available_versions = [version.text for version in available_versions if version.text.startswith(tuple(scraper.accepted_versions))]
            allowed_versions = [version for version in available_versions if version.startswith(tuple(scraper.accepted_versions))]
            exclude_keywords = ["rc", "alpha", "beta", "snapshot", "dmr"]
            allowed_versions = [
                version for version in allowed_versions
                if not any(x in version.lower() for x in exclude_keywords)
                and not re.search(r"m([1-9]|1[0-9]|20)\b", version.lower())
            ]
            from concurrent.futures import ThreadPoolExecutor, as_completed
            version_bar = tqdm(total=len(allowed_versions), desc=f"{os_name} versions", leave=False)
            entries = []
            def fetch_and_collect(version):
                try:
                    url = f"{scraper.community_url_download}?tpl=platform&os={scraper.os_handling[os_name]}&version={version}"
                    info_pkgs = scraper.scrape_base(url, os_name)
                    result = []
                    if info_pkgs:
                        for pkg in info_pkgs:
                            pkg["version"] = version
                            result.append(pkg)
                    logging.info(f"Completed version {version} for OS {os_name} ({len(result)} packages)")
                    return result
                finally:
                    version_bar.update(1)
            with ThreadPoolExecutor(max_workers=8) as executor:
                futures = [executor.submit(fetch_and_collect, version) for version in allowed_versions]
                for future in as_completed(futures):
                    entries.extend(future.result())
            version_bar.close()
            logging.info(f"Found {len(entries)} entries for {os_name}")
            for entry in entries:
                if entry is None:
                    logging.warning(f"Skipped None entry for {os_name}")
                    continue
                all_data.append({
                    "os": entry.get("os", os_name),
                    "url": entry.get("url"),
                    "version": entry.get("version")
                })
                logging.info(f"Added entry: OS={entry.get('os', os_name)}, version={entry.get('version')}, url={entry.get('url')}")
        except Exception as e:
            logging.error(f"Error scraping {os_name}: {e}")
    # Map internal OS keys to display names
    os_display = {"win": "Windows", "linux": "Linux", "mac": "macOS"}
    grouped = {"Windows": [], "Linux": [], "macOS": []}
    
    for entry in all_data:
        os_key = entry.get("os", "Unknown")
        os_name = os_display.get(os_key, os_key)
        grouped.setdefault(os_name, []).append({
            "version": entry.get("version", ""),
            "gpg": entry.get("gpg", ""),
            "link": entry.get("url", "")
        })
    
    # For each OS, group by version and sort by version descending
    mysql_list = []
    for os_name, data in grouped.items():
        if not data:
            continue
        version_map = {}
        for entry in data:
            version = entry.get("version", "")
            # Only keep one entry per version (first one found)
            if version not in version_map:
                version_map[version] = {
                    "version": version,
                    "gpg": entry.get("gpg", ""),
                    "link": entry.get("link", "")
                }
        
        def version_key(v):
            return tuple(int(x) if x.isdigit() else 0 for x in v.split(".")) if v else (0,)

        sorted_versions = sorted(version_map.keys(), key=version_key, reverse=True)
        ordered_data = [version_map[v] for v in sorted_versions]
        mysql_list.append({"os": os_name, "data": ordered_data})
    
    db = {"mysql": mysql_list}
    with open("database.json", "w", encoding="utf-8") as f:
        json.dump(db, f, indent=2, ensure_ascii=False)
    logging.info("Saved all MySQL download info to database.json")
    print("Saved all MySQL download info to database.json")
