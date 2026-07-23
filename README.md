# Telangana ePASS GitHub Actions Checker

This repo scaffold checks the fixed Telangana ePASS Postmatric applications with Playwright in GitHub Actions.

## Files

- `.github/workflows/epass-check.yml`: installs Chromium, runs the checker, saves state, and opens a GitHub issue only when a new matching condition is found.
- `scripts/epass_check.py`: reads the official status page for the four configured applications.
- `epass-notification-state.md`: created automatically after the first successful run.

## Setup

1. Copy these files into a GitHub repository.
2. Go to the repository's **Actions** tab.
3. Open **Telangana ePASS check**.
4. Click **Run workflow**.

The workflow also runs daily at 22:45 IST. Change the cron line in `.github/workflows/epass-check.yml` if you want a different schedule.

Do not share your GitHub password or personal access token. The default `GITHUB_TOKEN` is enough for this workflow to update the state file and create an issue.

