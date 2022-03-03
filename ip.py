# 1 min or 5 min 10 sec


def index(regi: int = 1, count: int = 0):
    client = Client(host='192.168.50.82', port='502')
    try:

        r = get_registers_by_address(client=client, address=regi, count=count)

        return r
    except ConnectionException as e:
        return None


while:
    index(ip, port, regi: int=1, count: int=0):
