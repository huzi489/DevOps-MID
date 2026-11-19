import json
import os
import threading
from urllib.parse import urlparse

from flask import Flask, jsonify, render_template_string, request

REQUIRED = {
    "name": "Name is required.",
    "registration_number": "Registration number is required.",
    "assignment_title": "Assignment title is required.",
    "submission_url": "Submission URL is required.",
}


def is_valid_url(value):
    if not value or any(c.isspace() for c in value):
        return False
    try:
        p = urlparse(value)
    except ValueError:
        return False
    if p.scheme not in ("http", "https") or not p.hostname:
        return False
    return "." in p.hostname or p.hostname == "localhost"


def validate_submission(data):
    errors = {}
    for field, msg in REQUIRED.items():
        if not str(data.get(field, "")).strip():
            errors[field] = msg
    url = str(data.get("submission_url", "")).strip()
    if url and not is_valid_url(url):
        errors["submission_url"] = "Submission URL is invalid."
    return errors


PAGE = """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Assignment Submission Portal</title>
<style>body{font-family:system-ui,sans-serif;max-width:640px;margin:2rem auto;padding:0 1rem}
input,button{display:block;width:100%;padding:.6rem;margin:.4rem 0;box-sizing:border-box}
.err{color:#b00020}.ok{color:#0a7d2c}li{margin:.4rem 0}</style></head><body>
<h1>Assignment Submission Portal</h1>
<form id="f"><input name="name" placeholder="Name"><input name="registration_number" placeholder="Registration number">
<input name="assignment_title" placeholder="Assignment title"><input name="submission_url" placeholder="Submission URL (https://...)">
<button>Submit</button></form><p id="msg"></p><h2>Submissions</h2><ul id="list"></ul>
<script>
const msg=document.getElementById('msg'),list=document.getElementById('list');
async function load(){const r=await fetch('/submissions');const d=await r.json();
list.innerHTML='';d.forEach(s=>{const li=document.createElement('li');
li.textContent=s.name+' ('+s.registration_number+') - '+s.assignment_title+' - '+s.submission_url;list.appendChild(li)})}
document.getElementById('f').onsubmit=async e=>{e.preventDefault();
const body=Object.fromEntries(new FormData(e.target));
const r=await fetch('/submit',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
const d=await r.json();
if(r.ok){msg.className='ok';msg.textContent='Submission saved.';e.target.reset();load()}
else{msg.className='err';msg.textContent=Object.values(d.errors).join(' ')}};
load();
</script></body></html>"""


def create_app(data_file=None):
    app = Flask(__name__)
    path = data_file or os.environ.get("DATA_FILE", "data/submissions.json")
    lock = threading.Lock()

    def read():
        if not os.path.exists(path):
            return []
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)

    @app.get("/")
    def index():
        return render_template_string(PAGE)

    @app.get("/submissions")
    def submissions():
        return jsonify(read())

    @app.post("/submit")
    def submit():
        data = request.get_json(silent=True) or request.form.to_dict()
        errors = validate_submission(data)
        if errors:
            return jsonify({"errors": errors}), 400
        record = {k: str(data[k]).strip() for k in REQUIRED}
        with lock:
            items = read()
            items.append(record)
            os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
            with open(path, "w", encoding="utf-8") as fh:
                json.dump(items, fh, indent=2)
        return jsonify(record), 201

    return app


if __name__ == "__main__":
    create_app().run(port=int(os.environ.get("PORT", 5000)), debug=False)
