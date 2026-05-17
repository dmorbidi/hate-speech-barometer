# Hate Speech Barometer

A WordPress plugin that adds a Gutenberg block for analysing hate speech in Facebook post comments. Developed and tested with the [Humanity Theme](https://github.com/amnestywebsite/humanity-theme), an open source WordPress theme designed for human rights organizations. Compatible with any WordPress theme.

> **Note:** This is an independent open-source proof-of-concept developed by a volunteer engaged in online hate speech monitoring. It is not affiliated with any organization.

---

## ⚠️ Privacy & GDPR Notice

This tool retrieves and processes publicly available Facebook comments. Comments may contain personal data including usernames and profile information.

- **Users are solely responsible** for ensuring their use of this tool complies with applicable privacy regulations, including GDPR.
- **Do not commit** any dataset containing real user data to public repositories.
- The sample dataset included in this repository (`scripts/anonymized_dataset_sample.json`) has been manually anonymized — all usernames and identifiable references to private individuals have been removed.
- This tool is intended for research and human rights monitoring purposes only, in line with the legitimate interest provisions of GDPR Article 6(1)(f).

---

## Demo

The demo below shows the tool analyzing a real public Facebook post and returning its hate-speech classification results.

https://github.com/user-attachments/assets/c1da500d-2e71-4074-9afb-9015be1ddbd2



---

## Requirements

- WordPress 6.4+
- PHP 8.2+
- Python 3.9+ (must match the Python version used by your server environment)
- Node.js 20+ (only for block compilation)

---

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
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

> **Note on Python version:** The venv must use the same Python version as your server environment to avoid binary incompatibility with compiled packages such as numpy. This project was developed and tested with Python 3.9 inside a Devilbox container. If you encounter import errors related to numpy or pandas, ensure your venv Python version matches your server's Python version.

> **Note on the AI model:** The HuggingFace model (`IMSyPP/hate_speech_it`) is downloaded automatically the first time you run the pipeline and cached in `scripts/.cache/`. It is not part of the venv and does not need to be reinstalled. The cache folder is excluded from the repository via `.gitignore`.

> **Note on the venv:** Never commit the `venv/` folder — it is already in `.gitignore`. Each user must recreate it locally after cloning.

### 4. Configure environment variables for local testing (optional)

If you want to test the Python scripts locally (see the "Python Pipeline" section), add the following to your environment (`~/.bashrc`, `~/.zshrc`):

```bash
# Apify token — required in production mode
# Get yours at: https://console.apify.com/account/integrations
export APIFY_TOKEN="your_apify_token_here"

# Test mode — set to "1" to use a local JSON file instead of calling Apify
# Recommended during development to avoid unnecessary API calls
export HSB_TEST_MODE="1"

# Path to the local test JSON file (optional)
# Default: scripts/anonymized_dataset_sample.json
export HSB_TEST_FILE="/path/to/your/anonymized_file.json"
```

> **Security:** never commit your Apify token to the repository.

### 5. Activate the plugin

Go to **WP Admin → Network Admin → Plugins** and activate *Hate Speech Barometer*.

> **Note:** Theme Options are accessible via **WP Admin → `admin.php?page=amnesty_theme_options_page`**. This is a known limitation of the Humanity Theme in multisite environments — the menu entry does not appear automatically in the single site dashboard.

---

## Usage

1. Create or edit any WordPress page
2. Add the **Hate Speech Barometer** block (find it in the block inserter under *Widgets*)
3. Publish the page
4. On the frontend, paste the URL of any public Facebook post and click **Analyze**

### Demo mode vs Live mode

The same variables set for local testing can be set in `wp-config.php` when running the tool through WordPress. The tool supports two operating modes:

**Demo mode** (no Apify calls — uses local dataset):
```php
putenv('HSB_TEST_MODE=1');
putenv('HSB_TEST_FILE=/absolute/path/to/anonymized_dataset_sample.json');
```

**Live mode** (real Facebook data via Apify):
```php
// Remove or comment out HSB_TEST_MODE and HSB_TEST_FILE
putenv('APIFY_TOKEN=your_apify_token_here');
```

In live mode, the tool retrieves real comments from the provided Facebook post URL. Analysis may take 1–2 minutes depending on the number of comments and Apify response time.

---

## Python Pipeline

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
export HSB_TEST_FILE=/path/to/anonymized_dataset_sample.json
python3 1_fb_comments_scraping.py "https://www.facebook.com/.../posts/..."

# Test classification
python3 2_comments_hate_analysis.py anonymized_dataset_sample.json

# Full pipeline test
python3 analyze.py "https://www.facebook.com/.../posts/..."
```

### KPIs

| KPI | Formula |
|-----|---------|
| `total_impact` | Σ confidence × (likesCount + 1) per category |
| `avg_impact` | total_impact / comment_count |

### Categories

| Label | Meaning |
|-------|---------|
| ACCEPTABLE | Acceptable content |
| INAPPROPRIATE | Inappropriate content |
| OFFENSIVE | Offensive content |
| VIOLENT | Violent content |

---

## REST API

| Method | Endpoint | Auth |
|--------|----------|------|
| `POST` | `/wp-json/hate-speech-barometer/v1/analyze` | WP nonce |

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

---

## Known Limitations

This is a proof-of-concept prototype. The following limitations are acknowledged, with suggested paths for resolution:

- **Facebook posts only** — Reels, Stories and other content types are not supported. *Solvable by integrating a dedicated Apify actor for each content type.*

- **Nested comments flattened** — Replies to comments are retrieved but treated as top-level comments, losing the conversational hierarchy. *Solvable by preserving the parent-child relationship in the data model and weighting nested replies accordingly.*

- **Comment limit** — By default, only the latest 50 comments (plus nested comments/replies up to 3 levels) are retrieved per post. *Configurable via the `resultsLimit` parameter in `1_fb_comments_scraping.py`. A production version would expose this as a user-facing setting.*

- **Local environment only** — The WordPress instance runs on a local development server. However, the comment scraping pipeline calls real external services (Apify) and processes actual Facebook data. Deploying to a production server would require minimal configuration changes.

- **Python via exec()** — The pipeline is currently invoked via PHP `exec()`, which is not suitable for high-traffic production use. *Solvable by exposing the pipeline as a Flask or FastAPI microservice, callable via `wp_remote_post()`. The HuggingFace Inference API supports batch processing — all comments can be classified in a single HTTP call, eliminating the need for a local AI model entirely.*

- **AI model accuracy** — The model (`IMSyPP/hate_speech_it`) was trained on general Italian social media content. Its accuracy on human rights specific discourse may be limited. *Solvable via fine-tuning on a domain-specific labeled dataset, which HuggingFace fully supports.*

- **Production scalability** — Many of the above limitations dissolve with a modest production budget: a Flask microservice on Railway or Render (~$7/month), HuggingFace Pro for reliable inference (~$9/month), and a standard WordPress hosting plan would yield a fully functional, scalable tool.

---

## Development

The following commands are useful only if you are actively developing the Gutenberg block:

```bash
npm run start    # watch mode — recompiles the block automatically on file changes
npm run lint:js  # JavaScript linting against WordPress coding standards
```

For standard use, `npm run build` (run once after cloning) is sufficient.

---

## Acknowledgements

This project was developed with the assistance of AI language models:

- **Google Gemini** (free tier) — used in the early stages of the Python pipeline development
- **Claude Sonnet 4.6** by Anthropic — used throughout the WordPress plugin development, Gutenberg block implementation, and documentation

The use of LLM assistance is disclosed in the interest of transparency. All architectural decisions, code review, testing, and domain knowledge (hate speech monitoring, GDPR compliance) were provided by the author.

---

## License

GPL-2.0-or-later
