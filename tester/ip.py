from time import sleep
from pymodbus.client.sync import ModbusTcpClient as Client
from get_data import get_registers_by_address
from pymodbus.exceptions import ConnectionException


def index(regi: int = 1, count: int = 0):
    client = Client(host='192.168.1.180', port='502')
    try:

        r = get_registers_by_address(client=client, address=regi, count=count)
        print(r)
        return r
    except ConnectionException as e:
        return None


# while True:
index(regi=5, count=2)
sleep(0.3)
