from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, Response, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.email import send_account_link
from app.models import OneTimeToken, User, UserSession
from app.schemas import (
    LoginRequest,
    MessageResponse,
    PasswordResetEmailRequest,
    PasswordResetRequest,
    RegisterRequest,
    TokenRequest,
    UserResponse,
)
from app.security import as_utc, digest_secret, expires_in, hash_password, new_secret, verify_password

router = APIRouter(prefix="/api/auth", tags=["authentication"])
SESSION_COOKIE = "chess_session"
GENERIC_RESET_MESSAGE = "If an account exists for that email, a password reset link will be sent."


def require_allowed_origin(request: Request) -> None:
    origin = request.headers.get("origin")
    if origin and origin not in settings.frontend_origins:
        raise HTTPException(status_code=403, detail="Request origin is not allowed")


def set_session_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=SESSION_COOKIE,
        value=token,
        httponly=True,
        secure=settings.session_cookie_secure,
        samesite="lax",
        max_age=settings.session_ttl_hours * 3600,
        path="/",
    )


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    raw_token = request.cookies.get(SESSION_COOKIE)
    if not raw_token:
        raise HTTPException(status_code=401, detail="Not signed in")
    session = db.scalar(
        select(UserSession).where(UserSession.token_hash == digest_secret(raw_token))
    )
    if not session or as_utc(session.expires_at) <= datetime.now(timezone.utc):
        if session:
            db.delete(session)
            db.commit()
        raise HTTPException(status_code=401, detail="Session expired")
    user = db.get(User, session.user_id)
    if not user or not user.is_verified:
        raise HTTPException(status_code=401, detail="Not signed in")
    return user


@router.post("/register", status_code=status.HTTP_202_ACCEPTED, response_model=MessageResponse)
def register(
    payload: RegisterRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    _: None = Depends(require_allowed_origin),
) -> MessageResponse:
    email = str(payload.email).lower()
    existing = db.scalar(select(User).where(User.email == email))
    if existing is None:
        user = User(
            display_name=payload.display_name,
            email=email,
            password_hash=hash_password(payload.password),
        )
        db.add(user)
        try:
            db.flush()
            token = new_secret()
            db.add(
                OneTimeToken(
                    user_id=user.id,
                    token_hash=digest_secret(token),
                    purpose="email-verification",
                    expires_at=expires_in(24),
                )
            )
            db.commit()
            background_tasks.add_task(
                send_account_link, email, "Verify your Chess account", "verify-email", token
            )
        except IntegrityError:
            db.rollback()
    return MessageResponse(message="If registration can proceed, a verification link will be sent.")


@router.post("/verify-email", response_model=MessageResponse)
def verify_email(
    payload: TokenRequest,
    db: Session = Depends(get_db),
    _: None = Depends(require_allowed_origin),
) -> MessageResponse:
    record = db.scalar(
        select(OneTimeToken).where(
            OneTimeToken.token_hash == digest_secret(payload.token),
            OneTimeToken.purpose == "email-verification",
        )
    )
    if not record or as_utc(record.expires_at) <= datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Verification link is invalid or expired")
    user = db.get(User, record.user_id)
    if not user:
        raise HTTPException(status_code=400, detail="Verification link is invalid or expired")
    user.is_verified = True
    db.delete(record)
    db.commit()
    return MessageResponse(message="Email verified. You can now sign in.")


@router.post("/verify-email/resend", status_code=status.HTTP_202_ACCEPTED, response_model=MessageResponse)
def resend_verification(
    payload: PasswordResetEmailRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    _: None = Depends(require_allowed_origin),
) -> MessageResponse:
    user = db.scalar(select(User).where(User.email == str(payload.email).lower()))
    if user and not user.is_verified:
        token = new_secret()
        db.add(
            OneTimeToken(
                user_id=user.id,
                token_hash=digest_secret(token),
                purpose="email-verification",
                expires_at=expires_in(24),
            )
        )
        db.commit()
        background_tasks.add_task(
            send_account_link, user.email, "Verify your Chess account", "verify-email", token
        )
    return MessageResponse(message="If the account needs verification, a link will be sent.")


@router.post("/login", response_model=UserResponse)
def login(
    payload: LoginRequest,
    response: Response,
    db: Session = Depends(get_db),
    _: None = Depends(require_allowed_origin),
) -> UserResponse:
    user = db.scalar(select(User).where(User.email == str(payload.email).lower()))
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Email or password is incorrect")
    if not user.is_verified:
        raise HTTPException(status_code=403, detail="Please verify your email before signing in")

    token = new_secret()
    db.add(
        UserSession(
            user_id=user.id,
            token_hash=digest_secret(token),
            expires_at=expires_in(settings.session_ttl_hours),
        )
    )
    db.commit()
    set_session_cookie(response, token)
    return UserResponse(id=user.id, display_name=user.display_name, email=user.email)


@router.post("/logout", response_model=MessageResponse)
def logout(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    _: None = Depends(require_allowed_origin),
) -> MessageResponse:
    raw_token = request.cookies.get(SESSION_COOKIE)
    if raw_token:
        session = db.scalar(
            select(UserSession).where(UserSession.token_hash == digest_secret(raw_token))
        )
        if session:
            db.delete(session)
            db.commit()
    response.delete_cookie(key=SESSION_COOKIE, path="/", secure=settings.session_cookie_secure, httponly=True, samesite="lax")
    return MessageResponse(message="Signed out")


@router.get("/me", response_model=UserResponse)
def me(user: User = Depends(get_current_user)) -> UserResponse:
    return UserResponse(id=user.id, display_name=user.display_name, email=user.email)


@router.post("/password-reset/request", status_code=status.HTTP_202_ACCEPTED, response_model=MessageResponse)
def request_password_reset(
    payload: PasswordResetEmailRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    _: None = Depends(require_allowed_origin),
) -> MessageResponse:
    user = db.scalar(select(User).where(User.email == str(payload.email).lower()))
    if user and user.is_verified:
        token = new_secret()
        db.add(
            OneTimeToken(
                user_id=user.id,
                token_hash=digest_secret(token),
                purpose="password-reset",
                expires_at=expires_in(1),
            )
        )
        db.commit()
        background_tasks.add_task(
            send_account_link, user.email, "Reset your Chess password", "reset-password", token
        )
    return MessageResponse(message=GENERIC_RESET_MESSAGE)


@router.post("/password-reset/confirm", response_model=MessageResponse)
def confirm_password_reset(
    payload: PasswordResetRequest,
    db: Session = Depends(get_db),
    _: None = Depends(require_allowed_origin),
) -> MessageResponse:
    record = db.scalar(
        select(OneTimeToken).where(
            OneTimeToken.token_hash == digest_secret(payload.token),
            OneTimeToken.purpose == "password-reset",
        )
    )
    if not record or as_utc(record.expires_at) <= datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Reset link is invalid or expired")
    user = db.get(User, record.user_id)
    if not user:
        raise HTTPException(status_code=400, detail="Reset link is invalid or expired")
    user.password_hash = hash_password(payload.new_password)
    db.delete(record)
    for session in list(user.sessions):
        db.delete(session)
    db.commit()
    return MessageResponse(message="Password updated. Please sign in again.")
