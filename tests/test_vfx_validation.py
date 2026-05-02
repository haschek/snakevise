import subprocess


def test_invalid_vfx_returns_error():
    """Test that an invalid VFX name returns an error."""
    result = subprocess.run(
        ["python3", "snakevise.py", "--vfx", "nonexistent_effect"],
        capture_output=True,
        text=True,
    )
    assert "Requested effect 'nonexistent_effect' does not exist" in result.stdout
    assert "Valid effects are:" in result.stdout


def test_valid_vfx_names_pass_validation():
    """Test that valid VFX names (including 'all' and 'none') pass the initial validation."""
    # We expect this to fail later due to missing inputs, but NOT due to effect validation
    for effect in ["zoomin", "blur", "sharpen", "colorboost", "invert", "all", "none"]:
        result = subprocess.run(
            ["python3", "snakevise.py", "--vfx", effect], capture_output=True, text=True
        )
        assert f"Requested effect '{effect}' does not exist" not in result.stdout
        assert "No input sources defined." in result.stdout
