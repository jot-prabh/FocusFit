# FocusFit – Smart Personalized Focus & Wellness System

FocusFit is a Flask + SQLite web app for screen-time awareness, study planning, mood-based recommendations, wellness breaks, and optional study focus sessions.

## Main changes in this version

- Cleaner dashboard with fewer cards and more spacing
- Daily check-in merged inside recommendation section
- Human, contextual recommendation logic
- Personalized limits based on user type, screen purpose, age context, and fitness level
- Fitness break now requires completing the timer before marking done
- Timer completion sound added
- Study Focus Timer is shown only for study/work suitable profiles
- Weekly report simplified
- Dark/light theme retained

## Files to replace

- `app.py`
- `database.py`
- `templates/dashboard.html`
- `static/css/style.css`
- Optional: `README.md`

## Run locally

```bash
pip install -r requirements.txt
python app.py
```

Open: `http://127.0.0.1:5000`
