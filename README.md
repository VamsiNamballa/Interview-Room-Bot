# Interview Room Booking Bot

A public Streamlit chatbot for scheduling two interview rooms without user registration.

## Features

- Asks for interview duration first
- Room aliases: upper room, top floor and setup room → Room 1; hall → Room 2
- Books only from today through today + 4 days
- Detects time overlaps before saving
- Suggests the other room or the next available time
- Stores bookings in `data/bookings.xlsx`
- Captures candidate, implementation partner, client and role
- Displays and exports the schedule
- Cancels bookings by booking ID

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

## Test

```bash
pip install pytest
pytest -q
```

## Deployment warning

Streamlit Community Cloud does not guarantee persistent local files. The Excel design is suitable for a local or prototype deployment, but cloud restarts can erase bookings. Before real shared use, place the Excel workbook in durable shared storage or replace it with a persistent database while keeping Excel export.
"# Interview-Room-Bot" 
