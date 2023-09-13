'''
This Driver was tested on a FL SWITCH 2303-8SP1 with FW-version 3.27.01 BETA
file   phoenix_fl_switch.py
author Raffael Krakau
date   2023-08-24

Copyright 2023 JUMO GmbH & Co. KG
'''

from telnetlib import Telnet

PORT=23

def power_set(host, port, index: int, value: bool):
    """
    Set power state by socket port number (e.g. 1 - 8) and an value {'enable', 'disable'}.

    - values:
        - disable(False): Turn OFF,
        - enable(True): Turn ON
    """
    username = "admin"
    password = "private"
    action = "enable" if value else "disable"

    telnet = Telnet(host=host, port=port)

    # login user with password
    telnet.read_until(match=b'User: ')
    telnet.write(bytes(f'{username}\r\n', "utf-8"))
    telnet.read_until(match=b'Password: ')
    telnet.write(bytes(f'{password}\r\n', "utf-8"))

    # enter command
    telnet.write(bytes(f'pse port {index} power {action}\r\n', 'utf-8'))
    # wait for return
    status = telnet.read_until(match=b'OK', timeout=7.0)
    # close connection
    telnet.close()
    status = status.decode('utf-8')
    if "OK" in status:
        pass
    else:
        print("Could not set power")
        raise Exception


def power_get(host, port, index: int) -> bool:
    """
    Get current state of a given socket number.
    - host: spe-switch-device adress
    - port: standard is 23
    - index: depends on spe-switch-device 1-n (n is the number of spe-switch-ports)
    """
    username = "admin"
    password = "private"
    status = None

    telnet = Telnet(host=host, port=port)

    # login user with password
    telnet.read_until(match=b'User: ')
    telnet.write(bytes(f'{username}\r\n', "utf-8"))
    telnet.read_until(match=b'Password: ')
    telnet.write(bytes(f'{password}\r\n', "utf-8"))

    # enter command
    telnet.write(bytes(f'show pse port port-no {index}\r\n', "utf-8"))
    # wait for return
    status = telnet.read_until(match=b'Mode')
    status = status.decode("utf-8")
    # close connection
    telnet.close()
    # check status
    if "OK" in status:
        status = status.split("Status :  ")[1].splitlines()[0]
    else:
        print("Could not get power")
        raise Exception
    return True if 'enable' in status else False
