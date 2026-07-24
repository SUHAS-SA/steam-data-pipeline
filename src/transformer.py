import json
import os
import re
from datetime import datetime
from src import config

class SteamDataTransformer:
    """Transforms raw scraped JSONL app details into normalized SQL queries and clean structured data models."""

    def __init__(self, input_dir=None, output_sql=None, log_file=None):
        self.input_dir = input_dir or config.RAW_DATA_DIR
        self.output_sql = output_sql or config.SQL_OUTPUT_FILE
        self.log_file = log_file or config.LOG_FILE

    @staticmethod
    def sql_val_str(val):
        if val is None or val == "":
            return "NULL"
        escaped = str(val).replace("'", "''")
        return f"'{escaped}'"

    @staticmethod
    def parse_date(date_str):
        if not date_str:
            return None
        formats = ["%d %b, %Y", "%b %d, %Y", "%d %B, %Y", "%B %d, %Y", "%b %Y", "%B %Y", "%Y"]
        for fmt in formats:
            try:
                dt = datetime.strptime(date_str, fmt)
                return dt.strftime("%Y-%m-%d")
            except ValueError:
                continue
        return None

    @staticmethod
    def parse_requirements_html(html_str):
        if not html_str:
            return {}
        
        # Strip header strong tag
        html_str = re.sub(r'<strong>(Minimum|Recommended):?</strong><br>', '', html_str, flags=re.IGNORECASE)
        reqs = {}
        
        li_matches = re.findall(r'<li>(.*?)</li>', html_str, re.IGNORECASE | re.DOTALL)
        if not li_matches:
            li_matches = re.split(r'<br\s*/?>', html_str, flags=re.IGNORECASE)
            
        for li in li_matches:
            li = li.strip()
            if not li:
                continue
            kv_match = re.search(r'<strong>\s*(.*?)\s*:?\s*</strong>\s*:?\s*(.*)', li, re.IGNORECASE | re.DOTALL)
            if kv_match:
                key = kv_match.group(1).strip().replace(' *', '').replace(':', '').lower()
                val = kv_match.group(2).strip()
                val = re.sub(r'<[^>]+>', ' ', val).strip()
                val = re.sub(r'\s+', ' ', val)
                
                if 'os' in key:
                    reqs['os'] = val
                elif 'processor' in key or 'cpu' in key:
                    reqs['processor'] = val
                elif 'memory' in key or 'ram' in key:
                    reqs['memory'] = val
                elif 'graphics' in key or 'video card' in key or 'gpu' in key:
                    reqs['graphics'] = val
                elif 'directx' in key:
                    reqs['directx'] = val
                elif 'network' in key or 'internet' in key:
                    reqs['network'] = val
                elif 'storage' in key or 'hard drive' in key or 'space' in key:
                    reqs['storage'] = val
                elif 'sound' in key:
                    reqs['sound_card'] = val
                elif 'additional' in key:
                    reqs['additional_notes'] = val
        return reqs

    def get_target_appids_and_files_from_log(self):
        if not os.path.exists(self.log_file):
            return set(), set()

        with open(self.log_file, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()

        start_idx = 0
        for i in range(len(lines) - 1, -1, -1):
            if "Update started." in lines[i]:
                start_idx = i
                break

        target_lines = lines[start_idx:]
        appids = set()
        files = set()
        pattern = re.compile(r"\(AppID:\s*(\d+)\)\s*added to\s*(.*?\.jsonl)")

        for line in target_lines:
            match = pattern.search(line)
            if match:
                appids.add(int(match.group(1)))
                files.add(match.group(2))

        return appids, files

    def transform_to_sql(self):
        appids_to_process, files_to_process = self.get_target_appids_and_files_from_log()

        if not appids_to_process:
            print("No new games found in latest extraction logs to transform.")
            return 0

        print(f"Transforming {len(appids_to_process)} games from {len(files_to_process)} JSONL files...")
        os.makedirs(os.path.dirname(self.output_sql), exist_ok=True)

        count = 0
        with open(self.output_sql, "w", encoding="utf-8") as out_f:
            out_f.write("-- Steam Games Normalized SQL Dump\n")

            for jsonl_filename in files_to_process:
                jsonl_file = os.path.join(self.input_dir, jsonl_filename)
                if not os.path.exists(jsonl_file):
                    continue

                with open(jsonl_file, "r", encoding="utf-8") as f:
                    for line in f:
                        if not line.strip():
                            continue
                        try:
                            record = json.loads(line)
                        except json.JSONDecodeError:
                            continue

                        appid = record.get("appid")
                        if appid not in appids_to_process:
                            continue

                        raw_response = record.get("raw_response", {})
                        app_data = raw_response.get(str(appid), {})
                        if not app_data.get("success"):
                            continue

                        details = app_data.get("data", {})
                        if details.get("type") != "game":
                            continue

                        name = details.get("name", "")
                        if not name or len(name) > 255:
                            continue

                        developers = ", ".join(details.get("developers", [])) if isinstance(details.get("developers"), list) else ""
                        publishers = ", ".join(details.get("publishers", [])) if isinstance(details.get("publishers"), list) else ""
                        
                        release_info = details.get("release_date", {})
                        release_date = self.parse_date(release_info.get("date", "")) if not release_info.get("coming_soon") else None

                        platforms_dict = details.get("platforms", {})
                        platforms = ", ".join([p for p, val in platforms_dict.items() if val])
                        header_image = details.get("header_image", "")

                        metacritic_info = details.get("metacritic")
                        metacritic_score = metacritic_info.get("score") if isinstance(metacritic_info, dict) else None
                        metacritic_sql = str(metacritic_score) if metacritic_score is not None else "NULL"
                        about_the_game = details.get("about_the_game", "")

                        # Insert Game SQL
                        stmt = f"""INSERT INTO games (steam_appid, name, developer, publisher, release_date, platforms, header_image, metacritic_score, about_the_game)
VALUES ({appid}, {self.sql_val_str(name)}, {self.sql_val_str(developers)}, {self.sql_val_str(publishers)}, {self.sql_val_str(release_date)}, {self.sql_val_str(platforms)}, {self.sql_val_str(header_image)}, {metacritic_sql}, {self.sql_val_str(about_the_game)})
ON CONFLICT (steam_appid) DO UPDATE SET 
    name = EXCLUDED.name, developer = EXCLUDED.developer, publisher = EXCLUDED.publisher,
    release_date = EXCLUDED.release_date, platforms = EXCLUDED.platforms,
    header_image = EXCLUDED.header_image, metacritic_score = EXCLUDED.metacritic_score, about_the_game = EXCLUDED.about_the_game;\n"""
                        out_f.write(stmt)

                        # Genres Junction SQL
                        for g in details.get("genres", []):
                            g_name = str(g.get("description", "")).strip()
                            if g_name:
                                n_sql = self.sql_val_str(g_name)
                                out_f.write(f"INSERT INTO genres (name) VALUES ({n_sql}) ON CONFLICT (name) DO NOTHING;\n")
                                out_f.write(f"INSERT INTO game_genres (game_appid, genre_id) VALUES ({appid}, (SELECT genre_id FROM genres WHERE name = {n_sql})) ON CONFLICT (game_appid, genre_id) DO NOTHING;\n")

                        # Tags Junction SQL
                        for c in details.get("categories", []):
                            c_name = str(c.get("description", "")).strip()
                            if c_name:
                                t_sql = self.sql_val_str(c_name)
                                out_f.write(f"INSERT INTO tags (name) VALUES ({t_sql}) ON CONFLICT (name) DO NOTHING;\n")
                                out_f.write(f"INSERT INTO game_tags (game_appid, tag_id) VALUES ({appid}, (SELECT tag_id FROM tags WHERE name = {t_sql})) ON CONFLICT (game_appid, tag_id) DO NOTHING;\n")

                        # System Requirements SQL
                        for plat_key, plat_name in [("pc_requirements", "pc"), ("mac_requirements", "mac"), ("linux_requirements", "linux")]:
                            req_data = details.get(plat_key)
                            if isinstance(req_data, dict) and req_data:
                                for req_type in ["minimum", "recommended"]:
                                    req_html = req_data.get(req_type, "")
                                    parsed = self.parse_requirements_html(req_html)
                                    if parsed or str(req_html).strip():
                                        out_f.write(f"""INSERT INTO game_requirements (game_appid, platform, req_type, os, processor, memory, graphics, directx, network, storage, sound_card, raw_requirement, additional_notes) 
VALUES ({appid}, '{plat_name}', '{req_type}', {self.sql_val_str(parsed.get('os'))}, {self.sql_val_str(parsed.get('processor'))}, {self.sql_val_str(parsed.get('memory'))}, {self.sql_val_str(parsed.get('graphics'))}, {self.sql_val_str(parsed.get('directx'))}, {self.sql_val_str(parsed.get('network'))}, {self.sql_val_str(parsed.get('storage'))}, {self.sql_val_str(parsed.get('sound_card'))}, {self.sql_val_str(req_html)}, {self.sql_val_str(parsed.get('additional_notes'))}) 
ON CONFLICT (game_appid, platform, req_type) DO UPDATE SET 
    os = EXCLUDED.os, processor = EXCLUDED.processor, memory = EXCLUDED.memory, graphics = EXCLUDED.graphics, directx = EXCLUDED.directx, network = EXCLUDED.network, storage = EXCLUDED.storage, sound_card = EXCLUDED.sound_card, raw_requirement = EXCLUDED.raw_requirement, additional_notes = EXCLUDED.additional_notes;\n""")
                        count += 1

        print(f"Successfully transformed {count} game records into SQL script: {self.output_sql}")
        return count

if __name__ == "__main__":
    transformer = SteamDataTransformer()
    transformer.transform_to_sql()
