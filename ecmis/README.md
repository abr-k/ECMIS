ECMIS — Educational Market-Surveillance Prototype
ECMIS is a small Python project that demonstrates how unusual movements in fictional share prices and trading volumes can be flagged for human review.


Features
- Dashboard: View a summary of the sample market, latest prices, price changes, alert counts, and recent alerts.
- Market Analysis: Explore price and volume charts for an individual fictional security.
- Alerts: Filter alerts, read why they were generated, change their status, and save review notes.
- CSV upload: Load a compatible CSV file for exploration.
- Local persistence: Save alert statuses and notes in a local SQLite database.
- Simple detection: Use three transparent rules rather than a complex machine-learning model.
How detection works
The app compares each day with the previous 20 trading days. It does not use later observations to calculate an earlier day's baseline.
1. Price move: The absolute daily price change is at least three times the recent typical daily move and at least 3%.
2. Volume spike: Daily volume is at least three times the recent average volume.
3. Price + volume: Both the price-move and volume-spike rules trigger on the same day, producing one combined alert.
Alert priority
- High: The price-move and volume-spike rules trigger together.
- Medium: A single rule exceeds its threshold by at least 1.5 times.
- Low: A single rule triggers but does not reach that 1.5-times level.
These are simple demonstration thresholds, not thresholds calibrated against real market data. The rules may flag ordinary activity, so an alert should be reviewed rather than treated as a conclusion.

Thresholds are defined near the top of src/detection.py.
Technology
- Python
- Streamlit
- pandas
- Plotly
- SQLite
- pytest
The app is intended to run locally. It does not connect to a live exchange or require a paid API.
Project structure
ECMIS/
├── app.py
├── make_sample_data.py
├── requirements.txt
├── src/
│   ├── data.py
│   ├── detection.py
│   ├── storage.py
│   └── charts.py
├── data/
│   └── sample_prices.csv
└── tests/
- app.py — Streamlit interface and the three app pages.
- src/data.py — Loads and validates CSV data.
- src/detection.py — Calculates indicators and generates alerts.
- src/storage.py — Saves alert statuses and notes in SQLite.
- src/charts.py — Creates charts.
- make_sample_data.py — Generates reproducible fictional sample data.
- tests/ — Automated tests for the main behaviours.
The database file data/ecmis.db is created locally when needed and should not be committed to GitHub.
Getting started
Requirements
Install Python first. Python 3.12 or another version supported by the packages in requirements.txt is recommended. The app has not been verified on every Python and dependency version.
Windows (PowerShell)
Open PowerShell or the VS Code terminal in the project folder, then run:
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m streamlit run app.py
Open http://localhost:8501 in your browser if it does not open automatically.

If PowerShell blocks virtual-environment activation, use the environment's Python directly:
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
macOS or Linux
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run app.py
Run the tests
With the virtual environment activated, run:
python -m pytest
Sample data
The project includes fictional data for five securities: DMBK, DMCF, DMCM, DMTL, and DMEN. The intended sample dataset contains 120 weekdays starting on 2026-01-05, for 600 rows, with three planted unusual days.

The sample generator is designed to demonstrate:
- A large price increase with unusually high volume.
- A volume spike without an unusual price movement.
- A price drop without unusually high volume.
A normal random movement may also cross a threshold and produce an alert. This is intentional: simple detection rules can generate false positives.

If you regenerate the sample data, check the generated CSV and the alert dates against make_sample_data.py, because the generated data is the source of truth.
Uploading a CSV
The app's CSV uploader expects these columns:
- date
- symbol
- close
- volume
The name column is optional. Invalid rows may be dropped with a warning. If the file contains no usable data, the app should reject it and keep the sample data.

Use fictional or otherwise authorised data. Do not upload private, confidential, or restricted market information to a public repository.
Saving alert reviews
Alert status and notes are saved locally in data/ecmis.db. The app uses an alert ID based on the security symbol and date, such as DMBK-20260511.

If a different dataset contains the same symbol and date, it may reuse the saved review for that ID. The prototype is intended for a single local user; it does not provide login, role-based access, or a tamper-proof audit log.
Testing and verification
The project author reported 25 tests covering CSV cleaning, the three detection rules, avoiding future-data leakage, reproducibility, and saving reviews.

The app was tested in a development environment using stand-ins for Streamlit and Plotly, but it was not verified in a real Streamlit browser session in that environment. Run the app locally and inspect all three pages. Test results can vary by installed package versions.

 -Current limitations and future improvements

Due to my currently developing knowledge of capital market analysis, the project uses simple logic rather than more complex and math intense models. I am actively learning more about capital markets and the quantitative methods used in market surveillance. As my knowledge grows, I intend to gradually improve the system by refining its detection rules, exploring more advanced statistical and mathematical models, and validating their effectiveness using realistic, authorized market data. These improvements will come in due time as both my understanding and the project mature.