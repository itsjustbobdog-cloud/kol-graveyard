# 🪦 KOL Graveyard

Where web3 KOLs come to rest. Exposing paid promotions, one tombstone at a time.

**Built by Archon while Russ slept.**

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/itsjustbobdog-cloud/kol-graveyard)

---

## What It Does

The KOL Graveyard is a satirical tool that:
- Analyzes X handles for paid promotion patterns
- Generates savage but fair roasts based on shill frequency
- Creates permanent tombstones in a public graveyard
- Tracks dead projects vs surviving ones
- Exposes the truth (with receipts)

### Features

🔥 **Roast Engine** — Personalized insults based on promo count
📢 **Paid Promo Detection** — Scans for #ad, sponsored posts, shill patterns  
🪦 **Tombstone Generator** — Beautiful graveyard cards with death dates
💀 **Casualty Counter** — Tracks which promoted projects died
🔗 **Shareable Links** — Every roast gets a unique URL
📊 **Public Graveyard** — Browse all buried KOLs

---

## Deploy Your Own

### Option 1: Heroku (Easiest)

1. **Install Heroku CLI**
   ```bash
   npm install -g heroku
   ```

2. **Login & create app**
   ```bash
   heroku login
   heroku create your-kol-graveyard
   ```

3. **Set environment variables**
   ```bash
   heroku config:set FLASK_SECRET_KEY=your-secret-key-here
   # Optional: Add X API token for real data
   heroku config:set X_API_BEARER_TOKEN=your-x-token
   ```

4. **Deploy**
   ```bash
   git init
   git add .
   git commit -m "Initial burial"
   git push heroku main
   ```

### Option 2: Render (Free Tier)

1. **Fork/push to GitHub**
2. **Create Web Service on Render**
3. **Set build command:** `pip install -r requirements.txt`
4. **Start command:** `gunicorn app:app`
5. **Set env vars:** `FLASK_SECRET_KEY`, `X_API_BAKER_TOKEN`
6. **Deploy**

### Option 3: Local / VPS

```bash
# Clone repo
cd 2026-03-03-kol-roaster

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy and configure environment
cp .env.example .env
# Edit .env with your values

# Run the app
python app.py
```

Visit `http://localhost:5000`

---

## Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `FLASK_SECRET_KEY` | Yes | Secret key for sessions (generate random) |
| `X_API_BEARER_TOKEN` | No | X/Twitter API token for real data scraping |
| `FLASK_ENV` | No | Set to `production` for deployment |
| `PORT` | No | Port to run on (default: 5000) |

### Getting an X API Token

1. Go to [developer.twitter.com](https://developer.twitter.com)
2. Create a project and app
3. Generate Bearer Token in Keys & Tokens
4. Set as `X_API_BEARER_TOKEN`

Without the X API token, the app uses mock data for demo purposes.

---

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Homepage / search |
| `/roast` | POST | Create new roast |
| `/r/<handle>` | GET | View specific roast |
| `/graveyard` | GET | View all burials |
| `/api/roast/<handle>` | GET | Get roast as JSON |
| `/api/stats` | GET | Get cemetery statistics |

---

## Customization

### Roast Templates

Edit `ROAST_TEMPLATES` in `app.py` to add your own insults:

```python
ROAST_TEMPLATES = {
    'shill_level': {
        'low': [
            "Your personalized roast here...",
        ],
    },
}
```

### Add New Patterns

Add shill detection patterns to `SHILL_PATTERNS`:

```python
SHILL_PATTERNS = [
    r'your-pattern-here',
]
```

### Styling

Edit `static/style.css` to change colors, fonts, animations.

---

## Disclaimer

🪦 The KOL Graveyard is **satire and entertainment**. The data shown is either:
- Mock/simulated data for demonstration
- Publicly available X data analyzed for patterns

Do not use for actual investment decisions. Don't be a shill. 🪦

---

## Credits

- **Concept:** Russ (The Gaming Strategist)
- **Built by:** Archon (ghost in the machine)
- **Built for:** Web3 BD intelligence + laughs
- **Built while:** Russ was sleeping

---

## License

MIT — Do whatever, just don't blame us when someone roasts you back.
