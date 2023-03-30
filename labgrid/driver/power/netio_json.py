#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''
Netio control:
 - This Programm is able to switch on/off specific netio sockets by using the HTTP-JSON-API.
'''
__author__    = "Eugen Wiens, Christian Happ"
__copyright__ = "Copyright 2022, JUMO GmbH & Co. KG"
__email__     = "Eugen.Wiens@jumo.net, Christian.Happ@jumo.net"
__date__      = "2022-04-02"
__status__    = "Production"

import argparse
import json
import termcolor
import requests


class NetioControl:
    '''
    Netio-Class to switch sockets via HTTP-JSON-API
    '''
    __host = str()
    __port = int()
    __username = str()
    __password = str()
    __telnetConnection = None

    def __init__( self, host, port=80, username=None, password=None ):
        '''
        Define Connection details
        '''
        self.__host     = host
        self.__port     = port
        self.__username = username
        self.__password = password

    def setState(self, socketID, action):
        '''
        Set power state by a socket port number (e.g. 1 - 8) and an action ('1'-'4').
        '''
        state = None
        response = requests.post(self.__createRequestUrl(), json=self.__getRequestJsonData(socketID, action))

        if response.ok:
            responseDict = json.loads(response.text)
            outputStates = responseDict['Outputs']

            for outputState in outputStates:
                if outputState['ID'] == socketID:
                    state = outputState
                    break
        else:
            raise Exception(f"Cannot SET the power state for socket number: {socketID} for action: {action}. Error code: {response.text}" )

        return state

    def getState(self, socketID):
        '''
        Read power state of a given socket number.
        '''
        state = None
        response = requests.get(self.__createRequestUrl())

        if response.ok:
            responseDict = json.loads(response.text)
            outputStates = responseDict['Outputs']

            for outputState in outputStates:
                if outputState['ID'] == socketID:
                    state = outputState
                    break
        else:
            raise Exception(f"Cannot get the power state for socket {socketID}. Error code: {response.text}")

        return state

    def convertSocketID(self, socketID) -> int:
        try:
            socketID = int(socketID)
        except ValueError as e:
            raise Exception(f"socketID \"{socketID}\" could not converted to an integer: {e}!")

        return socketID


    def __createRequestUrl(self) -> str:
        requestUrl = 'http://'

        if self.__username and self.__password:
            requestUrl += f'{self.__username}:{self.__password}@'

        requestUrl += self.__host

        if self.__port:
            requestUrl += f':{self.__port}'

        requestUrl += '/netio.json'

        return  requestUrl

    def __getRequestJsonData(self, socketID, action) -> str:
        data = f'{{"Outputs":[{{"ID":{socketID},"Action":{self.__convertAction(action)}}}]}}'

        return json.loads(data)

    def __toStr(self, toConvert) -> str:
        if toConvert == 1 or toConvert == True:
            toConvert = "1"
        elif toConvert == 0 or toConvert == False:
            toConvert = "0"
        return toConvert

    def __convertAction(self, action) -> str:
        action = self.__toStr(action)

        try:
            assert 0 <= int(action) <= 4
            return action
        except AssertionError as e:
                raise Exception(f"Action \"{action}\" seems not right, should be between -> '0'-'4'!")


def getSocketStatusPrint(socketStatus: dict) -> str:
    return f"Power state for socket {socketStatus['ID']}: {socketStatus['Name']}"

def printStatus(socketStatus: dict):
    if True == socketStatus['State']:
        print( f"[ {termcolor.colored('on', 'green')} ] {getSocketStatusPrint(socketStatus)}")
    else:
        print( f"[ {termcolor.colored('off', 'red')} ] {getSocketStatusPrint(socketStatus)}")


def main():
    parser = argparse.ArgumentParser(description="Control NETIO ")

    parser.add_argument('--host', type=str, required=True, help="Hostname of NETIO. (e.g. ew-netio02.jumo.net)")
    parser.add_argument('--username', type=str, default=None, help="Username will be used to connect.")
    parser.add_argument('--password', type=str, default=None, help="Password will be used to connect.")
    parser.add_argument('--port', type=int, default=80, help="Port for HTTP interface of NETIO. (default = 80))")
    parser.add_argument('--socket', '-s', type=int, required=True, help='Specify which socket have to switch. (required)')
    parser.add_argument('-v', '--value', choices=['0', '1', '2', '3', '4'], type=str, default='4', help='''Select new state. (default = 4)
                        { 0 – Turn OFF,
                          1 – Turn ON,
                          2 – Short OFF delay (restart),
                          3 – Short ON delay,
                          4 – Toggle (invert the state)
                        }''')
    parser.add_argument('--show-status', action='store_true', help='Show the current status of the given outlet ID.')
    args = parser.parse_args()

    netio = NetioControl( args.host, args.port)

    if args.show_status:
        printStatus(netio.getState(args.socket))
    else:
        printStatus(netio.setState(args.socket, args.value))


############################################################
# Add missing labgrid-netio JSON power driver API functions
# Set the model in the YML-CFG to 'netio_json'
############################################################
def power_set(host, port, index, value):
    # Username, password and port not available via labgrid
    netio = NetioControl(host, port)
    print(netio.setState(netio.convertSocketID(index), value))

def power_get(host, port, index):

    netio = NetioControl(host, port)
    return netio.getState(netio.convertSocketID(index))


if '__main__' == __name__:
    main()
