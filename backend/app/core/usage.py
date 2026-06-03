"""토큰 사용량 누적·조회 및 일일 쿼터 검사.

공개 데모의 비용 폭주를 막기 위해 두 가지 한도를 적용한다.

- **계정별 일일 한도**: 패스코드로 로그인한 계정 하나가 하루에 쓸 수 있는 LLM
  토큰 상한.
- **사이트 전체 일일 한도**: 모든 계정 합산 상한(전체 비용 캡).

날짜는 UTC ``YYYY-MM-DD`` 문자열로 다루며, 매일 새 행이 쌓여 자정마다 리셋된다.
``settings.auth_enabled`` 가 False(접근 코드 미설정)면 한도를 적용하지 않는다.
"""

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.db.models import TokenUsage

SITE_SCOPE = "__site__"


def today_utc() -> str:
    """UTC 기준 오늘 날짜(YYYY-MM-DD)."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def get_used(db: Session, scope: str, date: str | None = None) -> int:
    """해당 범위·날짜의 누적 토큰 사용량을 반환한다(없으면 0)."""
    date = date or today_utc()
    row = db.execute(
        select(TokenUsage).where(TokenUsage.scope == scope, TokenUsage.usage_date == date)
    ).scalar_one_or_none()
    return row.total_tokens if row else 0


def remaining(db: Session, account: str) -> dict[str, int]:
    """계정·사이트 각각의 잔여 토큰 수를 반환한다."""
    used_acct = get_used(db, account)
    used_site = get_used(db, SITE_SCOPE)
    return {
        "account_limit": settings.daily_token_limit_per_account,
        "account_used": used_acct,
        "account_remaining": max(0, settings.daily_token_limit_per_account - used_acct),
        "site_limit": settings.site_daily_token_limit,
        "site_used": used_site,
        "site_remaining": max(0, settings.site_daily_token_limit - used_site),
    }


def check_quota(db: Session, account: str) -> tuple[bool, str | None]:
    """호출 전 쿼터 검사. (통과여부, 사유) 를 반환한다.

    인증이 비활성(로컬 개발)이면 항상 통과한다.
    """
    if not settings.auth_enabled:
        return True, None
    info = remaining(db, account)
    if info["site_remaining"] <= 0:
        return False, "오늘 데모 전체 사용 한도에 도달했습니다. 내일 다시 시도해 주세요."
    if info["account_remaining"] <= 0:
        return False, "오늘 사용 가능한 토큰을 모두 사용했습니다. 내일 다시 시도해 주세요."
    return True, None


def record_usage(db: Session, account: str, tokens: int) -> None:
    """계정과 사이트 양쪽에 토큰 사용량을 누적한다(UPSERT).

    인증이 비활성이면 기록하지 않는다.
    """
    if not settings.auth_enabled or tokens <= 0:
        return
    date = today_utc()
    for scope in (account, SITE_SCOPE):
        row = db.execute(
            select(TokenUsage).where(TokenUsage.scope == scope, TokenUsage.usage_date == date)
        ).scalar_one_or_none()
        if row is None:
            db.add(TokenUsage(scope=scope, usage_date=date, total_tokens=tokens))
        else:
            row.total_tokens += tokens
    db.commit()
