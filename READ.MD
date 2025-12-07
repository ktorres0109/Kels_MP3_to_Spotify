# 🎵 Spotify Super Sync

A robust, intelligent Python script designed to sync messy local MP3 libraries to Spotify playlists. 

Unlike standard importers, this tool uses aggressive fuzzy matching and logic branches to handle "internet-style" filenames—including YouTube rips, slowed/reverb edits, typos, unreleased leaks, and inconsistent metadata.

## ✨ Features

* **Aggressive Normalization:** Automatically fixes "leet speak" (`Travi$ Scott`), CamelCase (`LifeOfTheParty`), and missing spaces.
* **Smart "Flavor" Detection:** Finds the original song even if your file is named `Song (Slowed + Reverb)` or `Song (Sped Up)`.
* **Fake Artist Bypass:** Detects and ignores YouTube uploader names (e.g., `LVP`, `Argos Productions`) to find the actual song title.
* **Duplicate Protection:** Checks your current playlist inventory before adding tracks to prevent duplicates.
* **Orphan Handler:** Intelligently guesses artists for files with missing data (e.g., `Black Skinhead.mp3` -> searches Kanye West).
* **Classical Filter:** Separates classical music files into a separate log file to avoid mismatched pop song results.

## 🛠️ Prerequisites

* Python 3.x
* A Spotify Developer Account (Free)

## 📦 Installation

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/YOUR_USERNAME/Kels_MP3_to_Spotify.git](https://github.com/YOUR_USERNAME/Kels_MP3_to_Spotify.git)
    cd Kels_MP3_to_Spotify
    ```

2.  **Install dependencies:**
    ```bash
    pip install spotipy thefuzz tqdm
    ```

3.  **Set up your environment:**
    * Create a `.gitignore` file to protect your secrets (see "Security" below).

## ⚙️ Configuration

Open `spotify_super_sync.py` and configure the following variables at the top of the file:

```python
# Spotify API Credentials
CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID") # or your ID string
CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET") # or your Secret string
REDIRECT_URI = "[http://127.0.0.1:8888/callback](http://127.0.0.1:8888/callback)"

# Target Playlist
PLAYLIST_LINK = "[https://open.spotify.com/playlist/](https://open.spotify.com/playlist/)..."

# Your Music Folder
LOCAL_MUSIC_PATH = r"C:\Path\To\Your\Music"

Getting Spotify Credentials
Go to the Spotify Developer Dashboard.

Create a new App.

In the App settings, add http://127.0.0.1:8888/callback to the Redirect URIs.

Copy your Client ID and Client Secret.

🚀 Usage
The script operates in two modes, controlled by the MODE variable in the script:

1. Folder Mode (Default)
Scans your local music directory and attempts to match every MP3 found.

Python

MODE = "FOLDER"
2. Text Mode
Processes a specific text file (FINAL_LOCAL_ONLY.txt) containing a list of filenames that previously failed.

Python

MODE = "TEXT"
Run the script:

Bash

python spotify_super_sync.py
🔒 Security Note
NEVER commit your CLIENT_SECRET or .cache file to GitHub.

Ensure your .gitignore file includes:

Plaintext

.cache
.cache-*
scan_progress.json
*.txt
📝 Output Files
FINAL_LOCAL_ONLY.txt: Songs that truly could not be found on Spotify (likely unreleased leaks or local edits).

CLASSICAL_FAILURES.txt: Classical music files separated for manual review.

scan_progress.json: Saves your spot so you can stop/resume the script.

🤝 Contributing
Feel free to fork this repo and submit pull requests if you find new regex patterns or edge cases!


### One Final Tip for GitHub
When you create the repository on GitHub, look for the text box that asks for a "Description." You can use this one-liner:
> *"A Python tool to sync local MP3s to Spotify, specialized in handling YouTube rips, unreleased leaks, and messy filenames."*

You are all set! Good luck with the upload.
