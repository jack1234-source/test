from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from pydantic import BaseModel

from database import (
    authenticate_user,
    create_session,
    create_user,
    delete_session,
    get_all_users_with_submissions,
    get_contact_submissions,
    get_session_user,
    init_db,
    save_contact_submission,
)

app = FastAPI(title="Basic FastAPI App")
BASE_DIR = Path(__file__).resolve().parent


class ContactSubmission(BaseModel):
    name: str
    email: str
    projectType: str
    message: str


class UserRegisterPayload(BaseModel):
    username: str
    email: str
    password: str
    role: str = "user"


class UserLoginPayload(BaseModel):
    username: str
    password: str


def serve_html(page_name: str):
    return FileResponse(BASE_DIR / f"{page_name}.html")


def get_current_user(request: Request):
    token = request.cookies.get("session_token")
    if not token:
        raise HTTPException(status_code=401, detail="Authentication required")

    user = get_session_user(token)
    if not user:
        raise HTTPException(status_code=401, detail="Session expired or invalid")
    return user


@app.on_event("startup")
def startup_event():
    init_db()


@app.get("/")
async def read_root(request: Request):
    token = request.cookies.get("session_token")
    if token and get_session_user(token):
        return RedirectResponse(url="/dashboard")
    return serve_html("login")


@app.get("/about")
async def read_about():
    return serve_html("about")


@app.get("/services")
async def read_services():
    return serve_html("services")


@app.get("/work")
async def read_work():
    return serve_html("work")


@app.get("/contact")
async def read_contact():
    return serve_html("contact")


@app.get("/login")
async def login_page(request: Request):
    token = request.cookies.get("session_token")
    if token and get_session_user(token):
        return RedirectResponse(url="/dashboard")
    return serve_html("login")


@app.get("/register")
async def register_page(request: Request):
    token = request.cookies.get("session_token")
    if token and get_session_user(token):
        return RedirectResponse(url="/dashboard")
    return serve_html("register")


@app.get("/dashboard")
async def dashboard_page(request: Request):
    token = request.cookies.get("session_token")
    if not token or not get_session_user(token):
        return RedirectResponse(url="/login")
    return serve_html("dashboard")


@app.get("/admin")
async def admin_page(request: Request):
    token = request.cookies.get("session_token")
    user = get_session_user(token) if token else None
    if not user:
        return RedirectResponse(url="/login")
    if user["role"] != "admin":
        return RedirectResponse(url="/dashboard")
    return serve_html("admin")


@app.get("/feature.js")
async def read_feature_js():
    return FileResponse(BASE_DIR / "feature.js")


@app.get("/health")
async def health_check():
    return {"status": "ok"}


@app.post("/api/register")
async def register_user(payload: UserRegisterPayload):
    try:
        user_id = create_user(
            username=payload.username.strip(),
            email=payload.email.strip(),
            password=payload.password,
            role=payload.role.strip().lower() if payload.role else "user",
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    session_token = create_session(user_id)
    response = JSONResponse({"status": "success", "message": "Registration successful."})
    response.set_cookie(
        key="session_token",
        value=session_token,
        httponly=True,
        samesite="lax",
        max_age=7 * 24 * 60 * 60,
    )
    return response


@app.post("/api/login")
async def login_user(payload: UserLoginPayload):
    user = authenticate_user(payload.username.strip(), payload.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    session_token = create_session(user["id"])
    response = JSONResponse({"status": "success", "message": "Login successful.", "role": user["role"]})
    response.set_cookie(
        key="session_token",
        value=session_token,
        httponly=True,
        samesite="lax",
        max_age=7 * 24 * 60 * 60,
    )
    return response


@app.post("/api/logout")
async def logout_user(request: Request):
    token = request.cookies.get("session_token")
    if token:
        delete_session(token)

    response = JSONResponse({"status": "success", "message": "Logged out successfully."})
    response.delete_cookie("session_token")
    return response


@app.get("/api/me")
async def get_me(request: Request):
    user = get_current_user(request)
    return {"id": user["id"], "username": user["username"], "email": user["email"], "role": user["role"]}


@app.post("/api/contact")
async def submit_contact(submission: ContactSubmission, request: Request):
    user = None
    try:
        user = get_current_user(request)
    except HTTPException:
        user = None

    try:
        save_contact_submission(
            name=submission.name.strip(),
            email=submission.email.strip(),
            project_type=submission.projectType.strip(),
            message=submission.message.strip(),
            user_id=user["id"] if user else None,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Database error: {exc}") from exc

    return {
        "status": "success",
        "message": f"Thanks, {submission.name}! We will reach out about your {submission.projectType.lower()} project soon.",
    }


@app.get("/api/my-submissions")
async def get_my_submissions(request: Request):
    user = get_current_user(request)
    submissions = get_contact_submissions(limit=50, user_id=user["id"], include_all=False)
    return {"role": user["role"], "submissions": submissions}


@app.get("/api/admin/submissions")
async def get_all_submissions(request: Request):
    user = get_current_user(request)
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    submissions = get_contact_submissions(limit=100, include_all=True)
    return {"role": user["role"], "submissions": submissions}


@app.get("/api/admin/users")
async def get_admin_users_data(request: Request):
    user = get_current_user(request)
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    return {"role": user["role"], "users": get_all_users_with_submissions()}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
