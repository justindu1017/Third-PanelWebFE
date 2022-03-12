from pymodbus.client.sync import ModbusTcpClient as Client
from pymodbus.exceptions import ConnectionException
from typing import Optional, Union
from exception import GetRegistersException


def get_registers_by_address(client: Client, address: int, count: int) -> Optional[Union[list, bool]]:
    try:
        client.connect()
        r = client.read_holding_registers(address=address, count=count)
        client.close()
        try:
            print(r)
            return r.registers
        except AttributeError:
            raise GetRegistersException

    except ConnectionException as e:
        return False
    finally:
        client.close()
