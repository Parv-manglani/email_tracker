from fastapi import FastAPI, Response, Request
from database import init_db, insert_email, mark_as_opened
from utils import generate_uuid

app = FastAPI()

@app.on_event("startup")
def startup_event() :
    init_db()

@app.get("/") 
def home() :
    return {"message" : "Email tracking running.. "}


@app.post("/create-email")
def create_email(email: str) :
    uid = generate_uuid()
    insert_email(uid, email)
    return {
        "uid" : uid,
        "message" : f"Email Record created"
    }

@app.get("/track")
def track(uid: str, request: Request) :

    mark_as_opened(uid)

    ip = request.client.host
    user_agent = request.headers.get("user-agent")
    print(f"Email with uid {uid} opened from IP: {ip} with User-Agent: {user_agent}")

    pixel = (
        b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01'
        b'\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89'
        b'\x00\x00\x00\nIDATx\x9cc`\x00\x00\x00\x02\x00\x01'
        b'\xe2!\xbc33\x00\x00\x00\x00IEND\xaeB`\x82'
    )

    return Response(content = pixel, media_type = "image/png")
