"""Banking rules and storage for Coding Bank of India.

This module has no Streamlit code in it, so the same logic can later sit
behind a REST API (FastAPI/Flask) or be unit-tested on its own.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
import tempfile
import threading
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

ACTIVE, PENDING, FROZEN = "active", "pending", "frozen"
MIN_PASSWORD_LENGTH = 6
_ITERATIONS = 120_000


class BankError(Exception):
    """A rule was broken. The message is written for the person using the app."""


# ---------------------------------------------------------------- passwords
def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), _ITERATIONS)
    return f"pbkdf2${salt}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    if not stored.startswith("pbkdf2$"):
        return False
    _, salt, expected = stored.split("$")
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), _ITERATIONS)
    return hmac.compare_digest(digest.hex(), expected)


def _public(customer: dict) -> dict:
    """A copy of the customer record without the password hash."""
    return {k: v for k, v in customer.items() if k != "Password"}


# --------------------------------------------------------------------- bank
class Bank:
    def __init__(self, path: str | os.PathLike | None = None):
        self.path = Path(path or os.getenv("BANK_DATA_PATH", "data/bank_data.json"))
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()

    # -- storage ----------------------------------------------------------
    def _load(self) -> tuple[dict, bool]:
        data = {"customers": [], "admin": [], "transaction": []}
        if self.path.exists():
            text = self.path.read_text(encoding="utf-8").strip()
            if text:
                data.update(json.loads(text))

        # Upgrade records written by the original command-line version.
        changed = False
        for c in data["customers"]:
            status = str(c.get("Status", PENDING)).lower()
            if status == "approve":  # the old approve_account() wrote this by mistake
                status = ACTIVE
            if status != c.get("Status"):
                c["Status"] = status
                changed = True
            if not str(c.get("Password", "")).startswith("pbkdf2$"):
                c["Password"] = hash_password(str(c.get("Password", "")))
                changed = True
            c["Account No."] = str(c["Account No."])
        return data, changed

    def _save(self, data: dict) -> None:
        # Write to a temp file first so a crash can never leave a half-written file.
        fd, tmp = tempfile.mkstemp(dir=self.path.parent, suffix=".tmp")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
        os.replace(tmp, self.path)

    @contextmanager
    def _txn(self, write: bool = True):
        """Load fresh data, let the caller change it, save if nothing raised."""
        with self._lock:
            data, migrated = self._load()
            yield data
            if write or migrated:
                self._save(data)

    # -- helpers ----------------------------------------------------------
    @staticmethod
    def _find(data: dict, customer_id: int) -> dict:
        for c in data["customers"]:
            if c["Customer ID"] == customer_id:
                return c
        raise BankError("Customer not found.")

    @staticmethod
    def _amount(value) -> int:
        try:
            amount = int(value)
        except (TypeError, ValueError):
            raise BankError("Enter a valid amount.")
        if amount <= 0:
            raise BankError("Amount must be more than ₹0.")
        return amount

    @staticmethod
    def _require_active(c: dict) -> None:
        if c["Status"] == PENDING:
            raise BankError("Your account is waiting for admin approval.")
        if c["Status"] != ACTIVE:
            raise BankError("This account is frozen. Contact the bank to reactivate it.")

    @staticmethod
    def _log(data: dict, kind: str, amount: int, **fields) -> None:
        data["transaction"].append({
            "Transaction ID": len(data["transaction"]) + 1,
            "Type": kind,
            **fields,
            "Amount": amount,
            "Date": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        })

    # -- customer ---------------------------------------------------------
    def register(self, customer_id: int, name: str, account_no: str, balance: int, password: str) -> None:
        name, account_no = name.strip(), account_no.strip()
        if not name:
            raise BankError("Enter your name.")
        if not account_no:
            raise BankError("Enter an account number.")
        if int(balance) <= 0:
            raise BankError("Opening balance must be more than ₹0.")
        if len(password) < MIN_PASSWORD_LENGTH:
            raise BankError(f"Password must be at least {MIN_PASSWORD_LENGTH} characters.")
        with self._txn() as data:
            for c in data["customers"]:
                if c["Customer ID"] == customer_id:
                    raise BankError("That Customer ID is already taken.")
                if c["Account No."] == account_no:
                    raise BankError("That account number is already registered.")
            data["customers"].append({
                "Customer ID": customer_id,
                "Name": name,
                "Account No.": account_no,
                "Balance": int(balance),
                "Status": PENDING,
                "Password": hash_password(password),
            })

    def authenticate(self, customer_id: int, password: str) -> dict:
        with self._txn(write=False) as data:
            for c in data["customers"]:
                if c["Customer ID"] == customer_id and verify_password(password, c["Password"]):
                    return _public(c)
        raise BankError("Customer ID or password is incorrect.")

    def get_customer(self, customer_id: int) -> dict:
        with self._txn(write=False) as data:
            return _public(self._find(data, customer_id))

    def deposit(self, customer_id: int, amount: int) -> int:
        amount = self._amount(amount)
        with self._txn() as data:
            c = self._find(data, customer_id)
            self._require_active(c)
            c["Balance"] += amount
            self._log(data, "Deposit", amount, **{"Customer ID": customer_id, "Balance After": c["Balance"]})
            return c["Balance"]

    def withdraw(self, customer_id: int, amount: int) -> int:
        amount = self._amount(amount)
        with self._txn() as data:
            c = self._find(data, customer_id)
            self._require_active(c)
            if amount > c["Balance"]:
                raise BankError("Insufficient balance.")
            c["Balance"] -= amount
            self._log(data, "Withdrawal", amount, **{"Customer ID": customer_id, "Balance After": c["Balance"]})
            return c["Balance"]

    def transfer(self, sender_id: int, receiver_id: int, amount: int) -> int:
        amount = self._amount(amount)
        if sender_id == receiver_id:
            raise BankError("Sender and receiver cannot be the same.")
        with self._txn() as data:
            sender = self._find(data, sender_id)
            try:
                receiver = self._find(data, receiver_id)
            except BankError:
                raise BankError("Receiver not found.")
            self._require_active(sender)
            if receiver["Status"] != ACTIVE:
                raise BankError("The receiver's account cannot accept money right now.")
            if amount > sender["Balance"]:
                raise BankError("Insufficient balance.")
            sender["Balance"] -= amount
            receiver["Balance"] += amount
            self._log(data, "Transfer", amount, **{"Sender ID": sender_id, "Receiver ID": receiver_id})
            return sender["Balance"]

    def history(self, customer_id: int) -> list[dict]:
        with self._txn(write=False) as data:
            mine = [t for t in data["transaction"]
                    if customer_id in (t.get("Customer ID"), t.get("Sender ID"), t.get("Receiver ID"))]
        return mine[::-1]

    def change_password(self, customer_id: int, old: str, new: str) -> None:
        if len(new) < MIN_PASSWORD_LENGTH:
            raise BankError(f"New password must be at least {MIN_PASSWORD_LENGTH} characters.")
        with self._txn() as data:
            c = self._find(data, customer_id)
            if not verify_password(old, c["Password"]):
                raise BankError("Current password is incorrect.")
            c["Password"] = hash_password(new)

    # -- admin ------------------------------------------------------------
    @staticmethod
    def admin_uses_default_password() -> bool:
        return "ADMIN_PASSWORD" not in os.environ

    @staticmethod
    def verify_admin(password: str) -> bool:
        expected = os.getenv("ADMIN_PASSWORD", "admin123")
        return hmac.compare_digest(password.encode(), expected.encode())

    def stats(self) -> dict:
        with self._txn(write=False) as data:
            cs = data["customers"]
            return {
                "customers": len(cs),
                "active": sum(c["Status"] == ACTIVE for c in cs),
                "pending": sum(c["Status"] == PENDING for c in cs),
                "frozen": sum(c["Status"] == FROZEN for c in cs),
                "deposits": sum(c["Balance"] for c in cs),
                "transactions": len(data["transaction"]),
            }

    def all_customers(self, query: str = "") -> list[dict]:
        q = query.strip().lower()
        with self._txn(write=False) as data:
            rows = [_public(c) for c in data["customers"]]
        if q:
            rows = [c for c in rows
                    if q in str(c["Customer ID"]) or q in c["Name"].lower() or q in c["Account No."].lower()]
        return rows

    def all_transactions(self) -> list[dict]:
        with self._txn(write=False) as data:
            return data["transaction"][::-1]

    def approve(self, account_no: str) -> None:
        with self._txn() as data:
            for c in data["customers"]:
                if c["Account No."] == str(account_no):
                    if c["Status"] != PENDING:
                        raise BankError("Account is not pending.")
                    c["Status"] = ACTIVE
                    return
        raise BankError("Account not found.")

    def set_status(self, account_no: str, status: str) -> None:
        if status not in (ACTIVE, FROZEN):
            raise BankError("Status must be active or frozen.")
        with self._txn() as data:
            for c in data["customers"]:
                if c["Account No."] == str(account_no):
                    c["Status"] = status
                    return
        raise BankError("Account not found.")
