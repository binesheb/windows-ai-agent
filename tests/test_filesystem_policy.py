from pathlib import Path

from agent.core.paths import evaluate_path, is_sensitive


def test_workspace_path_is_allowed(tmp_path: Path):
    decision = evaluate_path(str(tmp_path / "project"), [str(tmp_path)])
    assert decision.allowed is True


def test_outside_workspace_is_denied(tmp_path: Path):
    workspace = tmp_path / "workspace"
    outside = tmp_path / "outside"
    workspace.mkdir()
    outside.mkdir()

    decision = evaluate_path(str(outside), [str(workspace)])
    assert decision.allowed is False
    assert "outside configured" in decision.reason


def test_windows_sensitive_locations_are_protected():
    assert is_sensitive(Path(r"C:\Windows\System32")) is True
    assert is_sensitive(Path(r"C:\Program Files\Example")) is True


def test_ssh_directory_is_protected(monkeypatch, tmp_path: Path):
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
    assert is_sensitive((tmp_path / ".ssh" / "id_ed25519").resolve()) is True
