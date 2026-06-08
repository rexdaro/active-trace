import pytest
import subprocess
import os

def test_alembic_setup():
    # Run alembic current to see if it works without error
    # We use subprocess to call alembic in the project root
    # Note: Using '.' as cwd because we are running from project root
    env = os.environ.copy()
    env["DATABASE_URL"] = "sqlite+aiosqlite:///./test.db"
    result = subprocess.run(["alembic", "current"], capture_output=True, text=True, env=env)
    assert result.returncode == 0
