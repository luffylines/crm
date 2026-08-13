# EXACT CODE CHANGES - Flask CRM Security Hardening

## Change 1: Add `is_safe_key()` and `get_user_draft_path()` Functions

**File:** app.py
**Line:** 166-217
**Status:** ✅ IMPLEMENTED

```python
def is_safe_key(key):
    """
    Validate that a file key does not contain path traversal sequences.
    Prevents attacks like ../user1_file, ..\\user1_file, etc.
    """
    if not key:
        return False
    safe_key = os.path.basename(str(key))
    traversal_patterns = ['..', '~', '//', '\\\\']
    for pattern in traversal_patterns:
        if pattern in safe_key:
            return False
    return safe_key == str(key)


def get_user_draft_path(key):
    """
    Generate a deterministic file path for a user's draft file.
    Uses the file_key directly (no auto-incrementing).
    This should be used for opening/saving/deleting existing files.
    
    Format: {DRAFT_DIR}/{username}_{key}_draft.xlsx
    """
    user = get_username()
    if not user or not key:
        return None
    if not is_safe_key(key):
        return None
    safe_key = os.path.basename(str(key))
    return os.path.join(DRAFT_DIR, f"{user}_{safe_key}_draft.xlsx")
```

**Why:**
- `is_safe_key()` blocks directory traversal attacks (../, ../../, etc.)
- `get_user_draft_path()` generates deterministic paths that ALWAYS resolve to the current user's namespace
- Uses `os.path.basename()` to strip any directory separators from the key

---

## Change 2: Add @login_required to `/contactout/search`

**File:** app.py
**Line:** 733-736
**Status:** ✅ IMPLEMENTED

**BEFORE:**
```python
@app.route("/contactout/search", methods=["POST"])
def contactout_search():
    data = request.get_json(silent=True) or {}
```

**AFTER:**
```python
@app.route("/contactout/search", methods=["POST"])
@login_required
def contactout_search():
    data = request.get_json(silent=True) or {}
```

**Why:**
- This route performs enrichment queries and uses API credits
- Should NOT be accessible to anonymous users
- All other enrichment routes already have @login_required

---

## Change 3: Secure `/open/<key>` Route with Path Validation

**File:** app.py
**Line:** 953-1001
**Status:** ✅ IMPLEMENTED

**BEFORE (VULNERABLE):**
```python
@app.route("/open/<key>")
@login_required
def open_file(key):
    user = get_username()
    draft_path = os.path.join(DRAFT_DIR, f"{user}_{key}_draft.xlsx")
    if not os.path.exists(draft_path):
        return jsonify({"error": "Draft not found"}), 404

    pkl = os.path.join(DRAFT_DIR, f"{user}_{key}.pkl")
    store_key = f"{user}::{key}"
    # ... rest of function
```

**AFTER (SECURE):**
```python
@app.route("/open/<key>")
@login_required
def open_file(key):
    user = get_username()
    # SECURITY: Validate key against path traversal attacks
    if not is_safe_key(key):
        return jsonify({"error": "Invalid file key"}), 400
    
    draft_path = get_user_draft_path(key)
    if not draft_path or not os.path.exists(draft_path):
        return jsonify({"error": "Draft not found"}), 404

    # Pickle file uses the same user::key format
    safe_key = os.path.basename(str(key))
    pkl = os.path.join(DRAFT_DIR, f"{user}_{safe_key}.pkl")
    store_key = f"{user}::{key}"
    # ... rest of function
```

**Key Security Improvements:**
1. ✅ `is_safe_key(key)` rejects `../`, `../../`, etc. with 400 error
2. ✅ `get_user_draft_path(key)` returns `None` if validation fails
3. ✅ Malicious keys are rejected BEFORE attempting file access
4. ✅ Returns 404 if file doesn't exist (doesn't reveal whether a user exists)

---

## Change 4: Fix `/upload` Route Key Extraction

**File:** app.py
**Line:** 1003-1049
**Status:** ✅ IMPLEMENTED

**BEFORE:**
```python
@app.route("/upload", methods=["POST"])
@login_required
def upload():
    file = request.files.get("file")
    if not file:
        return jsonify({"error": "No file uploaded"}), 400

    filename = file.filename
    draft_path = get_draft_path(filename)
    key = os.path.splitext(os.path.basename(draft_path))[0].replace("_draft", "")
    # ... rest of function
    return jsonify({"total": len(df), "columns": list(df.columns), "resume_index": resume_index, "resumed": os.path.exists(draft_path)})
```

**AFTER:**
```python
@app.route("/upload", methods=["POST"])
@login_required
def upload():
    file = request.files.get("file")
    if not file:
        return jsonify({"error": "No file uploaded"}), 400

    filename = file.filename
    # For new uploads, use get_draft_path (which auto-increments if needed)
    draft_path = get_draft_path(filename)
    # Extract the key from the path: user_KEY_draft.xlsx -> KEY
    user = get_username()
    draft_base = os.path.basename(draft_path)
    # Format: {user}_{key}_draft.xlsx
    prefix = f"{user}_"
    key = draft_base[len(prefix):].replace("_draft.xlsx", "")
    # ... rest of function
    return jsonify({"total": len(df), "columns": list(df.columns), "resume_index": resume_index, "resumed": os.path.exists(draft_path), "user": user})
```

**Why:**
- ✅ More explicit key extraction (better readability)
- ✅ Key is extracted ONLY after user-scoped path generation
- ✅ Added `user` to response for debugging/verification
- ✅ get_draft_path() ensures key always prefixed with current user

---

## Change 5: Fix `/save/<idx>` Route - Use Exact Session File Key

**File:** app.py
**Line:** 1143-1160
**Status:** ✅ IMPLEMENTED

**BEFORE (VULNERABLE):**
```python
    store["validated"].add(idx)
    store["df"] = df

    key = get_session_key()
    draft_path = get_draft_path(store["filename"])  # ❌ WRONG!
    # This might generate a different filename than the one opened!
    draft_df = df.copy()
    draft_df["_validated"] = draft_df.index.map(lambda i: "1" if i in store["validated"] else "")
    safe_write_excel(draft_df, draft_path)
    save_store(key, store)
```

**AFTER (SECURE):**
```python
    store["validated"].add(idx)
    store["df"] = df

    key = get_session_key()
    # SECURITY: Use the exact file_key from session for existing files
    # Do NOT use get_draft_path() which may generate a different filename
    file_key = session.get("file_key")
    if not file_key:
        return jsonify({"error": "No file loaded"}), 400
    draft_path = get_user_draft_path(file_key)
    if not draft_path:
        return jsonify({"error": "Invalid file key"}), 400
    draft_df = df.copy()
    draft_df["_validated"] = draft_df.index.map(lambda i: "1" if i in store["validated"] else "")
    safe_write_excel(draft_df, draft_path)
    save_store(key, store)
```

**Why This Was Critical:**
- `get_draft_path(store["filename"])` searches filesystem for existing files
- If a file with the same name exists elsewhere, could match wrong file
- `get_draft_path()` auto-increments: "leads_draft.xlsx" → "leads_2_draft.xlsx"
- **Now we use EXACT session file_key** set when file was opened/uploaded
- ✅ Guarantees we save to the correct user's file
- ✅ Validation ensures file_key hasn't been tampered with

---

## Change 6: Fix `/delete/<idx>` Route - Use Exact Session File Key

**File:** app.py
**Line:** 1174-1191
**Status:** ✅ IMPLEMENTED

**BEFORE (VULNERABLE):**
```python
    store["validated"] = {i if i < idx else i - 1 for i in store["validated"] if i != idx}

    key = get_session_key()
    draft_path = get_draft_path(store["filename"])  # ❌ WRONG!
    draft_df = df.copy()
    draft_df["_validated"] = draft_df.index.map(lambda i: "1" if i in store["validated"] else "")
    safe_write_excel(draft_df, draft_path)
    save_store(key, store)
```

**AFTER (SECURE):**
```python
    store["validated"] = {i if i < idx else i - 1 for i in store["validated"] if i != idx}

    key = get_session_key()
    # SECURITY: Use the exact file_key from session for existing files
    # Do NOT use get_draft_path() which may generate a different filename
    file_key = session.get("file_key")
    if not file_key:
        return jsonify({"error": "No file loaded"}), 400
    draft_path = get_user_draft_path(file_key)
    if not draft_path:
        return jsonify({"error": "Invalid file key"}), 400
    draft_df = df.copy()
    draft_df["_validated"] = draft_df.index.map(lambda i: "1" if i in store["validated"] else "")
    safe_write_excel(draft_df, draft_path)
    save_store(key, store)
```

**Why This Was Critical:**
- Delete operations MUST target the exact file that was opened
- ✅ Using session file_key ensures we delete from correct file
- ✅ Impossible for user to accidentally delete another user's file

---

## Summary of Changes

| Change | Location | Type | Impact |
|--------|----------|------|--------|
| Add `is_safe_key()` | Line 166-177 | New Function | Path traversal protection |
| Add `get_user_draft_path()` | Line 180-194 | New Function | Deterministic user-scoped paths |
| `/contactout/search` | Line 735 | Decorator | Authentication required |
| `/open/<key>` | Line 953-1001 | Validation + Path | Path traversal + secure path resolution |
| `/upload` | Line 1003-1049 | Key extraction | More explicit, verified |
| `/save/<idx>` | Line 1143-1160 | File path | Use session file_key instead of re-deriving |
| `/delete/<idx>` | Line 1174-1191 | File path | Use session file_key instead of re-deriving |

---

## Security Guarantees After Changes

### ✅ Per-User File Isolation
```
User1 uploads "leads.xlsx" → stored as "drafts/user1_abc123_draft.xlsx"
User2 uploads "leads.xlsx" → stored as "drafts/user2_xyz789_draft.xlsx"
User2 tries /open/abc123 → Returns 404 (not found)
User2 tries /open/../abc123 → Returns 400 (invalid key)
```

### ✅ No Path Traversal
```
/open/../user1_file → Blocked by is_safe_key()
/open/../../etc/passwd → Blocked by is_safe_key()
/open/....//....//etc → Blocked by is_safe_key()
```

### ✅ No File Collision
```
Same filename uploaded by multiple users → Different files per user
Resume works correctly → Uses session file_key
Save/Delete target correct file → Uses session file_key, not re-derived path
```

### ✅ No Privilege Escalation
```
Session["username"] set at login only, never from client request
Session["file_key"] validated with is_safe_key()
get_session_key() combines username::filekey securely
All file operations use this key, ensuring per-user isolation
```

---

## Deployment Instructions

1. **Backup current app.py**
   ```bash
   cp app.py app.py.backup
   ```

2. **Deploy updated app.py**
   - All changes are backwards compatible
   - No database migrations needed
   - No configuration changes needed

3. **Verify in Render**
   - Test user isolation
   - Test file operations
   - Monitor error logs for 400 (path traversal attempts)

4. **Optional: Cleanup old files**
   - No cleanup needed - old files remain readable
   - Users can re-upload if needed

---

## Testing Commands

### Manual curl Tests

```bash
# Test 1: Successful login
curl -X POST http://localhost:5000/login \
  -H "Content-Type: application/json" \
  -d '{"username": "user1", "password": "pass1"}' \
  -c cookies.txt

# Test 2: Upload file
curl -X POST http://localhost:5000/upload \
  -b cookies.txt \
  -F "file=@leads.xlsx"
# Response: {"total": 100, "user": "user1", ...}

# Test 3: Open file (valid key)
curl http://localhost:5000/open/abc123 \
  -b cookies.txt
# Response: {"total": 100, "resumed": true, ...}

# Test 4: Try path traversal (BLOCKED)
curl http://localhost:5000/open/../user2_file \
  -b cookies.txt
# Response: 400 {"error": "Invalid file key"}

# Test 5: Try to open another user's file (BLOCKED)
# (After logout and login as user2)
curl http://localhost:5000/open/abc123 \
  -b cookies2.txt
# Response: 404 {"error": "Draft not found"}
```

---

## Remaining Limitations (Not in Scope)

⚠️ **Render Filesystem is Temporary**
- Files are stored in local `drafts/` directory
- Files are NOT preserved across Render redeploys
- **Recommendation:** Implement persistent storage (S3, etc.) for production

⚠️ **No File Encryption at Rest**
- Files stored as plain Excel/pickle files
- **Recommendation:** Add AES encryption for sensitive data

⚠️ **API Key Security**
- ContactOut/Apollo keys in .env file
- **Recommendation:** Use Render environment variable encryption

These limitations are OUTSIDE the scope of this per-user isolation update.

