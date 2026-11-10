"""Bridge between a WinWing / WINCTRL MCDU and the A320-family in FlightGear."""

import argparse
import json
import queue
import threading
import time
import urllib.error
import urllib.request

import mcdu_hardware as hardware
from mcdu_keys import CLEAR_KEY, KEY_ACTIONS, LOCAL_BRIGHTER, LOCAL_DIMMER, changed_keys
from mcdu_layout import build_page, message_page

POLL_SECONDS = 0.1
CLEAR_REPEAT_SECONDS = 0.25
READ_TIMEOUT_MS = 20
USB_RETRY_SECONDS = 2
BRIGHTNESS_STEP = 25
HTTP_TIMEOUT_SECONDS = 2


class SimLink(threading.Thread):
    """Background thread that exchanges data with FlightGear."""

    def __init__(self, host: str, port: int, side: int, dump: bool) -> None:
        """Prepare the connection data.

        host: FlightGear computer name or address.
        port: FlightGear HTTP port.
        side: 0 for the left MCDU, 1 for the right MCDU.
        dump: True to print the raw data from FlightGear.
        -> None.
        """
        super().__init__(daemon=True)
        self.base_url = f'http://{host}:{port}/json/mcdu-bridge'
        self.side = side
        self.dump = dump
        self.opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        self.keys = queue.Queue()
        self.lock = threading.Lock()
        self.state = 'no-simulator'
        self.export = ''
        self.version = 0

    def read_value(self, name: str) -> str:
        """Read one bridge property.

        name: property name below /mcdu-bridge.
        -> property value as text.
        """
        with self.opener.open(f'{self.base_url}/{name}', timeout=HTTP_TIMEOUT_SECONDS) as response:
            return str(json.loads(response.read().decode('utf-8', 'replace')).get('value', ''))

    def write_value(self, name: str, value: str) -> None:
        """Write one bridge property.

        name: property name below /mcdu-bridge.
        value: text to write.
        -> None.
        """
        body = json.dumps({'value': value}).encode('utf-8')
        request = urllib.request.Request(f'{self.base_url}/{name}', data=body, method='POST', headers={'Content-Type': 'application/json'})
        with self.opener.open(request, timeout=HTTP_TIMEOUT_SECONDS) as response:
            response.read()

    def send_key(self, function: str, argument: str, event: str = 'none') -> None:
        """Queue a key command for FlightGear.

        function: A320-family function name.
        argument: key name for that function.
        event: 'down', 'up' or 'none'.
        -> None.
        """
        self.keys.put(f'{self.side}|{function}|{argument}|{event}')

    def set_state(self, state: str, export: str = '') -> None:
        """Store the latest state for the main thread.

        state: connection state.
        export: exported screen data.
        -> None.
        """
        with self.lock:
            if state != self.state or export != self.export:
                self.state = state
                self.export = export
                self.version += 1

    def get_state(self) -> tuple:
        """Read the latest state.

        -> tuple (version, state, exported screen data).
        """
        with self.lock:
            return self.version, self.state, self.export

    def poll(self) -> None:
        """Send waiting keys and read the screen once.

        -> None.
        """
        while not self.keys.empty():
            self.write_value('key-input', self.keys.get_nowait())
        status = self.read_value('status')
        if status != 'ready':
            self.set_state(status)
            return
        export = self.read_value(f'unit{self.side}')
        if self.dump and export != self.get_state()[2]:
            print(export.replace('\t', ' | '), flush=True)
        self.set_state('ready', export)

    def run(self) -> None:
        """Run the exchange loop until the program ends.

        -> None.
        """
        while True:
            try:
                self.poll()
            except urllib.error.HTTPError as error:
                state = 'no-addon' if error.code == 404 else 'no-simulator'
                self.set_state(state)
            except (OSError, ValueError):
                self.set_state('no-simulator')
            time.sleep(POLL_SECONDS)


def state_page(state: str) -> list:
    """Create the page shown when the sim screen is not available.

    state: connection state.
    -> page for the display.
    """
    if state == 'no-simulator':
        return message_page([(3, 'FLIGHTGEAR BRIDGE', 'white'), (6, 'WAITING FOR', 'amber'), (7, 'FLIGHTGEAR', 'amber'), (10, 'USE --HTTPD=8080', 'cyan')])
    if state == 'no-addon':
        return message_page([(3, 'FLIGHTGEAR BRIDGE', 'white'), (6, 'ADD-ON NOT LOADED', 'amber'), (10, 'USE --ADDON=...', 'cyan')])
    if state == 'no-mcdu':
        return message_page([(3, 'FLIGHTGEAR BRIDGE', 'white'), (6, 'A320-FAMILY MCDU', 'amber'), (7, 'NOT FOUND', 'amber')])
    return message_page([(3, 'FLIGHTGEAR BRIDGE', 'white'), (6, 'LOADING AIRCRAFT', 'amber')])


def run_session(device: hardware.McduDevice, link: SimLink, side: int, brightness: int) -> None:
    """Run the bridge until the USB connection fails.

    device: open MCDU.
    link: running FlightGear link.
    side: 0 for the left MCDU, 1 for the right MCDU.
    brightness: first display brightness from 0 to 255.
    -> None.
    """
    device.set_light(hardware.BACKLIGHT, brightness)
    device.set_light(hardware.SCREEN_BACKLIGHT, brightness)
    device.set_light(hardware.LED_BRIGHTNESS, brightness)
    for led in hardware.ALL_LEDS:
        device.set_led(led, False)
    device.set_led(hardware.LED_FM2 if side else hardware.LED_FM1, True)
    shown_version = -1
    shown_fail = None
    previous_keys = 0
    next_clear_time = None
    while True:
        version, state, export = link.get_state()
        if version != shown_version:
            device.show_page(build_page(export) if state == 'ready' else state_page(state))
            shown_version = version
        if (state != 'ready') != shown_fail:
            shown_fail = state != 'ready'
            device.set_led(hardware.LED_FAIL, shown_fail)
        keys = device.read_keys(READ_TIMEOUT_MS)
        if keys is not None:
            for number, pressed in changed_keys(previous_keys, keys):
                if number == CLEAR_KEY:
                    link.send_key('button', 'CLR', 'down' if pressed else 'up')
                    next_clear_time = time.monotonic() + CLEAR_REPEAT_SECONDS if pressed else None
                elif number in (LOCAL_BRIGHTER, LOCAL_DIMMER) and pressed:
                    brightness += BRIGHTNESS_STEP if number == LOCAL_BRIGHTER else -BRIGHTNESS_STEP
                    brightness = max(0, min(255, brightness))
                    device.set_light(hardware.BACKLIGHT, brightness)
                    device.set_light(hardware.SCREEN_BACKLIGHT, brightness)
                elif number in KEY_ACTIONS and pressed:
                    link.send_key(*KEY_ACTIONS[number])
            previous_keys = keys
        if next_clear_time is not None and time.monotonic() >= next_clear_time:
            link.send_key('button', 'CLR', 'down')
            next_clear_time += CLEAR_REPEAT_SECONDS


def choose_side(requested: str, info: dict) -> int:
    """Choose the aircraft MCDU controlled by this device.

    requested: 'left', 'right' or 'auto'.
    info: device dictionary from hid.enumerate.
    -> 0 for the left MCDU, 1 for the right MCDU.
    """
    if requested == 'auto':
        return 1 if info['product_id'] == hardware.FIRST_OFFICER_PID else 0
    return 1 if requested == 'right' else 0


def main() -> None:
    """Read the options and keep the bridge running.

    -> None.
    """
    parser = argparse.ArgumentParser(description='WinWing MCDU bridge for the FlightGear A320-family')
    parser.add_argument('--host', default='127.0.0.1', help='FlightGear computer')
    parser.add_argument('--port', type=int, default=8080, help='FlightGear HTTP port')
    parser.add_argument('--side', choices=['auto', 'left', 'right'], default='auto', help='aircraft MCDU to control')
    parser.add_argument('--brightness', type=int, default=180, help='first brightness from 0 to 255')
    parser.add_argument('--dump', action='store_true', help='print the raw screen data')
    args = parser.parse_args()
    link = None
    while True:
        info = hardware.find_mcdu()
        if info is None:
            print('MCDU not found. Close SimAppPro and check the USB cable.', flush=True)
            time.sleep(USB_RETRY_SECONDS)
            continue
        side = choose_side(args.side, info)
        if link is None:
            link = SimLink(args.host, args.port, side, args.dump)
            link.start()
        print(f'MCDU found: {info.get("product_string")} (PID {info["product_id"]:#06x}). Side: {"right" if side else "left"}.', flush=True)
        device = None
        try:
            device = hardware.McduDevice(info)
            run_session(device, link, side, args.brightness)
        except (OSError, ValueError) as error:
            print(f'USB error: {error}. Trying again.', flush=True)
        finally:
            if device is not None:
                device.close()
        time.sleep(USB_RETRY_SECONDS)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Bridge stopped.')
