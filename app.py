"""Coding Bank of India - Streamlit frontend.

All banking rules live in backend/bank.py; this file only draws screens
and calls the backend.
"""
from __future__ import annotations

import html
from collections import Counter

import pandas as pd
import streamlit as st

from backend.bank import ACTIVE, FROZEN, MIN_PASSWORD_LENGTH, PENDING, Bank, BankError

st.set_page_config(page_title="Coding Bank of India", page_icon="🏦", layout="wide")


# ------------------------------------------------------------------ styling
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700&family=Fraunces:opsz,wght@9..144,600&display=swap');

html, body, .stApp, [data-testid="stMarkdownContainer"], input, button, label {
    font-family: 'Manrope', sans-serif;
}
#MainMenu, footer { visibility: hidden; }
.block-container { padding-top: 2.5rem; max-width: 1100px; }

[data-testid="stSidebar"] { background: #0B1F3A; }
[data-testid="stSidebar"] :is(p, span, label, h1, h2, h3) { color: #E6EEF7; }
[data-testid="stSidebar"] .stButton button { background: transparent; border: 1px solid #2DD4BF; }
[data-testid="stSidebar"] .stButton button :is(p, span) { color: #2DD4BF; }
.side-brand { font-family: 'Fraunces', serif; font-size: 1.35rem; color: #FFFFFF; line-height: 1.2; }
.side-user { color: #9FB3C8; font-size: .85rem; margin: .15rem 0 1rem; }

.brand-big { font-family: 'Fraunces', serif; font-size: 3.1rem; line-height: 1.05; color: #0B1F3A; margin: 1.5rem 0 1rem; }
.lede { font-size: 1.1rem; color: #4A5D73; max-width: 26rem; }

.balance-card { background: #0B1F3A; border-left: 6px solid #2DD4BF; border-radius: 10px; padding: 1.6rem 1.8rem; margin-bottom: 1.2rem; }
.bc-label { color: #9FB3C8; font-size: .9rem; }
.bc-amount { font-family: 'Fraunces', serif; color: #FFFFFF; font-size: 2.9rem; line-height: 1.15; margin: .2rem 0 .8rem; }
.bc-meta { display: flex; gap: 1rem; align-items: center; color: #C9D6E3; font-size: .95rem; }

.pill { display: inline-block; padding: .12rem .7rem; border-radius: 999px; font-size: .8rem; font-weight: 600; }
.pill-active { background: #CCFBF1; color: #0F5F57; }
.pill-pending { background: #FEF3C7; color: #92600A; }
.pill-frozen { background: #FEE2E2; color: #9B2C2C; }

h1, h2, h3 { color: #0B1F3A; }
[data-testid="stMetric"] { background: #FFFFFF; border: 1px solid #DDE5ED; border-radius: 10px; padding: .9rem 1.1rem; }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


# ------------------------------------------------------------------ helpers
@st.cache_resource
def get_bank() -> Bank:
    return Bank()


def inr(amount: int) -> str:
    """Format a number the Indian way: ₹12,50,000."""
    sign = "-" if amount < 0 else ""
    digits = str(abs(int(amount)))
    if len(digits) > 3:
        head, tail = digits[:-3], digits[-3:]
        groups = []
        while len(head) > 2:
            groups.insert(0, head[-2:])
            head = head[:-2]
        if head:
            groups.insert(0, head)
        digits = ",".join(groups + [tail])
    return f"{sign}₹{digits}"


def pill(status: str) -> str:
    return f'<span class="pill pill-{status}">{status.capitalize()}</span>'


def csv_button(df: pd.DataFrame, label: str, filename: str) -> None:
    st.download_button(label, df.to_csv(index=False).encode(), filename, "text/csv")


def sign_out() -> None:
    st.session_state.role = None
    st.session_state.cid = None
    st.rerun()


bank = get_bank()
st.session_state.setdefault("role", None)
st.session_state.setdefault("cid", None)


# ------------------------------------------------------------- sign-in page
def login_screen() -> None:
    left, right = st.columns([1.05, 1], gap="large")
    with left:
        st.markdown(
            '<div class="brand-big">Coding Bank of India</div>'
            '<p class="lede">Open an account, move money and check your balance in one place.</p>',
            unsafe_allow_html=True,
        )
    with right:
        tab_in, tab_new, tab_admin = st.tabs(["Sign in", "Open an account", "Admin"])

        with tab_in:
            with st.form("signin"):
                cid = st.number_input("Customer ID", min_value=1, step=1, value=None, format="%d")
                pwd = st.text_input("Password", type="password")
                go = st.form_submit_button("Sign in", type="primary")
            if go:
                if cid is None or not pwd:
                    st.error("Enter your Customer ID and password.")
                else:
                    try:
                        bank.authenticate(int(cid), pwd)
                        st.session_state.role, st.session_state.cid = "customer", int(cid)
                        st.rerun()
                    except BankError as e:
                        st.error(str(e))

        with tab_new:
            with st.form("signup", clear_on_submit=True):
                c1, c2 = st.columns(2)
                new_id = c1.number_input("Customer ID", min_value=1, step=1, value=None, format="%d")
                acc_no = c2.text_input("Account number")
                name = st.text_input("Full name")
                opening = st.number_input("Opening balance (₹)", min_value=1, step=500, value=None, format="%d")
                p1 = st.text_input(f"Password (at least {MIN_PASSWORD_LENGTH} characters)", type="password")
                p2 = st.text_input("Confirm password", type="password")
                go = st.form_submit_button("Create account", type="primary")
            if go:
                if new_id is None or opening is None:
                    st.error("Fill in the Customer ID and opening balance.")
                elif p1 != p2:
                    st.error("Passwords do not match.")
                else:
                    try:
                        bank.register(int(new_id), name, acc_no, int(opening), p1)
                        st.success("Account created. You can sign in once an admin approves it.")
                    except BankError as e:
                        st.error(str(e))

        with tab_admin:
            if bank.admin_uses_default_password():
                st.warning("This app is using the default admin password. Set ADMIN_PASSWORD before you deploy.")
            with st.form("admin_signin"):
                apwd = st.text_input("Admin password", type="password")
                go = st.form_submit_button("Sign in as admin", type="primary")
            if go:
                if bank.verify_admin(apwd):
                    st.session_state.role = "admin"
                    st.rerun()
                else:
                    st.error("Incorrect admin password.")


# ----------------------------------------------------------- customer pages
def history_frame(txns: list[dict], cid: int) -> pd.DataFrame:
    rows = []
    for t in txns:
        amt = t["Amount"]
        if t["Type"] == "Deposit":
            detail, signed = "Cash deposit", amt
        elif t["Type"] == "Withdrawal":
            detail, signed = "Cash withdrawal", -amt
        elif t.get("Sender ID") == cid:
            detail, signed = f"Sent to customer {t['Receiver ID']}", -amt
        else:
            detail, signed = f"Received from customer {t['Sender ID']}", amt
        rows.append({"Date": t["Date"], "Type": t["Type"], "Details": detail, "Amount (₹)": signed})
    return pd.DataFrame(rows, columns=["Date", "Type", "Details", "Amount (₹)"])


def money_form(cid: int, kind: str) -> None:
    verb = "Deposit" if kind == "deposit" else "Withdraw"
    with st.form(f"{kind}_form", clear_on_submit=True):
        amount = st.number_input("Amount (₹)", min_value=1, step=100, value=None, format="%d", placeholder="Enter amount")
        go = st.form_submit_button(f"{verb} money", type="primary")
    if go:
        if amount is None:
            st.error("Enter an amount.")
            return
        try:
            balance = getattr(bank, kind)(cid, int(amount))
            st.success(f"{verb} complete. New balance: {inr(balance)}")
        except BankError as e:
            st.error(str(e))


def customer_app() -> None:
    cid = st.session_state.cid
    try:
        me = bank.get_customer(cid)
    except BankError:
        sign_out()
        return

    with st.sidebar:
        st.markdown(
            f'<div class="side-brand">Coding Bank<br>of India</div>'
            f'<div class="side-user">{html.escape(me["Name"])}</div>',
            unsafe_allow_html=True,
        )
        page = st.radio("Menu", ["Overview", "Deposit", "Withdraw", "Transfer", "History", "Password"],
                        label_visibility="collapsed")
        st.write("")
        if st.button("Sign out"):
            sign_out()

    if me["Status"] == PENDING:
        st.info("Your account is waiting for admin approval. You can look around, but you can't move money yet.")
    elif me["Status"] == FROZEN:
        st.error("Your account is frozen. Contact the bank to reactivate it.")

    if page == "Overview":
        st.markdown(
            f'<div class="balance-card"><div class="bc-label">Balance</div>'
            f'<div class="bc-amount">{inr(me["Balance"])}</div>'
            f'<div class="bc-meta"><span>Account {html.escape(me["Account No."])}</span>'
            f'<span>Customer ID {me["Customer ID"]}</span>{pill(me["Status"])}</div></div>',
            unsafe_allow_html=True,
        )
        st.subheader("Recent activity")
        df = history_frame(bank.history(cid)[:5], cid)
        if df.empty:
            st.write("No transactions yet. Make a deposit to get started.")
        else:
            st.dataframe(df, hide_index=True)

    elif page in ("Deposit", "Withdraw"):
        st.subheader(page)
        st.caption(f"Current balance: {inr(me['Balance'])}")
        money_form(cid, page.lower())

    elif page == "Transfer":
        st.subheader("Transfer")
        st.caption(f"Current balance: {inr(me['Balance'])}")
        with st.form("transfer_form", clear_on_submit=True):
            to_id = st.number_input("Receiver's Customer ID", min_value=1, step=1, value=None, format="%d")
            amount = st.number_input("Amount (₹)", min_value=1, step=100, value=None, format="%d", placeholder="Enter amount")
            go = st.form_submit_button("Send money", type="primary")
        if go:
            if to_id is None or amount is None:
                st.error("Enter the receiver's ID and an amount.")
            else:
                try:
                    balance = bank.transfer(cid, int(to_id), int(amount))
                    st.success(f"Sent {inr(int(amount))}. New balance: {inr(balance)}")
                except BankError as e:
                    st.error(str(e))

    elif page == "History":
        st.subheader("Transaction history")
        df = history_frame(bank.history(cid), cid)
        if df.empty:
            st.write("No transactions yet.")
        else:
            st.dataframe(df, hide_index=True)
            csv_button(df, "Download as CSV", "my_transactions.csv")

    elif page == "Password":
        st.subheader("Change password")
        with st.form("pwd_form", clear_on_submit=True):
            old = st.text_input("Current password", type="password")
            new = st.text_input(f"New password (at least {MIN_PASSWORD_LENGTH} characters)", type="password")
            again = st.text_input("Confirm new password", type="password")
            go = st.form_submit_button("Update password", type="primary")
        if go:
            if new != again:
                st.error("New passwords do not match.")
            else:
                try:
                    bank.change_password(cid, old, new)
                    st.success("Password updated.")
                except BankError as e:
                    st.error(str(e))


# --------------------------------------------------------------- admin pages
def customers_frame(rows: list[dict]) -> pd.DataFrame:
    return pd.DataFrame(rows, columns=["Customer ID", "Name", "Account No.", "Balance", "Status"])


def admin_app() -> None:
    with st.sidebar:
        st.markdown('<div class="side-brand">Coding Bank<br>of India</div><div class="side-user">Admin</div>',
                    unsafe_allow_html=True)
        page = st.radio("Menu", ["Dashboard", "Approvals", "Accounts", "Transactions"], label_visibility="collapsed")
        st.write("")
        if st.button("Sign out"):
            sign_out()

    if page == "Dashboard":
        st.subheader("Dashboard")
        s = bank.stats()
        a, b, c, d = st.columns(4)
        a.metric("Customers", s["customers"])
        b.metric("Active", s["active"])
        c.metric("Pending", s["pending"])
        d.metric("Total deposits", inr(s["deposits"]))
        st.write("")
        txns = bank.all_transactions()
        if txns:
            st.markdown("**Transactions by type**")
            counts = Counter(t["Type"] for t in txns)
            st.bar_chart(pd.Series(counts, name="Count"))
        else:
            st.write("No transactions yet.")

    elif page == "Approvals":
        st.subheader("Accounts waiting for approval")
        pending = [c for c in bank.all_customers() if c["Status"] == PENDING]
        if not pending:
            st.write("No accounts are waiting for approval.")
        for c in pending:
            info, action = st.columns([4, 1])
            info.markdown(f"**{html.escape(c['Name'])}**  \nAccount {c['Account No.']} · "
                          f"ID {c['Customer ID']} · Opening balance {inr(c['Balance'])}")
            if action.button("Approve", key=f"approve_{c['Account No.']}", type="primary"):
                try:
                    bank.approve(c["Account No."])
                    st.rerun()
                except BankError as e:
                    st.error(str(e))

    elif page == "Accounts":
        st.subheader("All accounts")
        query = st.text_input("Search by name, Customer ID or account number")
        rows = bank.all_customers(query)
        if rows:
            st.dataframe(customers_frame(rows), hide_index=True)
            csv_button(customers_frame(rows), "Download as CSV", "accounts.csv")
        else:
            st.write("No accounts match your search.")

        st.markdown("**Change an account's status**")
        everyone = bank.all_customers()
        if everyone:
            choice = st.selectbox(
                "Account", everyone, label_visibility="collapsed",
                format_func=lambda c: f"{c['Name']} · {c['Account No.']} · {c['Status']}",
            )
            on, off, _ = st.columns([1, 1, 3])
            if on.button("Activate"):
                try:
                    bank.set_status(choice["Account No."], ACTIVE)
                    st.rerun()
                except BankError as e:
                    st.error(str(e))
            if off.button("Freeze"):
                try:
                    bank.set_status(choice["Account No."], FROZEN)
                    st.rerun()
                except BankError as e:
                    st.error(str(e))

    elif page == "Transactions":
        st.subheader("All transactions")
        df = pd.DataFrame(bank.all_transactions())
        if df.empty:
            st.write("No transactions yet.")
        else:
            st.dataframe(df, hide_index=True)
            csv_button(df, "Download as CSV", "transactions.csv")


# ------------------------------------------------------------------- router
role = st.session_state.role
if role == "customer":
    customer_app()
elif role == "admin":
    admin_app()
else:
    login_screen()
