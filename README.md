# Canaima Weekly — Volunteer feedback

A lightweight interactive dashboard for GitHub Pages. Kobo submissions are fetched during a GitHub Actions build, aggregated in memory, and published only as dashboard JSON inside the Pages artifact. Raw submissions are never committed or uploaded as artifacts.

## Preview first

Requires Python 3.12 (no packages needed for API mode or the fictional demo).

```bash
python scripts/build.py --demo --output preview
python -m http.server 8000 --directory preview
```

Open http://localhost:8000. The included `preview` folder already contains a fictional demo. Do not upload it to the repository; it is ignored. Upload the project source including `.github/workflows/pages.yml` and `.gitignore`.

## Deploy on GitHub

1. Create a GitHub repository with default branch `main` and upload the contents of this project, including hidden `.github` and `.gitignore` files. Do not upload the ZIP itself, preview, raw exports, or credentials. A public repository is the simplest GitHub Pages setup; private-repository Pages availability depends on your plan.
2. In **Settings → Secrets and variables → Actions → Secrets**, add `KOBO_TOKEN` (your API token) and `KOBO_ASSET_UID` (the project UID from its Kobo URL). Never paste the token into source code or chat.
3. Under the **Variables** tab, add `KOBO_SERVER`: `https://kf.kobotoolbox.org` for the global server or `https://eu.kobotoolbox.org` for the EU server. A private Kobo server can also be supplied as an HTTPS origin.
4. In **Settings → Pages**, choose **GitHub Actions** as the publishing source.
5. Open **Actions → Refresh and deploy dashboard → Run workflow**. The deployment job displays the website link. Visitors do not need GitHub accounts.

The workflow also runs on pushes to main and every six hours at minute 17 UTC. Scheduled runs can be delayed by GitHub; inactive public repositories may have schedules disabled. A failed fetch/build prevents deployment and leaves the previous successful website in place. The page displays its last successful update time. No demo fallback is used in production. Repository/environment protection rules may require approval; configure these deliberately if unattended refresh is required.

## Data and calculations

The inspected export has `viaje` plus nine rating questions: `hr`, `education`, `logistics`, `im`, `sm`, `acompa`, `estadia`, `comidas`, `vuelos`. Nested Kobo group paths are supported by their final field name; ambiguous matches fail. Confirm that the live form uses this schema and ratings encoded as integers 1–5. HR, IM and SM retain the supplied abbreviations until their full names are confirmed.

Trip filters use `viaje`. Periods use trip dates, measured from the successful update date, and trends group published trips by calendar month. Missing/invalid dates are excluded with a coverage count. Missing/invalid ratings are excluded, never treated as zero. Question averages weight each valid answer equally. Support and trip composite scores use complete responses within the category and weight respondents equally. Low-rating percentages use individual question answers as the denominator. Alerts list published questions below 4.0; they are prompts for review, not statistical evidence.

Groups with fewer than five submissions are withheld. Questions and composites also require at least five valid responses per trip. Withheld values never enter the public JSON. Counts of excluded responses are reported for coverage; this is a simple publication threshold, not a formal anonymity guarantee. Confirm that publishing trip dates and aggregate results is appropriate for the NGO. A public website is accessible to anyone, not just people receiving the link. Comments and names are excluded entirely. Add qualitative feedback only through a separate, explicitly reviewed publication process.

The supplied Excel example contains three test records across two trips; neither passes the default threshold. The preview therefore uses fictional data, clearly labelled on the page. None of the uploaded names or text is packaged.

## Manual local export option

Install `openpyxl` locally if using Excel, then run:

```bash
python scripts/build.py --xlsx /path/to/export.xlsx --output dist
```

Keep the export outside the repository. API mode has no third-party dependencies. To refresh live data manually, use GitHub's Run workflow button instead of downloading Excel.

## Verify / maintain

```bash
python -m unittest discover -s tests
```

Change labels and field groups in `scripts/process_data.py`. The frontend uses plain HTML/CSS/JavaScript with native SVG and CSS charts, so it needs no CDN or frontend build tool. Relative paths work under a GitHub project URL. The workflow uploads only `dist`, with a one-day artifact retention period; the live website remains published until replaced. Production data is intentionally not committed back to GitHub.

Official references: [Kobo API v2](https://support.kobotoolbox.org/migrating_api.html), [Kobo API access](https://support.kobotoolbox.org/api.html), [GitHub Pages custom workflows](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages).

## Open questions and confidentiality

The demo includes six fictional Spanish comment cards, filterable across all four open questions: `pre_feedback` (preparation team), `feedback` (recurring Weekly Canaima team), `apoyo` (next volunteers), and `header_3` (additional recommendations). They do not follow trip/period filters, since they are design examples rather than dated submissions. The section is hidden in production, and no live open answers enter the published JSON.

The supplied form explicitly states that information is handled only by IM and Logistics. Real comments need a publication basis consistent with that statement before they can be used on a public dashboard, including any manually reviewed excerpts. Review the audience and publication basis for aggregate results too.
