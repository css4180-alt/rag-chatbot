"""테스트 공통 셋업.

``TestClient`` 를 컨텍스트 매니저로 쓰지 않으면 앱 lifespan 이 실행되지 않아
테이블이 생성되지 않는다. 테스트 시작 전에 스키마를 보장한다.
"""

import os

import pytest


@pytest.fixture(scope="session", autouse=True)
def _create_schema():
    os.makedirs("data/sqlite", exist_ok=True)
    # 모델 등록을 위해 import 후 create_all
    from app.db import models  # noqa: F401
    from app.db.database import Base, engine

    Base.metadata.create_all(bind=engine)
    yield
