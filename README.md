# Hate Speech Analyzer

WordPress plugin that adds a Gutenberg block for analysing hate speech in Facebook post comments. Designed to work with the [Humanity Theme](https://github.com/amnestywebsite/humanity-theme) by Amnesty International.

> **Note:** This is an independent open-source project, not affiliated with or endorsed by Amnesty International.

## Requirements

- WordPress 6.4+
- PHP 8.2+
- Python 3.10+
- Node.js 20+ (only for block compilation)
- [Humanity Theme](https://github.com/amnestywebsite/humanity-theme)

## Installation

### 1. Clone the plugin

```bash
cd wp-content/plugins/
git clone https://github.com/dmorbidi/hate-speech-analyzer
cd hate-speech-analyzer
```

### 2. Build the Gutenberg block

```bash
npm install
npm run build
```

### 3. Set up the Python environment

```bash
cd scripts/
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 4. Configure environment variables

Add the following to your environment (`~/.bashrc`, `~/.zshrc`, or your server config):

```bash
# Apify token — required in production mode
# Get yours at: https://console.apify.com/account/integrations
export APIFY_TOKEN="your_apify_token_here"

# Test mode — set to "1" to use local JSON file instead of calling Apify
# Recommended during development to avoid unnecessary API calls
export HSA_TEST_MODE="1"

# Path to the local test JSON file (optional)
# Default: scripts/estrazione_amnesty.json
export HSA_TEST_FILE="/path/to/your/file.json"
```

> **Security:** never commit your Apify token to the repository.
> Add `.env` to `.gitignore` if you use an env file.

### 5. Activate the plugin

Go to **WP Admin → Plugins** and activate *Hate Speech Analyzer*.

## Usage

1. Create or edit any WordPress page
2. Add the **Hate Speech Analyzer** block (find it in the block inserter)
3. Publish the page
4. On the frontend, paste a Facebook post URL and click **Analyze**

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

Each script can also be run standalone:

```bash
# Test scraping (test mode)
export AHA_TEST_MODE=1
python3 1_fb_comments_scraping.py "https://www.facebook.com/.../posts/..."

# Test classification
python3 2_comments_hate_analysis.py estrazione_amnesty.json

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

## Development

```bash
npm run start    # watch mode
npm run lint:js  # JS linting
```

## License

GPL-2.0-or-later
