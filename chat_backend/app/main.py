from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes import auth, chat, admin

# Create FastAPI app
app = FastAPI(
    title="Chat API",
    description="API for chat application with feedback system and role-based access control",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],  # Frontend URLs
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=600,  # Cache preflight requests for 10 minutes
)

app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(admin.router)

@app.get("/")
async def root():
    return {
        "message": "Welcome to the Chat API",
        "docs": "/docs",
        "redoc": "/redoc"
    }

@app.get("/health")
async def health_check():
    return {"status": "ok"}

# @app.on_event("startup")
# async def startup_event():
#     await create_initial_admin()