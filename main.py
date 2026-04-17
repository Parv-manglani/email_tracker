from fastapi import FastAPI, Response, Request
from pydantic import BaseModel
from database import get_connection, init_db, insert_email, mark_as_opened
from utils import generate_uuid

app = FastAPI()


class CreateEmailRequest(BaseModel):
    email: str


@app.on_event("startup")
def startup_event():
    init_db()


@app.get("/")
def home():
    return {"message": "Email tracking running.. 🚀"}


# 🔹 Create email record
@app.post("/create-email")
def create_email(payload: CreateEmailRequest):
    uid = generate_uuid()
    insert_email(uid, payload.email)

    return {
        "uid": uid,
        "message": "Email Record created"
    }


# 🔥 TRACKING ENDPOINT (IMPORTANT)
@app.get("/track")
def track(uid: str, request: Request):

    # 🔹 IP + User-Agent nikaal pehle
    ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent")

    # 🔹 DB me pass kar
    mark_as_opened(uid, ip, user_agent)

    print(f"UID: {uid}")
    print(f"IP: {ip}")
    print(f"User-Agent: {user_agent}")

    # 🔹 1x1 pixel return
    pixel = (
        b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01'
        b'\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89'
        b'\x00\x00\x00\nIDATx\x9cc`\x00\x00\x00\x02\x00\x01'
        b'\xe2!\xbc33\x00\x00\x00\x00IEND\xaeB`\x82'
    )

    return Response(content=pixel, media_type="image/png")


# 🔹 Get all data
@app.get("/get-data")
def get_data():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM email_tracking")
    rows = cursor.fetchall()

    conn.close()

    # 🔥 Clean JSON response
    data = []
    for row in rows:
        data.append({
            "uid": row[0],
            "email": row[1],
            "status": row[2],
            "sent_at": row[3],
            "opened_at": row[4],
            "open_count": row[5],
            "ip": row[6],
            "user_agent": row[7],
            "is_proxy": row[8]
        })

    return {"data": data}