import os
import json
from pathlib import Path

from fastapi import FastAPI, HTTPException, Header, UploadFile, File, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import bot as bot_module

import sheets
import auth

app = FastAPI(title="SOOQ.TJ API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

ADMIN_ID = int(os.getenv("ADMIN_ID", "7555325054"))
bot = bot_module.bot  # reuse bot instance that has all handlers registered

# ─── AUTH ───────────────────────────────────────────────────

def get_current_user(x_init_data: str = Header(...)):
    user = auth.validate_init_data(x_init_data)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid initData")
    user["role"] = auth.get_role(user["id"])
    return user


def require_admin(user=Depends(get_current_user)):
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin only")
    return user


def require_driver_or_admin(user=Depends(get_current_user)):
    if user["role"] not in ("admin", "driver"):
        raise HTTPException(status_code=403, detail="Driver/Admin only")
    return user


# ─── WEBHOOK ────────────────────────────────────────────────

@app.post("/webhook")
async def webhook(update: dict):
    update_obj = telebot.types.Update.de_json(json.dumps(update))
    bot.process_new_updates([update_obj])
    return {"ok": True}


# ─── ME ─────────────────────────────────────────────────────

@app.get("/api/me")
def me(user=Depends(get_current_user)):
    return user


# ─── PRODUCTS ───────────────────────────────────────────────

@app.get("/api/products")
def get_products():
    return sheets.get_products()


class ProductIn(BaseModel):
    name: str
    category: str
    photo_url: str = ""
    price: float
    qty: int


@app.post("/api/products")
def add_product(data: ProductIn, user=Depends(require_admin)):
    product_id = sheets.add_product(
        data.name, data.category, data.photo_url, data.price, data.qty
    )
    return {"id": product_id}


@app.put("/api/products/{row_index}")
def update_product(row_index: int, data: ProductIn, user=Depends(require_admin)):
    ok = sheets.update_product(
        row_index, data.name, data.category, data.photo_url, data.price, data.qty
    )
    return {"ok": ok}


# ─── PHOTO UPLOAD ────────────────────────────────────────────

@app.post("/api/upload-photo")
async def upload_photo(file: UploadFile = File(...), user=Depends(require_admin)):
    upload_dir = Path("uploads")
    upload_dir.mkdir(exist_ok=True)
    safe_name = f"{file.filename}"
    path = upload_dir / safe_name
    path.write_bytes(await file.read())
    webapp_url = os.getenv("WEBAPP_URL", "")
    return {"url": f"{webapp_url}/uploads/{safe_name}"}


# ─── ORDERS ─────────────────────────────────────────────────

class OrderIn(BaseModel):
    name: str
    phone: str
    address: str
    product_id: str
    product_name: str
    quantity: int = 1
    price: float


@app.post("/api/orders")
def create_order(data: OrderIn, user=Depends(get_current_user)):
    order_id = sheets.create_order(
        user["id"], data.name, data.phone, data.address,
        data.product_id, data.product_name, data.quantity, data.price,
    )
    try:
        bot.send_message(
            ADMIN_ID,
            f"🛒 *НОВЫЙ ЗАКАЗ #{order_id}!*\n\n"
            f"👤 {data.name}\n"
            f"📱 {data.phone}\n"
            f"📦 {data.product_name} x{data.quantity}\n"
            f"📍 {data.address}\n"
            f"💰 {data.price} сомони",
            parse_mode="Markdown",
        )
    except Exception:
        pass
    return {"id": order_id}


@app.get("/api/orders/my")
def my_orders(user=Depends(get_current_user)):
    return sheets.get_orders(user_id=user["id"])


@app.get("/api/orders")
def all_orders(user=Depends(require_admin)):
    return sheets.get_orders()


@app.get("/api/deliveries")
def deliveries(user=Depends(require_driver_or_admin)):
    orders = sheets.get_orders()
    return [o for o in orders if o.get("status") in ("Новый", "В пути")]


class StatusIn(BaseModel):
    status: str


@app.put("/api/orders/{order_id}")
def update_order(order_id: str, data: StatusIn, user=Depends(require_driver_or_admin)):
    ok = sheets.update_order_status(order_id, data.status)
    return {"ok": ok}


# ─── STATS ──────────────────────────────────────────────────

@app.get("/api/stats")
def stats(user=Depends(require_admin)):
    return sheets.get_stats()


# ─── STATIC: uploads + mini-app SPA ─────────────────────────

uploads_dir = Path("uploads")
uploads_dir.mkdir(exist_ok=True)
app.mount("/uploads", StaticFiles(directory=uploads_dir), name="uploads")

dist = Path("mini-app/dist")
if dist.exists():
    app.mount("/assets", StaticFiles(directory=dist / "assets"), name="assets")

    @app.get("/{full_path:path}")
    def serve_spa(full_path: str):
        return FileResponse(dist / "index.html")
