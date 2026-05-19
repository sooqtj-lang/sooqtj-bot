import os
import json
import uuid
import requests
import csv
import io
import gspread
from datetime import datetime
from google.oauth2.service_account import Credentials

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
]

SPREADSHEET_ID = os.getenv("SPREADSHEET_ID", "1RoLKPZQY675Bv16GoMZDW7Sv_s77s0lKu-s2mVj3qA8")
PRODUCTS_SHEET = "Товары SOOQ"
ORDERS_SHEET = "Orders"


def _get_client():
    creds_json = os.getenv("GOOGLE_CREDENTIALS_JSON")
    if creds_json:
        info = json.loads(creds_json)
    else:
        with open("sooq-496809-a864eade54d5.json") as f:
            info = json.load(f)
    creds = Credentials.from_service_account_info(info, scopes=SCOPES)
    return gspread.authorize(creds)


def _get_sheet(name):
    client = _get_client()
    spreadsheet = client.open_by_key(SPREADSHEET_ID)
    try:
        return spreadsheet.worksheet(name)
    except gspread.WorksheetNotFound:
        return None


def _ensure_orders_sheet():
    client = _get_client()
    spreadsheet = client.open_by_key(SPREADSHEET_ID)
    try:
        ws = spreadsheet.worksheet(ORDERS_SHEET)
    except gspread.WorksheetNotFound:
        ws = spreadsheet.add_worksheet(title=ORDERS_SHEET, rows=1000, cols=12)
        ws.append_row([
            "id", "user_id", "name", "phone", "address",
            "product_id", "product_name", "quantity", "price",
            "timestamp", "status", "express"
        ])
    return ws


# ─── PRODUCTS ───────────────────────────────────────────────

def get_products():
    try:
        url = (
            f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}"
            f"/export?format=csv&sheet=Товары%20SOOQ"
        )
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            return []
        content = response.content.decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(content))
        products = []
        for i, row in enumerate(reader):
            if not any(row.values()):
                continue
            row["_index"] = i
            products.append(dict(row))
        return products
    except Exception as e:
        print(f"get_products error: {e}")
        return []


def add_product(name, category, photo_url, price, qty):
    ws = _get_sheet(PRODUCTS_SHEET)
    if not ws:
        return None
    product_id = str(uuid.uuid4())[:8].upper()
    ws.append_row([product_id, name, category, photo_url, str(price), str(qty)])
    return product_id


def update_product(row_index, name, category, photo_url, price, qty):
    ws = _get_sheet(PRODUCTS_SHEET)
    if not ws:
        return False
    actual_row = row_index + 2  # +1 for header, +1 for 1-based index
    ws.update(f"B{actual_row}:F{actual_row}", [[name, category, photo_url, str(price), str(qty)]])
    return True


# ─── ORDERS ─────────────────────────────────────────────────

def create_order(user_id, name, phone, address, product_id, product_name, quantity, price):
    ws = _ensure_orders_sheet()
    order_id = str(uuid.uuid4())[:8].upper()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ws.append_row([
        order_id, str(user_id), name, phone, address,
        str(product_id), product_name, str(quantity), str(price),
        timestamp, "Новый", "False"
    ])
    return order_id


def get_orders(user_id=None):
    ws = _ensure_orders_sheet()
    rows = ws.get_all_records()
    if user_id:
        rows = [r for r in rows if str(r.get("user_id")) == str(user_id)]
    return rows


def update_order_status(order_id, status):
    ws = _ensure_orders_sheet()
    rows = ws.get_all_values()
    for i, row in enumerate(rows):
        if row and row[0] == order_id:
            ws.update_cell(i + 1, 11, status)
            return True
    return False


def get_stats():
    ws = _ensure_orders_sheet()
    rows = ws.get_all_records()
    today = datetime.now().strftime("%Y-%m-%d")
    month = datetime.now().strftime("%Y-%m")

    today_orders = [r for r in rows if str(r.get("timestamp", "")).startswith(today)]
    month_orders = [r for r in rows if str(r.get("timestamp", "")).startswith(month)]

    return {
        "today_count": len(today_orders),
        "today_sum": sum(float(r.get("price", 0) or 0) for r in today_orders),
        "month_count": len(month_orders),
        "month_sum": sum(float(r.get("price", 0) or 0) for r in month_orders),
        "total_count": len(rows),
    }
