# AgriHealth — Beginner Starter ZIP

This is a clean Flask starter project created for a beginner-friendly AgriHealth prototype.

## What is included

- Farmer dashboard
- AI Crop Doctor form
- Crop/stage/moisture-based rule engine
- Image upload and case storage
- SQLite database
- Risk levels
- IPM-style monitoring and precautions
- Recheck workflow
- Extension assignment workflow
- Case management
- Analytics charts
- District hotspot aggregation
- Digital Field Vault
- Responsive UI

## Important

This version DOES NOT contain a trained AI image model. The uploaded crop image is stored with the case, while the diagnosis currently uses simple rules. This is intentional so the project can run without paid AI services or machine-learning setup.

## Run it on Windows

1. Install Python 3.11+ from python.org.
2. Open this project folder in VS Code.
3. Open Terminal in VS Code.
4. Run:

    python -m venv venv

5. Activate it:

    venv\Scripts\activate

6. Install Flask:

    pip install flask

7. Start the app:

    python app.py

8. Open:

    http://127.0.0.1:5000

## Next upgrades

1. Real weather/rainfall API
2. Real AI crop-image diagnosis model/API
3. GPS + interactive hotspot map
4. More crops and diseases
5. Expert validation
6. Real-world datasets and time-series charts
7. Farmer login and field profiles
8. WhatsApp/voice integration
9. Deployment

The project is inspired by publicly described Plantix workflows such as photo-based crop diagnosis, treatment guidance, disease libraries and field intelligence, but this starter has its own structure and UI.
