# Assignment Submission Portal (CSC418 DevOps Lab Mid)

Flask portal + pytest tests + GitHub Actions CI that sends a JSON test report to a local receiver.

## Run the app
```bash
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
python -m app.app            # http://localhost:5000
```

## Run the tests
```bash
pytest -v
```

## Start the receiver (saves `testreport.json`)
```bash
python receiver/receiver.py 8000
```
Optional: `RECEIVER_TOKEN=mysecret python receiver/receiver.py 8000`.

## Getting the report to your computer
**Option A: self-hosted runner (no tunnel).**
1. Repo > Settings > Actions > Runners > New self-hosted runner, follow the steps on your laptop and keep `./run.sh` running.
2. Repo > Settings > Secrets and variables > Actions > Variables: `REPORT_RUNNER` = `self-hosted`.
3. Secret `REPORT_URL` = `http://localhost:8000/report`.

**Option B: GitHub-hosted runner + tunnel.**
1. Start the receiver, then `ngrok http 8000` (or `cloudflared tunnel --url http://localhost:8000`).
2. Secret `REPORT_URL` = `https://<tunnel-host>/report`. Update it if the tunnel URL changes.

Optional secret `RECEIVER_TOKEN` (must match the receiver's env var).

## Pipeline (`.github/workflows/ci.yml`)
- `test`: runs pytest on every push; a failing test fails the job.
- `report`: runs even when tests fail, builds the report from the JUnit XML, POSTs it to the receiver.
- `email` (bonus): emails the report. Secrets: `SMTP_HOST`, `SMTP_USER`, `SMTP_PASSWORD` (Gmail app password), `EMAIL_TO`.
- `deploy` (bonus): publishes `docs/` to GitHub Pages on `main` only if `test` passed. Enable it under Settings > Pages > Source: **GitHub Actions**.

## Demo script
1. Push as is: all tests pass, `testreport.json` shows `"overall_status": "passed"`.
2. Introduce a defect: in `app/app.py` delete `"registration_number": "Registration number is required.",` from `REQUIRED`. Push: tests fail, report shows `failed` with the failure message, Pages stays unchanged.
3. Restore the line, push: passing again.
