import asyncio
from bleak import BleakScanner

async def run():
    async with BleakScanner() as scanner:
        await asyncio.sleep(5.0)
        devices = await scanner.get_discovered_devices()
    for d in devices:
        print(d.name,d.address)

loop = asyncio.get_event_loop()
loop.run_until_complete(run())