from agent.core.policy import PolicyEngine


def test_unknown_capability_is_denied():
    decision = PolicyEngine().evaluate("does_not_exist")
    assert decision.allowed is False
    assert decision.requires_approval is False


def test_system_inventory_is_read_only_allowed():
    decision = PolicyEngine().evaluate("system_inventory")
    assert decision.allowed is True
    assert decision.requires_approval is False
    assert decision.risk.value == "read"


def test_powershell_is_disabled_by_default():
    decision = PolicyEngine().evaluate("powershell")
    assert decision.allowed is False
    assert decision.risk.value == "dangerous"
