# pylint: disable=no-member
import logging

import attr
from pexpect import TIMEOUT

from ..factory import target_factory
from ..protocol import CommandProtocol, ConsoleProtocol, LinuxBootProtocol
from ..step import step
from ..util import Timeout
from .common import Driver
from .commandmixin import CommandMixin


@target_factory.reg_driver
@attr.s(eq=False)
class ZephyrDriver(CommandMixin, Driver, CommandProtocol, LinuxBootProtocol):
    """
    ZephyrDriver - Driver to control zephyr via the console.
       ZephyrDriver binds on top of a ConsoleProtocol.

       On activation, the ZephyrDriver will look for the zephyr prompt on the
       console and provide access to the zephyr shell.

    Args:
        prompt (str): zephyr prompt to match
        login_timeout (int): optional, timeout for access to the shell
    """
    bindings = {"console": ConsoleProtocol, }
    prompt = attr.ib(default="", validator=attr.validators.instance_of(str))
    login_timeout = attr.ib(default=60, validator=attr.validators.instance_of(int))

    def __attrs_post_init__(self):
        super().__attrs_post_init__()
        self.logger = logging.getLogger(f"{self}:{self.target}")
        self._status = 0

    def on_activate(self):
        """Await prompt and disable logging to prevent inteference with the tests"""
        if self._status == 0:
            self._await_prompt()
        self._run("log disable")

    def on_deactivate(self):
        """Deactivate the ZephyrDriver by simply setting internal status to 0"""
        self._status = 0

    @Driver.check_active
    @step(args=['cmd'])
    def run(self, cmd: str, *, timeout: int = 30):  # pylint: disable=unused-argument
        return self._run(cmd, timeout=timeout)

    def _run(self, cmd: str, *, timeout: int = 30, codec: str = "utf-8", decodeerrors: str = "strict"):  # pylint: disable=unused-argument,line-too-long
        """
        Runs the specified cmd on the shell and returns the output.

        Arguments:
        cmd - cmd to run on the shell
        """
        if self._status == 1:
            self.console.sendline(cmd)
            timeout
            _, _, match, _ = self.console.expect(rf'.*{self.prompt}', timeout=timeout)
            # exclude issued command and split by newline
            data = match.group(0).decode('utf-8').split('\r\n')[1:-1]
            self.logger.debug("Received Data: %s", data)
            return (data)

        return None

    @Driver.check_active
    @step()
    def reset(self):
        """Reset the board via kernel command"""
        self._status = 0
        self.console.sendline("kernel reboot cold")

    def get_status(self):
        """
        Retrieve status of the ZephyrDriver
        0 means inactive, 1 means active.

        Returns:
            int: status of the driver
        """
        return self._status

    def _check_prompt(self):
        """
        Internal function to check if we have a valid prompt.
        It sets the internal _status to 1 or 0 based on the prompt detection.
        """
        self.console.sendline(f"invalidCommand42")
        try:
            self.console.expect(f"invalidCommand42: command not found", timeout=2)
            self.console.expect(self.prompt, timeout=1)
            self._status = 1
        except TIMEOUT:
            self._status = 0
            raise

    @step()
    def _await_prompt(self):
        """Awaits the prompt and enters the shell"""

        timeout = Timeout(float(self.login_timeout))

        # We call console.expect with a short timeout here to detect if the
        # console is idle, which would result in a timeout without any changes
        # to the before property. So we store the last before value we've seen.
        # Because pexpect keeps any read data in it's buffer when a timeout
        # occours, we can't lose any data this way.
        last_before = None

        expectations = [self.prompt, TIMEOUT]
        while True:
            index, before, _, _ = self.console.expect(
                expectations,
                timeout=2
            )

            if index == 0:
                # we got a prompt. no need for any further action to activate
                # this driver.
                self._status = 1
                break

            elif index == 1:
                # expect hit a timeout while waiting for a match
                if before == last_before:
                    # we did not receive anything during the previous expect cycle
                    # let's assume the target is idle and we can safely issue a
                    # newline to check the state
                    self.console.sendline("")

                if timeout.expired:
                    raise TIMEOUT(
                        f"Timeout of {self.login_timeout} seconds exceeded during waiting for login"  # pylint: disable=line-too-long
                    )

            last_before = before
        self._check_prompt()

    @Driver.check_active
    def await_boot(self):
        raise NotImplementedError

    @Driver.check_active
    def boot(self, name: str):
        raise NotImplementedError

