"""Email results/report.json. Needs SMTP_* secrets and EMAIL_TO."""
import json
import os
import smtplib
from email.message import EmailMessage

r = json.load(open("results/report.json"))
s = r["summary"]
lines = [f"Repository: {r['repository']}", f"Branch: {r['branch']}",
         f"Commit: {r['commit_sha']}", f"Run: {r['pipeline_run_id']}",
         f"Overall: {r['overall_status'].upper()}",
         f"Total: {s['total']}  Passed: {s['passed']}  Failed: {s['failed']}", ""]
for t in r["tests"]:
    lines.append(f"- [{t['result'].upper()}] {t['name']}")
    if t.get("failure_message"):
        lines.append(f"    {t['failure_message']}")

msg = EmailMessage()
msg["Subject"] = f"[CI {r['overall_status'].upper()}] {r['repository']} {r['commit_sha'][:7]}"
msg["From"] = os.environ["SMTP_USER"]
msg["To"] = os.environ["EMAIL_TO"]
msg.set_content("\n".join(lines))
msg.add_attachment(json.dumps(r, indent=2).encode(), maintype="application",
                   subtype="json", filename="testreport.json")
with smtplib.SMTP(os.environ.get("SMTP_HOST", "smtp.gmail.com"),
                  int(os.environ.get("SMTP_PORT", 587))) as srv:
    srv.starttls()
    srv.login(os.environ["SMTP_USER"], os.environ["SMTP_PASSWORD"])
    srv.send_message(msg)
print("Email sent to", os.environ["EMAIL_TO"])
