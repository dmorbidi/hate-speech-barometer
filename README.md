# Hate Speech Barometer

A WordPress plugin that adds a Gutenberg block for analysing hate speech in Facebook post comments. Designed to work with the [Humanity Theme](https://github.com/amnestywebsite/humanity-theme) by Amnesty International.

> **Note:** This is an independent open-source project developed by a volunteer member of the [Amnesty International Italia Hate Speech Task Force](https://www.amnesty.it). It is not an official Amnesty International product or service.

---

## ⚠️ Privacy & GDPR Notice

This tool retrieves and processes publicly available Facebook comments. Comments may contain personal data including usernames and profile information.

- **Users are solely responsible** for ensuring their use of this tool complies with applicable privacy regulations, including GDPR.
- **Do not commit** any dataset containing real user data to public repositories.
- The `scripts/estrazione_amnesty.json` test file is excluded from this repository via `.gitignore`. If you use a local test file, ensure it does not contain identifiable personal data before sharing it.
- This tool is intended for research and human rights monitoring purposes only, in line with the legitimate interest provisions of GDPR Article 6(1)(f).

---

## Requirements

- WordPress 6.4+
- PHP 8.2+
- Python 3.9+ (must match the Python version used by your server environment)
- Node.js 20+ (only for block compilation)
- [Humanity Theme](https://github.com/amnestywebsite/humanity-theme)

## Installation

### 1. Clone the plugin

```bash
cd wp-content/plugins/
git clone https://github.com/dmorbidi/hate-speech-barometer
cd hate-speech-barometer
```

### 2. Build the Gutenberg block

```bash
npm install
npm run build
```

### 3. Set up the Python environment

The venv must be created inside the `scripts/` folder so that `analyze.py` can find it automatically. Use the same Python version as your server environment to avoid binary incompatibility (e.g. numpy C-extensions).

```bash
cd scripts/
python3.9 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

> **Note on the AI model:** The HuggingFace model (`IMSyPP/hate_speech_it`) is downloaded automatically the first time you run the pipeline and cached in `scripts/.cache/`. It is not part of the venv and does not need to be reinstalled. The cache folder is excluded from the repository via `.gitignore`.

> **Note on the venv:** Never commit the `venv/` folder — it is already in `.gitignore`. Each user must recreate it locally after cloning.

### 4. Configure environment variables

Add the following to your environment (`~/.bashrc`, `~/.zshrc`, or your server config):

```bash
# Apify token — required in production mode
# Get yours at: https://console.apify.com/account/integrations
export APIFY_TOKEN="your_apify_token_here"

# Test mode — set to "1" to use a local JSON file instead of calling Apify
# Recommended during development to avoid unnecessary API calls
export HSB_TEST_MODE="1"

# Path to the local test JSON file (optional)
# Default: scripts/estrazione_amnesty.json
export HSB_TEST_FILE="/path/to/your/anonymized_file.json"
```

> **Security:** never commit your Apify token to the repository.

### 5. Activate the plugin

Go to **WP Admin → Network Admin → Plugins** and activate *Hate Speech Barometer*.

> **Note:** Theme Options are accessible via **WP Admin → `admin.php?page=amnesty_theme_options_page`**. This is a known limitation of the Humanity Theme in multisite environments — the menu entry does not appear automatically in the single site dashboard.

## Usage

1. Create or edit any WordPress page
2. Add the **Hate Speech Barometer** block (find it in the block inserter under *Widgets*)
3. Publish the page
4. On the frontend, paste the URL of any public Facebook post and click **Analyze**

## Python pipeline

Three scripts chained in memory — no temporary files written to disk:

```
1_fb_comments_scraping.py    → fetches comments from Apify (or local JSON in test mode)
        ↓ list[dict]
2_comments_hate_analysis.py  → classifies with HuggingFace (IMSyPP/hate_speech_it)
        ↓ pd.DataFrame
3_post_hate_evaluation.py    → calculates hate impact KPIs
        ↓ list[dict]
analyze.py                   → WordPress entry point, outputs JSON to stdout
```

Each script can also be run standalone for testing:

```bash
cd scripts/
source venv/bin/activate

# Test scraping (test mode — no Apify calls)
export HSB_TEST_MODE=1
export HSB_TEST_FILE=/path/to/anonymized_file.json
python3 1_fb_comments_scraping.py "https://www.facebook.com/.../posts/..."

# Test classification
python3 2_comments_hate_analysis.py anonymized_file.json

# Test KPI calculation
python3 3_post_hate_evaluation.py analisi_odio_con_consenso.csv

# Full pipeline test
python3 analyze.py "https://www.facebook.com/.../posts/..."
```

### KPIs

| KPI | Formula |
|-----|---------|
| `impatto_totale` | Σ confidenza × (likesCount + 1) per categoria |
| `impatto_medio` | impatto_totale / n_commenti |

### Categories

| Label | Meaning |
|-------|---------|
| ACCEPTABLE | Acceptable content |
| INAPPROPRIATE | Inappropriate content |
| OFFENSIVE | Offensive content |
| VIOLENT | Violent content |

## REST API

| Method | Endpoint | Auth |
|--------|----------|------|
| `POST` | `/wp-json/hate-speech-analyzer/v1/analyze` | WP nonce |

### Request

```json
{ "url": "https://www.facebook.com/page/posts/123456" }
```

### Response

```json
{
    "post_title": "Post title",
    "post_url": "https://www.facebook.com/...",
    "stats": [
        { "categoria": "ACCEPTABLE",    "n_commenti": 72, "totale_likes": 239, "impatto_totale": 237.46, "impatto_medio": 3.30 },
        { "categoria": "INAPPROPRIATE", "n_commenti": 0,  "totale_likes": 0,   "impatto_totale": 0.0,   "impatto_medio": 0.0  },
        { "categoria": "OFFENSIVE",     "n_commenti": 17, "totale_likes": 137, "impatto_totale": 107.39, "impatto_medio": 6.32 },
        { "categoria": "VIOLENT",       "n_commenti": 4,  "totale_likes": 2,   "impatto_totale": 3.02,  "impatto_medio": 0.75 }
    ]
}
```

## Known Limitations

This is a proof-of-concept prototype with the following limitations:

- Analyzes one Facebook post at a time
- The AI model (`IMSyPP/hate_speech_it`) is optimized for Italian language content
- Requires a local server environment (not production-ready)
- Apify free tier has usage limits — use test mode for development
- The plugin requires Python 3.9 to match Devilbox container environment

## Development

```bash
npm run start    # watch mode
npm run lint:js  # JS linting
```

## License

GPL-2.0-or-later
