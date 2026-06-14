import pytest
import subprocess
import os

MIGRATION_TEST_DB = "./test_migration.db"

def _cleanup():
    if os.path.exists(MIGRATION_TEST_DB):
        os.remove(MIGRATION_TEST_DB)

def test_migration_apply_revert():
    _cleanup()
    env = os.environ.copy()
    env["DATABASE_URL"] = f"sqlite+aiosqlite:///{MIGRATION_TEST_DB}"
    
    # Apply
    apply_result = subprocess.run(["alembic", "upgrade", "head"], capture_output=True, text=True, env=env)
    assert apply_result.returncode == 0, f"Upgrade failed: {apply_result.stderr}"
    
    # Revert
    revert_result = subprocess.run(["alembic", "downgrade", "base"], capture_output=True, text=True, env=env)
    assert revert_result.returncode == 0, f"Downgrade failed: {revert_result.stderr}"
    
    _cleanup()
