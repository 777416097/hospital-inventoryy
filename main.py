from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import psycopg2
from psycopg2.extras import RealDictCursor
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# السماح للمتصفح بالوصول للخادم (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# رابط الاتصال من Supabase (تأكد من وضع كلمة المرور الصحيحة)
DB_URL = "postgresql://postgres:[RhN/fbK87TnVYggggggg]@db.xxxx.supabase.co:5432/postgres"

class Asset(BaseModel):
    name: str
    barcode: str
    dept: str
    qty: int
    status: str
    image: Optional[str] = None

# دالة للاتصال بقاعدة البيانات
def get_db_conn():
    return psycopg2.connect(DB_URL, cursor_factory=RealDictCursor)

# 1. جلب العناصر النشطة (غير المحذوفة)
@app.get("/assets")
def get_assets():
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM hospital_assets WHERE is_deleted = false ORDER BY created_at DESC")
    data = cur.fetchall()
    cur.close()
    conn.close()
    return data

# 2. إضافة صنف جديد
@app.post("/add")
def add_asset(asset: Asset):
    conn = get_db_conn()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO hospital_assets (name, barcode, dept, qty, status, image_url) VALUES (%s, %s, %s, %s, %s, %s)",
            (asset.name, asset.barcode, asset.dept, asset.qty, asset.status, asset.image)
        )
        conn.commit()
        return {"message": "Success"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail="الباركود موجود مسبقاً أو خطأ في البيانات")
    finally:
        cur.close()
        conn.close()

# 3. الحذف الناعم (النقل لسلة المهملات)
@app.put("/delete/{item_id}")
def soft_delete(item_id: int):
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("UPDATE hospital_assets SET is_deleted = true WHERE id = %s", (item_id,))
    conn.commit()
    cur.close()
    conn.close()
    return {"message": "Moved to trash"}

# 4. جلب محتويات سلة المهملات
@app.get("/trash")
def get_trash():
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM hospital_assets WHERE is_deleted = true ORDER BY created_at DESC")
    data = cur.fetchall()
    cur.close()
    conn.close()
    return data

# 5. استرجاع عنصر من سلة المهملات
@app.put("/restore/{item_id}")
def restore_item(item_id: int):
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("UPDATE hospital_assets SET is_deleted = false WHERE id = %s", (item_id,))
    conn.commit()
    cur.close()
    conn.close()

    return {"message": "Restored"}
