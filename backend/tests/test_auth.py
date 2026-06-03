"""패스코드 인증 + 토큰 쿼터 동작 테스트.

Bedrock 호출은 필요 없다. 인증 게이트는 모델 호출 이전 단계에서 동작하고,
토큰/쿼터 로직은 순수 함수로 검증한다.
"""

import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.core import auth, usage
from app.db.database import SessionLocal
from app.db.models import TokenUsage
from app.main import app

client = TestClient(app)


@pytest.fixture
def auth_on(monkeypatch):
    """접근 코드를 설정해 인증/쿼터를 활성화한다(테스트 종료 시 원복)."""
    monkeypatch.setattr(settings, "access_codes", "secret123:guest,vip999:reviewer")
    monkeypatch.setattr(settings, "daily_token_limit_per_account", 1000)
    monkeypatch.setattr(settings, "site_daily_token_limit", 5000)
    return settings


# ---- 토큰 서명/검증 ----


def test_token_roundtrip():
    token = auth.issue_token("guest")
    assert auth.verify_token(token) == "guest"


def test_token_tampered_rejected():
    token = auth.issue_token("guest")
    assert auth.verify_token(token + "x") is None
    assert auth.verify_token("garbage.sig") is None


# ---- 로그인 ----


def test_login_disabled_accepts_anything(monkeypatch):
    # 접근 코드 미설정: 어떤 패스코드든 통과해 토큰을 받는다.
    # (로컬 .env 에 ACCESS_CODES 가 있어도 영향받지 않도록 명시적으로 비운다.)
    monkeypatch.setattr(settings, "access_codes", "")
    res = client.post("/api/auth/login", json={"passcode": "whatever"})
    assert res.status_code == 200
    assert res.json()["quota"]["auth_enabled"] is False


def test_login_wrong_passcode_rejected(auth_on):
    res = client.post("/api/auth/login", json={"passcode": "nope"})
    assert res.status_code == 401


def test_login_correct_passcode(auth_on):
    res = client.post("/api/auth/login", json={"passcode": "secret123"})
    assert res.status_code == 200
    data = res.json()
    assert data["quota"]["account"] == "guest"
    assert data["quota"]["account_limit"] == 1000
    # 발급된 토큰으로 /me 가 동작해야 한다.
    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {data['token']}"})
    assert me.status_code == 200
    assert me.json()["account"] == "guest"


# ---- 보호된 엔드포인트 게이트 ----


def test_chat_requires_auth_when_enabled(auth_on):
    res = client.post("/api/chat", json={"question": "hi"})
    assert res.status_code == 401


def test_upload_requires_auth_when_enabled(auth_on):
    res = client.post("/api/documents", files={"file": ("a.md", b"hello", "text/markdown")})
    assert res.status_code == 401


# ---- 쿼터 로직 ----


def test_quota_blocks_when_account_exhausted(auth_on):
    db = SessionLocal()
    try:
        date = usage.today_utc()
        db.query(TokenUsage).filter(TokenUsage.usage_date == date).delete()
        db.commit()
        usage.record_usage(db, "guest", 1000)  # 계정 한도(1000) 소진
        ok, reason = usage.check_quota(db, "guest")
        assert ok is False
        assert "토큰" in reason
    finally:
        db.query(TokenUsage).filter(TokenUsage.scope.in_(["guest", usage.SITE_SCOPE])).delete()
        db.commit()
        db.close()


def test_quota_blocks_when_site_exhausted(auth_on):
    db = SessionLocal()
    try:
        date = usage.today_utc()
        db.query(TokenUsage).filter(TokenUsage.usage_date == date).delete()
        db.commit()
        # 사이트 전체 한도(5000)를 다른 계정이 모두 소진했다고 가정
        usage.record_usage(db, "reviewer", 5000)
        ok, reason = usage.check_quota(db, "guest")  # guest 는 아직 안 썼지만
        assert ok is False
        assert "전체" in reason
    finally:
        db.query(TokenUsage).filter(
            TokenUsage.scope.in_(["guest", "reviewer", usage.SITE_SCOPE])
        ).delete()
        db.commit()
        db.close()
