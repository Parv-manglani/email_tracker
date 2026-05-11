from fastapi import FastAPI, Response, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from database import get_connection, init_db, insert_email, mark_as_opened, insert_link, mark_link_clicked
from utils import generate_uuid
from email_verifier import verify_email

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class CreateEmailRequest(BaseModel):
    email: str
    company: str
    variant: str
    day: int


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
    insert_email(uid, payload.email, payload.company, payload.variant, payload.day)

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


# 🔹 Create link
class CreateLinkRequest(BaseModel):
    email: str
    company: str
    variant: str
    day: int
    target_url: str

@app.post("/create-link")
def create_link(payload: CreateLinkRequest):
    uid = generate_uuid()
    insert_link(uid, payload.email, payload.company, payload.variant, payload.day, payload.target_url)
    return {"uid": uid, "tracking_url": f"/r/{uid}"}


# 🔹 JS redirect page (scanners won't execute JS)
@app.get("/r/{uid}")
def track_link(uid: str):
    html = f"""<!DOCTYPE html>
<html>
<head><title>Redirecting...</title></head>
<body>
<script>
  fetch('/confirm/{uid}', {{method: 'POST'}}).finally(function() {{
    window.location.href = document.querySelector('meta[name=url]').content;
  }});
</script>
<meta name="url" content="">
<noscript><meta http-equiv="refresh" content="0;url=/confirm-redirect/{uid}"></noscript>
</body>
</html>"""

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT target_url FROM link_tracking WHERE id = %s", (uid,))
    result = cursor.fetchone()
    conn.close()

    if not result:
        return {"error": "Invalid link"}

    target_url = result[0]
    html = html.replace('content=""', f'content="{target_url}"')
    return Response(content=html, media_type="text/html")


# 🔹 Confirm click (called by JS)
@app.post("/confirm/{uid}")
def confirm_click(uid: str, request: Request):
    ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent")
    mark_link_clicked(uid, ip, user_agent)
    return {"ok": True}


# 🔹 Get link tracking data
@app.get("/get-links")
def get_links():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM link_tracking ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()

    data = []
    for row in rows:
        data.append({
            "uid": row[0],
            "email": row[1],
            "company": row[2],
            "variant": row[3],
            "day": row[4],
            "target_url": row[5],
            "created_at": row[6],
            "clicked": row[7],
            "clicked_at": row[8],
            "ip": row[9],
            "user_agent": row[10],
        })

    return {"data": data}


# 🔹 Verify email
@app.get("/verify-email")
def verify_email_endpoint(email: str):
    result = verify_email(email)
    return result


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
            "company": row[2],
            "variant": row[3],
            "day": row[4],
            "status": row[5],
            "sent_at": row[6],
            "opened_at": row[7],
            "open_count": row[8],
            "ip": row[9],
            "user_agent": row[10],
            "is_proxy": row[11]
        })

    return {"data": data}