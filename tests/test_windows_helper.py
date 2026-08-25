import platform


def test_platform_module_reports_current_system():
    assert isinstance(platform.system(), str)
    assert platform.system()
