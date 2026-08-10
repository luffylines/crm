from flask import Flask, request, jsonify, render_template, send_file, session, redirect, url_for
import pandas as pd
import requests as req
import re
import io
import os
import json
import pickle
import stat
from datetime import datetime
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
import time
from functools import wraps

app = Flask(__name__)
app.secret_key = "revalidation_tool_secret_2024"

DRAFT_DIR = "drafts"
os.makedirs(DRAFT_DIR, exist_ok=True)

# Per-file in-memory store: { session_key: { df, original_df, filename, validated } }
stores = {}


def load_users():
    path = os.path.join(os.path.dirname(__file__), "users.json")
    with open(path) as f:
        return {u["username"]: u["password"] for u in json.load(f)["users"]}


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("username"):
            return jsonify({"error": "Not logged in"}), 401
        return f(*args, **kwargs)
    return decorated


def get_username():
    return session.get("username", "")

ACCEPTED_TITLES = [
    "office manager", "it manager", "cfo", "coo", "controller",
    "general manager", "administrative assistant", "operations manager",
    "chief financial officer", "chief operating officer"
]

geolocator = Nominatim(user_agent="revalidation_tool")


def safe_write_excel(df, draft_path):
    os.makedirs(os.path.dirname(draft_path) or ".", exist_ok=True)

    if os.path.exists(draft_path):
        try:
            os.chmod(draft_path, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IWGRP | stat.S_IROTH | stat.S_IWOTH)
        except Exception:
            pass

    base, ext = os.path.splitext(draft_path)
    ext = ext or '.xlsx'
    stamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
    tmp_path = f"{base}.tmp_{stamp}{ext}"
    fallback_path = f"{base}.autosave_{stamp}{ext}"

    try:
        df.to_excel(tmp_path, index=False)
        try:
            os.replace(tmp_path, draft_path)
        except PermissionError:
            # Windows can block a rename/replace if the workbook is open/locked elsewhere.
            # Keep the save flow alive by writing the latest workbook under a fallback name.
            try:
                df.to_excel(fallback_path, index=False)
            except Exception:
                pass
            return False
        except OSError:
            try:
                df.to_excel(fallback_path, index=False)
            except Exception:
                pass
            return False
        return True
    except Exception:
        try:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
        except Exception:
            pass
        try:
            df.to_excel(fallback_path, index=False)
        except Exception:
            pass
        return False
    finally:
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception:
                pass


def get_draft_path(filename):
    base = os.path.splitext(os.path.basename(filename))[0]
    user = get_username()
    prefix = f"{user}_" if user else ""
    return os.path.join(DRAFT_DIR, f"{prefix}{base}_draft.xlsx")


def get_session_key():
    if "file_key" not in session:
        session["file_key"] = None
    user = get_username()
    key = session.get("file_key")
    if key and user:
        return f"{user}::{key}"
    return key


def get_store():
    key = get_session_key()  # format: "username::filekey"
    if not key:
        return None
    if key in stores:
        return stores[key]
    # Try loading from pickle
    parts = key.split("::", 1)
    if len(parts) == 2:
        pkl_name = f"{parts[0]}_{parts[1]}.pkl"
    else:
        pkl_name = f"{key}.pkl"
    pkl = os.path.join(DRAFT_DIR, pkl_name)
    if os.path.exists(pkl):
        try:
            with open(pkl, "rb") as f:
                stores[key] = pickle.load(f)
            return stores[key]
        except Exception:
            pass
    return None


def save_store(key, store):
    stores[key] = store
    # key is "username::filekey" — derive pickle path
    parts = key.split("::", 1)
    if len(parts) == 2:
        pkl_name = f"{parts[0]}_{parts[1]}.pkl"
    else:
        pkl_name = f"{key}.pkl"
    pkl = os.path.join(DRAFT_DIR, pkl_name)
    try:
        with open(pkl, "wb") as f:
            pickle.dump(store, f)
    except Exception:
        pass


def clean_phone(phone):
    if not phone:
        return ""
    digits = re.sub(r'\D', '', str(phone))
    if digits.startswith('1') and len(digits) == 11:
        digits = digits[1:]
    return digits


TOLL_FREE = {800, 833, 844, 855, 866, 877, 888}


def validate_phone(phone):
    digits = clean_phone(phone)
    if len(digits) != 10:
        return False, "Phone must be exactly 10 digits"
    prefix = int(digits[:3])
    if prefix in TOLL_FREE:
        return False, f"Toll-free numbers ({prefix}) not accepted"
    return True, "Valid"


def validate_email(email):
    if not email or str(email).strip() == "" or str(email).strip().lower() == "nan":
        return False, "Missing"
    if re.match(r'^[\w\.-]+@[\w\.-]+\.\w{2,}$', str(email).strip()):
        return True, "Valid"
    return False, "Invalid format"


def validate_website(url):
    if not url or str(url).strip() == "" or str(url).strip().lower() == "nan":
        return False, "Missing"
    try:
        url = str(url).strip()
        if not url.startswith("http"):
            url = "https://" + url
        resp = req.get(url, timeout=7, allow_redirects=True)
        if resp.status_code < 400:
            return True, "Active"
        return False, f"HTTP {resp.status_code}"
    except Exception:
        return False, "Unreachable"


def validate_address(street, city, state, zipcode):
    if not all([street, city, state, zipcode]):
        return False, "Incomplete address"
    addr = str(street).strip().upper()
    if re.search(r'\bP\.?\s*O\.?\s*BOX\b', addr):
        return False, "PO BOX not accepted"
    full_address = f"{street}, {city}, {state} {zipcode}, USA"
    try:
        time.sleep(1)
        location = geolocator.geocode(full_address, timeout=10)
        if location:
            return True, "Valid"
        return False, "Address not found"
    except GeocoderTimedOut:
        return False, "Geocoder timeout"
    except Exception as e:
        return False, f"Error: {str(e)}"


def validate_title(title):
    if not title or str(title).strip().lower() == "nan":
        return False, "Missing"
    title_lower = str(title).strip().lower()
    for accepted in ACCEPTED_TITLES:
        if accepted in title_lower:
            return True, "Valid"
    return False, "Title not in accepted list"


def calculate_rank(row, validations):
    website_ok = validations["website"]["valid"]

    def has_value(key):
        v = str(row.get(key, "")).strip()
        return bool(v) and v.lower() != "nan"

    company_ok      = has_value("Company")
    address_ok      = has_value("Street") and has_value("City") and has_value("State") and has_value("Zip Code")
    phone_ok        = has_value("Phone")
    title_ok        = has_value("Title")
    email_ok        = has_value("Email")
    has_alt_contact = has_value("Alt. Contact Info")
    has_alt_phone   = has_value("Alternate Phone")

    missing = []
    if not company_ok: missing.append("Company Name")
    if not address_ok: missing.append("Address")
    if not phone_ok:   missing.append("Phone")
    if not title_ok:   missing.append("Title")
    if not email_ok:   missing.append("Email")

    if not website_ok:
        return "good", f"Website is unreachable or missing ({validations['website']['msg']})"
    if missing:
        return "bad", f"Missing SOP field(s): {', '.join(missing)}"
    if has_alt_contact and has_alt_phone:
        return "best", "All SOP fields complete with alt. contact and alt. phone"
    if not has_alt_contact and not has_alt_phone:
        return "better", "All SOP fields complete but missing alt. contact and alt. phone"
    if not has_alt_contact:
        return "better", "All SOP fields complete but missing alt. contact info"
    return "better", "All SOP fields complete but missing alt. phone"


def run_validations(row):
    phone_valid, phone_msg   = validate_phone(row.get("Phone", ""))
    email_valid, email_msg   = validate_email(row.get("Email", ""))
    website_valid, website_msg = validate_website(row.get("Website", ""))
    address_valid, address_msg = validate_address(
        row.get("Street", ""), row.get("City", ""),
        row.get("State", ""), row.get("Zip Code", "")
    )
    title_valid, title_msg   = validate_title(row.get("Title", ""))
    validations = {
        "phone":   {"valid": phone_valid,   "msg": phone_msg},
        "email":   {"valid": email_valid,   "msg": email_msg},
        "website": {"valid": website_valid, "msg": website_msg},
        "address": {"valid": address_valid, "msg": address_msg},
        "title":   {"valid": title_valid,   "msg": title_msg},
    }
    suggested_rank, rank_reason = calculate_rank(row, validations)
    return validations, suggested_rank, rank_reason


@app.route("/login", methods=["POST"])
def login():
    data = request.json or {}
    users = load_users()
    username = data.get("username", "").strip().lower()
    password = data.get("password", "")
    if username in users and users[username] == password:
        session["username"] = username
        return jsonify({"ok": True, "username": username})
    return jsonify({"error": "Invalid username or password"}), 401


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"ok": True})


@app.route("/me")
def me():
    username = session.get("username")
    if not username:
        return jsonify({"logged_in": False})
    return jsonify({"logged_in": True, "username": username})


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/files")
@login_required
def list_files():
    files = []
    user = get_username()
    prefix = f"{user}_"
    for fname in os.listdir(DRAFT_DIR):
        if not fname.endswith("_draft.xlsx"):
            continue
        if not fname.startswith(prefix):
            continue
        draft_path = os.path.join(DRAFT_DIR, fname)
        base = fname[len(prefix):].replace("_draft.xlsx", "")
        try:
            df = pd.read_excel(draft_path, dtype=str).fillna("")
            total = len(df)
            done = int((df.get("_validated", pd.Series(dtype=str)) == "1").sum()) if "_validated" in df.columns else 0
            modified = os.path.getmtime(draft_path)
            modified_str = datetime.fromtimestamp(modified).strftime("%b %d, %Y %I:%M %p")
            files.append({
                "key": base,
                "filename": base + ".xlsx",
                "total": total,
                "done": done,
                "modified": modified_str,
                "modified_ts": modified
            })
        except Exception:
            pass
    files.sort(key=lambda x: x["modified_ts"], reverse=True)
    for f in files:
        del f["modified_ts"]
    return jsonify({"files": files})


@app.route("/open/<key>")
@login_required
def open_file(key):
    user = get_username()
    draft_path = os.path.join(DRAFT_DIR, f"{user}_{key}_draft.xlsx")
    if not os.path.exists(draft_path):
        return jsonify({"error": "Draft not found"}), 404

    pkl = os.path.join(DRAFT_DIR, f"{user}_{key}.pkl")
    store_key = f"{user}::{key}"
    if os.path.exists(pkl):
        try:
            with open(pkl, "rb") as f:
                store = pickle.load(f)
            stores[store_key] = store
            session["file_key"] = key
            validated = store["validated"]
            resume_index = max(validated) + 1 if validated else 0
            if resume_index >= len(store["df"]):
                resume_index = len(store["df"]) - 1
            return jsonify({"total": len(store["df"]), "resume_index": resume_index, "resumed": True})
        except Exception:
            pass

    # Load from draft xlsx only
    try:
        df = pd.read_excel(draft_path, dtype=str).fillna("")
        validated = set()
        if "_validated" in df.columns:
            validated = set(df.index[df["_validated"] == "1"].tolist())
            df = df.drop(columns=["_validated"])
        if "Lead Ranking" not in df.columns:
            df["Lead Ranking"] = ""
        store = {"df": df, "original_df": df.copy(), "filename": key + ".xlsx", "validated": validated}
        stores[store_key] = store
        session["file_key"] = key
        resume_index = max(validated) + 1 if validated else 0
        return jsonify({"total": len(df), "resume_index": resume_index, "resumed": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/upload", methods=["POST"])
@login_required
def upload():
    file = request.files.get("file")
    if not file:
        return jsonify({"error": "No file uploaded"}), 400

    filename = file.filename
    base = os.path.splitext(os.path.basename(filename))[0]
    key = base

    df = pd.read_excel(file, dtype=str).fillna("")
    if "be" in df.columns:
        df.rename(columns={"be": "Lead Ranking"}, inplace=True)
    if "Lead Ranking" not in df.columns:
        df["Lead Ranking"] = ""

    validated = set()
    resume_index = 0
    draft_path = get_draft_path(filename)

    if os.path.exists(draft_path):
        try:
            draft_df = pd.read_excel(draft_path, dtype=str).fillna("")
            if "_validated" in draft_df.columns:
                validated = set(draft_df.index[draft_df["_validated"] == "1"].tolist())
                for col in draft_df.columns:
                    if col != "_validated" and col in df.columns:
                        df[col] = draft_df[col]
                resume_index = max(validated) + 1 if validated else 0
        except Exception:
            pass

    store = {"df": df, "original_df": df.copy(), "filename": filename, "validated": validated}
    session["file_key"] = key
    store_key = get_session_key()
    save_store(store_key, store)

    return jsonify({"total": len(df), "columns": list(df.columns), "resume_index": resume_index, "resumed": os.path.exists(draft_path)})


@app.route("/row/<int:idx>")
@login_required
def get_row(idx):
    store = get_store()
    if not store:
        return jsonify({"error": "No file loaded"}), 400
    df = store["df"]
    if idx >= len(df):
        return jsonify({"done": True})
    row = df.iloc[idx].to_dict()
    validations, suggested_rank, rank_reason = run_validations(row)
    return jsonify({"row": row, "index": idx, "total": len(df), "validations": validations,
                    "suggested_rank": suggested_rank, "rank_reason": rank_reason,
                    "is_validated": idx in store["validated"]})


@app.route("/progress")
@login_required
def get_progress():
    store = get_store()
    if not store:
        return jsonify({"error": "No file loaded"}), 400
    df = store["df"]
    validated = store["validated"]
    rows, rows_full = [], []
    for i, row in df.iterrows():
        done = i in validated
        rows.append({"index": i, "company": row.get("Company", ""), "rank": row.get("Lead Ranking", ""),
                     "validated_by": row.get("Validated By", ""), "done": done})
        full = row.to_dict()
        full["_index"] = i
        full["_done"] = done
        rows_full.append(full)
    return jsonify({"rows": rows, "rows_full": rows_full, "total": len(df),
                    "done_count": sum(1 for i in validated if i < len(df))})


@app.route("/save/<int:idx>", methods=["POST"])
@login_required
def save_row(idx):
    store = get_store()
    if not store:
        return jsonify({"error": "No file loaded"}), 400
    df = store["df"]
    original_df = store.get("original_df")
    data = request.json

    changed, added, removed = [], [], []
    TRACK_COLS = ["Website", "No. of Employees", "Company Industry", "First Name", "Last Name",
                  "Title", "Email", "Phone", "Alt. Contact Info", "Alternate Phone", "Street", "City", "State", "Zip Code"]
    if original_df is not None and idx < len(original_df):
        orig_row = original_df.iloc[idx]
        for col in TRACK_COLS:
            new_val = str(data.get(col, "")).strip()
            old_val = str(orig_row.get(col, "")).strip() if col in orig_row else ""
            if old_val and not new_val:
                removed.append(col)
            elif not old_val and new_val:
                added.append(col)
            elif old_val and new_val and old_val != new_val:
                changed.append(col)

    parts = []
    if changed: parts.append("Changes: " + ", ".join(changed))
    if removed: parts.append("Removed: " + ", ".join(removed))
    if added:   parts.append("Added: " + ", ".join(added))
    changes_text = " | ".join(parts)

    for key, value in data.items():
        if key in df.columns:
            df.at[idx, key] = value

    if "Notes" in df.columns and changes_text:
        lines = [l for l in str(df.at[idx, "Notes"]).strip().split("\n")
                 if not l.startswith(("Changes:", "Added:", "Removed:"))]
        lines.append(changes_text)
        df.at[idx, "Notes"] = "\n".join(lines).strip()

    store["validated"].add(idx)
    store["df"] = df

    key = get_session_key()
    draft_path = get_draft_path(store["filename"])
    draft_df = df.copy()
    draft_df["_validated"] = draft_df.index.map(lambda i: "1" if i in store["validated"] else "")
    safe_write_excel(draft_df, draft_path)
    save_store(key, store)

    return jsonify({"ok": True, "done_count": sum(1 for i in store["validated"] if i < len(df)), "changes_text": changes_text})


@app.route("/delete/<int:idx>", methods=["POST"])
@login_required
def delete_row(idx):
    store = get_store()
    if not store:
        return jsonify({"error": "No file loaded"}), 400
    df = store["df"].drop(index=idx).reset_index(drop=True)
    store["df"] = df
    if store.get("original_df") is not None:
        store["original_df"] = store["original_df"].drop(index=idx).reset_index(drop=True)
    store["validated"] = {i if i < idx else i - 1 for i in store["validated"] if i != idx}

    key = get_session_key()
    draft_path = get_draft_path(store["filename"])
    draft_df = df.copy()
    draft_df["_validated"] = draft_df.index.map(lambda i: "1" if i in store["validated"] else "")
    safe_write_excel(draft_df, draft_path)
    save_store(key, store)

    return jsonify({"ok": True, "total": len(df)})


@app.route("/download")
@login_required
def download():
    store = get_store()
    if not store:
        return jsonify({"error": "No file loaded"}), 400
    df = store["df"]
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False)
    output.seek(0)
    filename = store["filename"].replace(".xlsx", "_validated.xlsx")
    return send_file(output, download_name=filename, as_attachment=True,
                     mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
