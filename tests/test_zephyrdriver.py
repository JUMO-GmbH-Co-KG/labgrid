import pytest

from labgrid.driver import ZephyrDriver, ExecutionError, ShellDriver
from labgrid.exceptions import NoDriverFoundError


class TestZephyrDriver:
    def test_instance(self, target, serial_driver):
        s = ZephyrDriver(target, "shell", prompt='dummy')
        assert (isinstance(s, ShellDriver))

    def test_no_driver(self, target):
        with pytest.raises(NoDriverFoundError):
            ZephyrDriver(target, "shell", prompt='dummy')

    def test_run(self, target_with_fakeconsole, mocker):
        t = target_with_fakeconsole
        d = ZephyrDriver(t, "shell", prompt='dummy')
        d.on_activate = mocker.MagicMock()
        d = t.get_driver('ZephyrDriver')
        d._run = mocker.MagicMock(return_value=(['success'], [], 0))
        res = d.run_check("test")
        assert res == ['success']
        res = d.run("test")
        assert res == (['success'], [], 0)

    def test_run_error(self, target_with_fakeconsole, mocker):
        t = target_with_fakeconsole
        d = ZephyrDriver(t, "shell", prompt='dummy')
        d.on_activate = mocker.MagicMock()
        d = t.get_driver('ZephyrDriver')
        d._run = mocker.MagicMock(return_value=(['error'], [], 1))
        with pytest.raises(ExecutionError):
            res = d.run_check("test")
        res = d.run("test")
        assert res == (['error'], [], 1)

    def test_run_with_timeout(self, target_with_fakeconsole, mocker):
        t = target_with_fakeconsole
        d = ZephyrDriver(t, "shell", prompt='dummy')
        d.on_activate = mocker.MagicMock()
        d = t.get_driver('ZephyrDriver')
        d._run = mocker.MagicMock(return_value=(['success'], [], 0))
        res = d.run_check("test", timeout=30.0)
        assert res == ['success']
        res = d.run("test")
        assert res == (['success'], [], 0)
