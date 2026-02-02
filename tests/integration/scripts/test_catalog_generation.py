import pytest
import os
import subprocess
from pathlib import Path

def test_generate_catalog_execution():
    """Test that the script runs and generates files."""
    output_dir = "tmp_catalog"
    if os.path.exists(output_dir):
        import shutil
        shutil.rmtree(output_dir)
        
    result = subprocess.run(
        ["python3", "scripts/generate_catalog.py", "--output", output_dir],
        capture_output=True,
        text=True
    )
    
    assert result.returncode == 0
    assert os.path.exists(output_dir)
    # Check if some expected file exists
    assert os.path.exists(os.path.join(output_dir, "workday-hcm", "get_employee.yaml"))

def test_generate_catalog_check_sync():
    """Test that --check works."""
    # First generate
    output_dir = "tmp_catalog_check"
    subprocess.run(["python3", "scripts/generate_catalog.py", "--output", output_dir])
    
    # Then check
    result = subprocess.run(
        ["python3", "scripts/generate_catalog.py", "--output", output_dir, "--check"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0
    assert "Catalog is in sync" in result.stderr
