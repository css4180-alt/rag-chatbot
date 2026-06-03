"""로그인 및 사용량 조회 엔드포인트."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.config import settings
from app.core import usage
from app.core.auth import LOCAL_ACCOUNT, authenticate, get_account, issue_token
from app.db.database import get_db

router = APIRouter(prefix="/api/auth", tags=["auth"])


class LoginRequest(BaseModel):
    passcode: str


class QuotaInfo(BaseModel):
    account: str
    auth_enabled: bool
    account_limit: int
    account_used: int
    account_remaining: int
    site_limit: int
    site_used: int
    site_remaining: int


class LoginResponse(BaseModel):
    token: str
    quota: QuotaInfo


def _quota_info(db: Session, account: str) -> QuotaInfo:
    info = usage.remaining(db, account)
    return QuotaInfo(account=account, auth_enabled=settings.auth_enabled, **info)


@router.post("/login", response_model=LoginResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """패스코드를 검증하고 로그인 토큰 + 현재 쿼터 정보를 돌려준다."""
    if not settings.auth_enabled:
        # 인증 비활성: 어떤 값이든 로컬 계정으로 통과(로컬 개발 편의).
        return LoginResponse(token=issue_token(LOCAL_ACCOUNT), quota=_quota_info(db, LOCAL_ACCOUNT))

    account = authenticate(request.passcode)
    if account is None:
        raise HTTPException(status_code=401, detail="패스코드가 올바르지 않습니다.")
    return LoginResponse(token=issue_token(account), quota=_quota_info(db, account))


@router.get("/me", response_model=QuotaInfo)
def me(account: str = Depends(get_account), db: Session = Depends(get_db)):
    """현재 토큰의 계정·잔여 쿼터를 반환한다(프론트 새로고침 시 세션 복원용)."""
    return _quota_info(db, account)
