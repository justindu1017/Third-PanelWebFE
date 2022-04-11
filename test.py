import asyncio
from datetime import datetime
from async_modbus import AsyncTCPClient
meters = [
    ['192.168.50.82', 502],
    ['192.168.1.180', 502],
    ['test.com', 502]
]


async def conn(index):
    print(f'start {index} at {datetime.now().strftime("%H:%M:%S")}')
    try:
        reader, writer = await asyncio.open_connection('localhost', 15020)
        client = AsyncTCPClient((reader, writer))
        await client.close()
        print(f'finish {index} at {datetime.now().strftime("%H:%M:%S")}')
    except Exception as e:
        print(e)
        print(
            f'connect failed {index} at {datetime.now().strftime("%H:%M:%S")}')


async def main(loop):
    while True:
        await asyncio.gather(*[conn(i) for i in range(len(meters))])

        await asyncio.sleep(1)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(loop))
    # loop.run_until_complete(print1(6))
