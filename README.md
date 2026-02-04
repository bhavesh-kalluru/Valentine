# Valentine Ask (Flask) — v10

### Change you asked for
- Removed BOTH decorative heart images (left + right).
- Now the result shows ONLY the quote centered.

## Run locally
After unzipping, `cd` into the folder that contains `app.py`:

```bash
cd valentine_app
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

PORT=5050 python app.py
```

Open http://localhost:5050/


### v11 change
- After clicking **Yes**, the UI switches to **quote-only mode** (title/subtitle/button/footer hidden).
