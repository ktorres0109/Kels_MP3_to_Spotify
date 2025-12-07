# --- CONFIGURATION ---
# INSTRUCTIONS:
# 1. Go to the Spotify Developer Dashboard (developer.spotify.com)
# 2. Create an app to get your Client ID and Secret.
# 3. Add 'http://localhost:8888/callback' to your Redirect URIs in the dashboard.

import os

# You can either replace these string with your keys LOCALLY (do not commit them),
# or set them as Environment Variables.
CLIENT_ID = "SPOTIFY_CLIENT_ID"
CLIENT_SECRET = "SPOTIFY_CLIENT_SECRET"
REDIRECT_URI = "http://127.0.0.1:8888/callback"

# Set this to the link of the playlist you want to sync to
PLAYLIST_LINK = "YOUR_PLAYLIST_LINK_HERE" 

# Set this to the folder where your MP3s are stored
LOCAL_MUSIC_PATH = r"C:\Path\To\Your\Music"
INPUT_TEXT_FILE = "FINAL_LOCAL_ONLY.txt" # Set this if you want to fix a specific text file instead of scanning folders
MODE = "TEXT" # Options: "FOLDER" (scans music folder) or "TEXT" (processes the missing text file)

# FILES
PROGRESS_FILE = "scan_progress.json"
OUTPUT_LOCAL_ONLY = "FINAL_LOCAL_ONLY.txt"
OUTPUT_CLASSICAL = "CLASSICAL_FAILURES.txt"

class SpotifySuperSync:
    def __init__(self):
        print("--- Spotify Super Sync Initialized ---")
        self.sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            redirect_uri=REDIRECT_URI,
            scope="playlist-modify-private playlist-modify-public user-library-read"
        ))
        
        self.playlist_id = self.extract_playlist_id(PLAYLIST_LINK)
        
        # --- LOGIC CONFIGURATION ---
        self.keep_tags = ['slowed', 'reverb', 'sped up', 'nightcore', '432', 'live', 'tour version', 'remix', 'en vivo', 'extended']
        self.junk_tags = [
            'official', 'music video', 'video', 'audio', 'explicit', 'lyrics', 
            'hq', 'best quality', 'prod.', 'amv', 'ost', 'un-official mv', 
            'tiktok version', 'visualizer', '4k', 'hd', 'clean', 'bonus track',
            'full song', 'intro', 'repost', 'digitally remastered original', 'album version'
        ]
        self.artist_aliases = {
            'late orchestration': 'Kanye West', '¥$': 'Kanye West', 
            'mrheada$$trendy': 'MrHeadassTrendy', 'travi$ scott': 'Travis Scott',
            'childish gambino': 'Childish Gambino', '검정치마': 'The Black Skirts', 
            '大張偉': 'Wowkie Zhang', '01': '', '10': '', '11': ''
        }
        self.orphan_defaults = {
            'black skinhead': 'Kanye West', 'new slaves': 'Kanye West', 'on sight': 'Kanye West',
            'guilt trip': 'Kanye West', 'bound 2': 'Kanye West', 'blood on the leaves': 'Kanye West',
            'awesome': 'Kanye West', 'diamonds': 'Rihanna', 'happy': 'Pharrell Williams',
            'hurricane': 'Kanye West', 'emotionless': 'Drake'
        }
        self.fake_artists = [
            'lvp', 'argos productions', 'temple of games', 'tranceohlic bass nation', 
            'ost remastered', 'nightcore', 'sped up nightcore', 'incorrect', 
            'kassia', 'coffee house instrumental jazz playlist'
        ]
        # Known leaks to skip immediately
        self.leaks = [
            "mama's boyfriend", "can u be", "never see me again", "precious", 
            "intro-1", "pissy pamper", "skeleton", "cancun", "kid cudi", "alien",
            "new body", "the storm", "chakras", "law of attraction", "yeezus"
        ]

    def extract_playlist_id(self, link):
        if "playlist/" in link:
            return link.split("playlist/")[1].split("?")[0]
        return link

    def get_playlist_inventory(self):
        print("Loading current playlist inventory to prevent duplicates...")
        inventory = []
        try:
            results = self.sp.playlist_items(self.playlist_id)
            while results:
                for item in results['items']:
                    if item['track']:
                        t = item['track']
                        inventory.append({
                            'name': t['name'].lower(),
                            'artist': t['artists'][0]['name'].lower(),
                            'uri': t['uri']
                        })
                if results['next']:
                    results = self.sp.next(results)
                else:
                    break
        except Exception as e:
            print(f"Error loading playlist: {e}")
        return inventory

    def is_in_inventory(self, track_obj, inventory):
        found_name = track_obj['name'].lower()
        found_artist = track_obj['artists'][0]['name'].lower()
        
        for item in inventory:
            # Strict check first
            if item['uri'] == track_obj['uri']: return True
            # Fuzzy check second
            if fuzz.token_set_ratio(found_name, item['name']) > 90 and \
               fuzz.token_set_ratio(found_artist, item['artist']) > 90:
                return True
        return False

    def is_classical(self, text):
        triggers = ['symphony', 'concerto', 'orchestra', 'philharmonic', 'op.', 'no.', 
                    'major', 'minor', 'mozart', 'bach', 'beethoven', 'chopin', 'debussy', 'sonata']
        if "21 savage" in text.lower() or "lil" in text.lower(): return False
        return any(t in text.lower() for t in triggers)

    def normalize_string(self, text):
        # Master text cleaner
        text = text.replace('–', '-').replace('—', '-').replace('−', '-').replace('_', ' ')
        text = re.sub(r'(?<=[a-z])(?=[A-Z])', ' ', text) # CamelCase
        text = text.replace('”', '"').replace('“', '"').replace("’", "'")
        text = text.replace('$', 's').replace('¥$', 'Kanye West')
        text = re.sub(r'(\S)-(\s)', r'\1 - \2', text)
        text = re.sub(r'(\s)-(\S)', r'\1 - \2', text)
        text = re.sub(r'-\d+\.mp3$', '.mp3', text)
        text = re.sub(r'\(\d{4}.*?\)', '', text)
        text = re.sub(r'^\[.*?\]\s*', '', text)
        return text

    def clean_title(self, title, keep_flavor=True):
        title = re.sub(r'\.mp3$', '', title, flags=re.IGNORECASE)
        title = re.sub(r'\[prod\..*?\]', '', title, flags=re.IGNORECASE)
        title = re.sub(r'\(prod\..*?\)', '', title, flags=re.IGNORECASE)

        for tag in self.junk_tags:
            title = re.sub(r'\(' + tag + r'.*?\)', '', title, flags=re.IGNORECASE)
            title = re.sub(r'\[' + tag + r'.*?\]', '', title, flags=re.IGNORECASE)
            title = re.sub(r'\b' + tag + r'\b', '', title, flags=re.IGNORECASE)

        if not keep_flavor:
            for tag in self.keep_tags:
                title = re.sub(r'\(' + tag + r'.*?\)', '', title, flags=re.IGNORECASE)
                title = re.sub(r'\[' + tag + r'.*?\]', '', title, flags=re.IGNORECASE)
                title = re.sub(r'\b' + tag + r'\b', '', title, flags=re.IGNORECASE)
        
        title = re.sub(r'^[IVX]+\.\s*', '', title)
        title = title.lstrip('. ')
        return title.strip()

    def parse_file_info(self, line):
        line = self.normalize_string(line)
        line = line.replace('.mp3', '')

        # Branch A: " by "
        if " by " in line.lower():
            parts = re.split(r' by ', line, flags=re.IGNORECASE, maxsplit=1)
            return parts[1].strip(), parts[0].strip()

        # Branch B: Hyphen
        if " - " in line:
            parts = line.split(" - ", 1)
            artist_cand = parts[0].strip()
            title_cand = parts[1].strip()
            if artist_cand.lower() in self.artist_aliases:
                artist_cand = self.artist_aliases[artist_cand.lower()]
            if artist_cand.lower() in self.fake_artists:
                return "", title_cand
            return artist_cand, title_cand

        # Branch C: Leading Number/Orphan
        match = re.match(r'^(\d+)\s+(.*)', line)
        if match: return "", match.group(2)

        return "", line

    def extract_feat_artist(self, title):
        match = re.search(r'\((?:feat|ft|w\/|with)\.?\s+(.*?)\)', title, re.IGNORECASE)
        if match:
            raw_feat = match.group(1).replace('_', ' ').replace('&', ' ')
            if "chat" in raw_feat.lower() or "humming" in raw_feat.lower(): return None
            return raw_feat
        return None

    def generate_queries(self, raw_line):
        queries = []
        artist_raw, title_raw = self.parse_file_info(raw_line)
        title_flavor = self.clean_title(title_raw, keep_flavor=True)
        title_clean = self.clean_title(title_raw, keep_flavor=False)
        
        artists_to_try = []
        if artist_raw:
            artists_to_try.append(artist_raw)
            for sep in ['&', ',', ' x ']:
                if sep in artist_raw:
                    artists_to_try.extend([a.strip() for a in artist_raw.split(sep)])
        else:
            feat_art = self.extract_feat_artist(title_raw)
            if feat_art: artists_to_try.append(feat_art)
            if title_clean.lower() in self.orphan_defaults:
                artists_to_try.append(self.orphan_defaults[title_clean.lower()])

        # Query Waterfall
        for art in artists_to_try:
            if art: queries.append(f"{art} {title_flavor}")
        for art in artists_to_try:
            if art: queries.append(f"{art} {title_clean}")
        if artist_raw: queries.append(f"{title_clean} {artist_raw}") # Reverse
        if "remix" in raw_line.lower():
            queries.append(f"{title_clean} remix")
            for art in artists_to_try: queries.append(f"{art} {title_clean} remix")
        queries.append(title_flavor)
        queries.append(title_clean)
        
        return list(dict.fromkeys([q for q in queries if len(q) > 1]))

    def verify_match(self, raw_line, track):
        if track['type'] != 'track': return False
        
        found_name = track['name'].lower()
        found_artists = [a['name'].lower() for a in track['artists']]
        
        local_art, local_title = self.parse_file_info(raw_line)
        local_title_clean = self.clean_title(local_title, keep_flavor=False).lower()
        
        title_score = fuzz.token_set_ratio(local_title_clean, found_name)
        
        artist_match = False
        if local_art:
            local_art_norm = local_art.lower().replace('$', 's')
            for found_a in found_artists:
                if fuzz.partial_ratio(local_art_norm, found_a) > 80:
                    artist_match = True
        else:
            feat_art = self.extract_feat_artist(local_title)
            if feat_art:
                for found_a in found_artists:
                    if fuzz.partial_ratio(feat_art.lower(), found_a) > 80: artist_match = True
            elif local_title_clean in self.orphan_defaults:
                def_art = self.orphan_defaults[local_title_clean].lower()
                for found_a in found_artists:
                    if fuzz.partial_ratio(def_art, found_a) > 80: artist_match = True

        if title_score > 90 and artist_match: return True
        if title_score == 100: return True
        if title_score > 80 and artist_match: return True
        if title_score > 95 and not local_art: return True
        return False

    def add_tracks_batch(self, uris):
        if not uris: return
        uris = list(set(uris))
        print(f"Adding {len(uris)} tracks to playlist...")
        for i in range(0, len(uris), 100):
            try:
                self.sp.playlist_add_items(self.playlist_id, uris[i:i+100])
                time.sleep(1) # Be nice to API
            except Exception as e:
                print(f"Error adding batch: {e}")

    def run(self, mode="TEXT"):
        inventory = self.get_playlist_inventory()
        
        # Load Progress
        if os.path.exists(PROGRESS_FILE):
            with open(PROGRESS_FILE, 'r') as f:
                progress = json.load(f)
        else:
            progress = {"processed": [], "local": [], "classical": []}

        files_to_process = []
        
        if mode == "FOLDER":
            print(f"Scanning folder: {LOCAL_MUSIC_PATH}")
            for root, dirs, files in os.walk(LOCAL_MUSIC_PATH):
                for file in files:
                    if file.endswith(".mp3") and file not in progress["processed"]:
                        files_to_process.append(file)
        else:
            print(f"Reading file list: {INPUT_TEXT_FILE}")
            if os.path.exists(INPUT_TEXT_FILE):
                with open(INPUT_TEXT_FILE, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and line not in progress["processed"]:
                            files_to_process.append(line)

        print(f"Processing {len(files_to_process)} items...")
        
        found_uris = []
        new_local = []
        new_classical = []
        
        for item in tqdm(files_to_process):
            # Check for known leaks
            if any(l in item.lower() for l in self.leaks):
                new_local.append(item)
                progress["processed"].append(item)
                continue

            # Classical check
            if self.is_classical(item):
                new_classical.append(item)
                progress["processed"].append(item)
                continue

            queries = self.generate_queries(item)
            match_found = False
            
            for q in queries:
                try:
                    res = self.sp.search(q, limit=1, type='track')
                    if res['tracks']['items']:
                        track = res['tracks']['items'][0]
                        if self.verify_match(item, track):
                            if not self.is_in_inventory(track, inventory):
                                found_uris.append(track['uri'])
                            match_found = True
                            break # Stop queries if found
                except Exception:
                    time.sleep(2) # Basic rate limit backoff
            
            if not match_found:
                new_local.append(item)
            
            progress["processed"].append(item)
            
            # Batch add every 20 found
            if len(found_uris) >= 20:
                self.add_tracks_batch(found_uris)
                found_uris = []
                # Save progress
                progress["local"].extend(new_local)
                progress["classical"].extend(new_classical)
                with open(PROGRESS_FILE, 'w') as f: json.dump(progress, f)
                new_local = []
                new_classical = []

        # Final Batch
        self.add_tracks_batch(found_uris)
        progress["local"].extend(new_local)
        progress["classical"].extend(new_classical)
        
        with open(PROGRESS_FILE, 'w') as f: json.dump(progress, f)
        
        # Write readable outputs
        with open(OUTPUT_LOCAL_ONLY, 'w', encoding='utf-8') as f:
            f.write('\n'.join(progress["local"]))
        with open(OUTPUT_CLASSICAL, 'w', encoding='utf-8') as f:
            f.write('\n'.join(progress["classical"]))
            
        print("Done! Check OUTPUT files for results.")

if __name__ == "__main__":
    syncer = SpotifySuperSync()
    # Change MODE to "FOLDER" to scan your drive, or "TEXT" to fix the file list
    syncer.run(mode=MODE)