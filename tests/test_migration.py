import pytest
import subprocess
import os

def test_migration_apply_revert():
    env = os.environ.copy()
    env["DATABASE_URL"] = "sqlite+aiosqlite:///./test.db"
    
    # Apply
    apply_result = subprocess.run(["alembic", "upgrade", "head"], capture_output=True, text=True, env=env)
    assert apply_result.returncode == 0, f"Upgrade failed: {apply_result.stderr}"
    
    # Revert
    revert_result = subprocess.run(["alembic", "downgrade", "base"], capture_output=True, text=True, env=env)
    assert revert_result.returncode == 0, f"Downgrade failed: {revert_result.stderr}"
