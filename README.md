# Coding Bank of India

A Streamlit web app for the Bank Management System.

```
app.py            Frontend: every screen (Streamlit)
backend/bank.py   Backend: banking rules, password hashing, JSON storage
data/             bank_data.json is created here on first run
.streamlit/       Theme and secrets template
```

## Run it on your computer (Windows / VS Code)

```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
set ADMIN_PASSWORD=choose-a-password
streamlit run app.py
```

Your old `bank_data.json` works as is: copy it into `data/`. Plain-text
passwords are converted to hashes the first time the app loads it.

## Deploy on Streamlit Community Cloud

1. Push this folder to a GitHub repository.
2. Go to share.streamlit.io, choose New app, pick the repo, and set the main file to `app.py`.
3. Open Advanced settings > Secrets and add: `ADMIN_PASSWORD = "your-long-password"`.
4. Deploy. Streamlit gives you a public `*.streamlit.app` link.

**Storage warning:** Community Cloud wipes local files when the app restarts
or redeploys, so accounts saved in `bank_data.json` will not last. That is
fine for a demo. For lasting data, use a host with a persistent disk (the
included Dockerfile works on Render or Railway with a volume mounted at
`/data`) or move storage to a hosted database.

## Using the app

- Customers open an account, wait for approval, then sign in with Customer ID and password.
- Admin signs in on the Admin tab with `ADMIN_PASSWORD` (default `admin123` for local testing only), approves new accounts, and can freeze or activate any account.
