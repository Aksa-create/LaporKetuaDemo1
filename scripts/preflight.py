"""Static release checks for LaporKetua. Does not replace live integration tests."""
from pathlib import Path
import re
import sys
from jinja2 import Environment

ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = ROOT / "app" / "templates"
errors = []
checks = []

# Python syntax
import compileall
if compileall.compile_dir(str(ROOT / "app"), quiet=1) and compileall.compile_file(str(ROOT / "run.py"), quiet=1):
    checks.append("Python syntax: PASS")
else:
    errors.append("Python syntax: FAIL")

# Jinja syntax
for path in sorted(TEMPLATES.rglob("*.html")):
    try:
        Environment().parse(path.read_text(encoding="utf-8"))
    except Exception as exc:
        errors.append(f"Jinja syntax: {path.relative_to(ROOT)}: {exc}")
if not errors:
    checks.append("Jinja template parsing: PASS")

# Every POST form must submit CSRF token as a hidden input (not visible text).
for path in sorted(TEMPLATES.rglob("*.html")):
    source = path.read_text(encoding="utf-8")
    for match in re.finditer(r"<form\b[\s\S]*?</form>", source, flags=re.I):
        form = match.group(0)
        method = re.search(r"\bmethod\s*=\s*['\"]?([a-z]+)", form, flags=re.I)
        if method and method.group(1).lower() == "post":
            if not re.search(r'<input\b[^>]*type=["\']hidden["\'][^>]*name=["\']csrf_token["\']', form, flags=re.I) and not re.search(r'<input\b[^>]*name=["\']csrf_token["\'][^>]*type=["\']hidden["\']', form, flags=re.I):
                errors.append(f"Missing hidden CSRF input: {path.relative_to(ROOT)}")
if not any("Missing hidden CSRF" in e for e in errors):
    checks.append("POST form CSRF fields: PASS")

# RT list contract
init = (ROOT / "app" / "__init__.py").read_text(encoding="utf-8")
expected = '["01", "02", "03", "04", "05", "06", "07", "08", "09", "11", "12", "13", "14"]'
if expected in init:
    checks.append("RW 06 RT reference list (13 RT, no RT 10): PASS")
else:
    errors.append("RW 06 RT reference list does not match agreed list")

# Required brand assets
for rel in ["app/static/icons/laporketua-logo.svg", "app/static/icons/icon-192.png", "app/static/icons/icon-512.png", "app/static/manifest.webmanifest"]:
    p = ROOT / rel
    if p.exists() and p.stat().st_size > 0:
        checks.append(f"Asset exists: {rel}")
    else:
        errors.append(f"Missing/empty asset: {rel}")

# Front-end JS syntax (if Node is available)
import shutil, subprocess
node = shutil.which("node")
if node:
    result = subprocess.run([node, "--check", str(ROOT / "app/static/js/app.js")], capture_output=True, text=True)
    if result.returncode == 0:
        checks.append("JavaScript syntax: PASS")
    else:
        errors.append("JavaScript syntax: " + result.stderr.strip())
else:
    checks.append("JavaScript syntax: SKIPPED (Node.js not installed)")


# Requested workflow revisions
feature_checks = {
    "Login role selector and server-side role match": (ROOT / "app/templates/auth/login.html").read_text(encoding="utf-8").find('name="role"') >= 0 and 'user.role == selected_role' in (ROOT / "app/routes/auth.py").read_text(encoding="utf-8"),
    "Report form has incident RT and location landmark": all(token in (ROOT / "app/templates/warga/report_form.html").read_text(encoding="utf-8") for token in ['name="rt_number"', 'name="location_detail"']),
    "Report stores incident RT independently of resident profile": 'rt_number=rt_number, location_detail=location_detail' in (ROOT / "app/routes/reports.py").read_text(encoding="utf-8"),
    "Admin verify endpoint and visible verify controls": 'def verify_report' in (ROOT / "app/routes/admin.py").read_text(encoding="utf-8") and 'admin.verify_report' in (ROOT / "app/templates/admin/reports.html").read_text(encoding="utf-8"),
    "Petugas dashboard shows incident location": 'r.location_detail' in (ROOT / "app/templates/petugas/dashboard.html").read_text(encoding="utf-8"),
    "Existing database migration script exists": (ROOT / "scripts/migrate_report_location_detail.py").exists(),
}
for label, passed in feature_checks.items():
    if passed:
        checks.append(label + ": PASS")
    else:
        errors.append(label + ": FAIL")

# Public login must expose only resident and field-officer roles; Admin has separate auth.
login_template = (ROOT / "app/templates/auth/login.html").read_text(encoding="utf-8")
auth_routes = (ROOT / "app/routes/auth.py").read_text(encoding="utf-8")
admin_routes = (ROOT / "app/routes/admin.py").read_text(encoding="utf-8")
admin_template = ROOT / "app/templates/admin/login.html"
if 'value="admin"' not in login_template and 'allowed_roles = {"warga", "petugas"}' in auth_routes:
    checks.append("Public login limited to Warga/Petugas: PASS")
else:
    errors.append("Public login must not offer or accept Admin role")
if 'def login()' in admin_routes and 'user.role == "admin"' in admin_routes and admin_template.exists():
    checks.append("Dedicated Admin authentication endpoint: PASS")
else:
    errors.append("Dedicated Admin authentication endpoint missing or not role-validated")

for item in checks:
    print("[PASS]", item)
for item in errors:
    print("[FAIL]", item)
print(f"\nResult: {len(checks)} passed, {len(errors)} failed")
sys.exit(1 if errors else 0)
