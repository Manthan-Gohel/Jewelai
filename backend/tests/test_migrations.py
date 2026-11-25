import os
from pathlib import Path
import subprocess
import sys

from sqlalchemy import create_engine, inspect


def test_fresh_database_migrates_from_any_working_directory(tmp_path):
    database_url = f"sqlite:///{(tmp_path / 'migration-test.db').as_posix()}"
    backend = Path(__file__).resolve().parents[1]
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "-c", str(backend / "alembic.ini"), "upgrade", "head"],
        cwd=tmp_path,
        env={**os.environ, "DATABASE_URL": database_url},
        capture_output=True, text=True, timeout=60,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    engine = create_engine(database_url)
    try:
        schema = inspect(engine)
        assert {"users", "instagram_accounts", "products", "post_product_links", "processed_comments"} <= set(schema.get_table_names())
        assert "token_expires_at" in {column["name"] for column in schema.get_columns("instagram_accounts")}
        defaults = {column["name"]: str(column["default"]).strip("'()") for column in schema.get_columns("business_settings")}
        assert defaults["business_name"] == defaults["tagline"] == defaults["store_timings"] == ""
        assert defaults["auto_reply_enabled"].lower() in {"0", "false"}
        assert defaults["gold_rate_22k_per_10g"] in {"0", "0.0"}
    finally:
        engine.dispose()
