import os
import json
import time
import gzip
import requests
from src import config

class SteamExtractor:
    """Handles interaction with Steam web APIs to fetch game catalogs and detailed game metadata incrementally."""

    def __init__(self, api_key=None, out_dir=None, apps_file=None, log_file=None):
        self.api_key = api_key or config.STEAM_API_KEY
        self.out_dir = out_dir or config.RAW_DATA_DIR
        self.apps_file = apps_file or config.APPS_FILE
        self.log_file = log_file or config.LOG_FILE
        self.chunk_size = config.CHUNK_SIZE
        self.rate_limit_delay = config.RATE_LIMIT_DELAY

    def log(self, message):
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        formatted = f"[{timestamp}] {message}"
        print(formatted)
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(formatted + "\n")

    def fetch_all_apps(self):
        self.log("Fetching latest app catalog from Steam API...")
        url = f"https://api.steampowered.com/IStoreService/GetAppList/v1/?key={self.api_key}&max_results=50000"
        all_apps = []

        while True:
            try:
                response = requests.get(url, timeout=20)
                if response.status_code != 200:
                    self.log(f"HTTP Error {response.status_code} while fetching app list. Retrying in 5 seconds...")
                    time.sleep(5)
                    continue

                data = response.json().get("response", {})
                apps = data.get("apps", [])
                all_apps.extend(apps)

                print(f"  Fetched {len(apps)} apps (Total: {len(all_apps)})")

                if data.get("have_more_results"):
                    last_appid = data.get("last_appid")
                    url = f"https://api.steampowered.com/IStoreService/GetAppList/v1/?key={self.api_key}&max_results=50000&last_appid={last_appid}"
                    time.sleep(1)
                else:
                    break
            except Exception as e:
                self.log(f"Exception during app list fetch: {e}. Retrying in 5s...")
                time.sleep(5)

        self.log(f"Total apps discovered on Steam: {len(all_apps)}")
        return all_apps

    def load_known_apps(self):
        if os.path.exists(self.apps_file):
            try:
                with open(self.apps_file, "r", encoding="utf-8") as f:
                    known_apps = json.load(f)
                    return known_apps
            except Exception as e:
                self.log(f"Warning: Failed to load {self.apps_file}: {e}")
        return []

    def save_known_apps(self, known_apps):
        os.makedirs(os.path.dirname(self.apps_file), exist_ok=True)
        with open(self.apps_file, "w", encoding="utf-8") as f:
            json.dump(known_apps, f, indent=4)

    def extract_new_games(self):
        os.makedirs(self.out_dir, exist_ok=True)

        known_apps = self.load_known_apps()
        known_appids = {app["appid"] for app in known_apps}
        self.log(f"Loaded {len(known_appids)} known apps state tracking file.")

        current_apps = self.fetch_all_apps()
        new_apps = [app for app in current_apps if app["appid"] not in known_appids]

        self.log(f"Update started. Found {len(new_apps)} NEW apps to inspect and fetch.")
        if not new_apps:
            self.log("No new apps to process. Everything is up to date!")
            return 0

        added_count = 0
        game_count = 0

        for i, app in enumerate(new_apps, 1):
            appid = app["appid"]
            app_name = app.get('name', 'Unknown')
            print(f"[{i}/{len(new_apps)}] Fetching AppID {appid} ({app_name})...")

            try:
                res = requests.get(f"https://store.steampowered.com/api/appdetails?appids={appid}", timeout=15)
                if res.status_code == 200:
                    app_details = res.json()
                    appid_str = str(appid)
                    success = app_details.get(appid_str, {}).get("success")

                    if success:
                        app_type = app_details.get(appid_str, {}).get("data", {}).get("type")
                        if app_type == "game":
                            record = {"appid": appid, "raw_response": app_details}

                            range_start = (appid // self.chunk_size) * self.chunk_size
                            range_end = range_start + self.chunk_size - 1
                            filename = f"apps_{range_start}_{range_end}.jsonl.gz"
                            filepath = os.path.join(self.out_dir, filename)

                            with gzip.open(filepath, "at", encoding="utf-8") as out_f:
                                out_f.write(json.dumps(record) + "\n")

                            self.log(f"SAVED GAME DATA: {app_name} (AppID: {appid}) added to {filename}")
                            game_count += 1
                        else:
                            self.log(f"SKIPPED DATA: {app_name} (AppID: {appid}) is not a game (Type: {app_type})")
                    else:
                        self.log(f"SKIPPED DATA: {app_name} (AppID: {appid}) returned success: false")

                    known_apps.append(app)
                    added_count += 1

                    if added_count % 50 == 0:
                        self.save_known_apps(known_apps)

                elif res.status_code == 429:
                    self.log("Rate limit exceeded (HTTP 429)! Waiting 60 seconds...")
                    time.sleep(60)
                else:
                    self.log(f"HTTP Error {res.status_code} for AppID {appid}")

            except Exception as e:
                self.log(f"Error fetching AppID {appid}: {e}")

            time.sleep(self.rate_limit_delay)

        if added_count > 0:
            self.save_known_apps(known_apps)

        self.log(f"Extraction step completed. Processed {added_count} new appids. Saved {game_count} valid games.")
        return game_count

if __name__ == "__main__":
    extractor = SteamExtractor()
    extractor.extract_new_games()
