# UK Optometry Locum Shifts Scraper

Automated daily scraper for UK Locum Optometry shifts. Feeds a visual heatmap dashboard.

## Setup

1.  **Install Python 3.11+**
2.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    playwright install chromium
    ```

## Running Locally

Set environment variables for credentials and run:

```bash
python main.py
```

## Supported Agencies

| Agency | Status |
| :--- | :--- |
| LocateALocum | ✅ Active |
| Locumbell | ✅ Active |
| Vision Express (via Locumbell) | ✅ Active |
| Locumotive | ✅ Active |
| Team Locum | ✅ Active |

## Automation

This repo is configured with **GitHub Actions**. It runs daily at 02:00 UTC.
Ensure you add all credentials as **Repository Secrets** in GitHub Settings.
