from pathlib import Path

from agent.core.policy import PolicyEngine


def test_known_enabled_read_capability_is_allowed(tmp_path: Path):
    policy = tmp_path / "policy.yml"
    policy.write_text(
        "capabilities:\n  inventory:\n    enabled: true\n    risk: read\n",
        encoding="utf-8",
    )
    decision = PolicyEngine(policy).evaluate("inventory")
    assert decision.allowed is True
    assert decision.requires_approval is False


def test_unknown_capability_is_denied():
    decision = PolicyEngine().evaluate("does_not_exist")
    assert decision.allowed is False


def test_disabled_capability_is_denied():
    decision = PolicyEngine().evaluate("powershell")
    assert decision.allowed is False
