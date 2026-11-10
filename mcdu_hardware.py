"""Low level USB driver for the WinWing / WINCTRL MCDU.

The USB protocol and the init packets come from XSchenFly by memo5 (GPL-3.0).
"""

import hid

VENDOR_ID = 0x4098
CAPTAIN_PID = 0xBB36
FIRST_OFFICER_PID = 0xBB3E
OBSERVER_PID = 0xBB3A
KNOWN_PIDS = {CAPTAIN_PID: 'captain', FIRST_OFFICER_PID: 'first officer', OBSERVER_PID: 'observer'}
PACKET_DATA_SIZE = 63
KEY_REPORT_SIZE = 25
KEY_BYTES = 12
COLOR_CODES = {'amber': 0x0021, 'white': 0x0042, 'cyan': 0x0063, 'green': 0x0084, 'magenta': 0x00A5, 'red': 0x00C6, 'yellow': 0x00E7}
SMALL_FONT_OFFSET = 0x016B
SPECIAL_CHARACTERS = {'<': '←', '>': '→'}
UTF8_CHARACTERS = {'←', '↑', '→', '↓', '☐', '°', 'Δ'}
BACKLIGHT = 0
SCREEN_BACKLIGHT = 1
LED_BRIGHTNESS = 2
LED_FAIL = 8
LED_FM = 9
LED_MCDU = 10
LED_MENU = 11
LED_FM1 = 12
LED_IND = 13
LED_RDY = 14
LED_STATUS = 15
LED_FM2 = 16
ALL_LEDS = [LED_FAIL, LED_FM, LED_MCDU, LED_MENU, LED_FM1, LED_IND, LED_RDY, LED_STATUS, LED_FM2]

# Packets that prepare the display and its color table.
INIT_PACKETS = []
INIT_PACKETS.append(bytes.fromhex('f000013832bb00001e010000c4240a00000000000032bb000018010000c4240a000008000000340018000e00180032bb000019010000c4240a00000e00000000'))
INIT_PACKETS.append(bytes.fromhex('f0000238000000010005000000020000000000000032bb000019010000c4240a00000e000000010006000000030000000000000032bb00001901000000000000'))
INIT_PACKETS.append(bytes.fromhex('f000033876721900000e0000000200000000ff040000000000000032bb00001901000076721900000e000000020000a5ffff050000000000000032bb00000000'))
INIT_PACKETS.append(bytes.fromhex('f000043800001901000076721900000e0000000200ffffffff060000000000000032bb00001901000076721900000e0000000200ffff00ff0700000000000000'))
INIT_PACKETS.append(bytes.fromhex('f00005380000000032bb00001901000076721900000e00000002003dff00ff080000000000000032bb00001901000076721900000e0000000200ff6300000000'))
INIT_PACKETS.append(bytes.fromhex('f0000638ffff090000000000000032bb00001901000076721900000e00000002000000ffff0a0000000000000032bb00001901000076721900000e0000000000'))
INIT_PACKETS.append(bytes.fromhex('f00007380000020000ffffff0b0000000000000032bb00001901000076721900000e0000000200425c61ff0c0000000000000032bb0000190100007600000000'))
INIT_PACKETS.append(bytes.fromhex('f0000838721900000e0000000200777777ff0d0000000000000032bb00001901000076721900000e00000002005e7379ff0e0000000000000032bb0000000000'))
INIT_PACKETS.append(bytes.fromhex('f0000938001901000076721900000e0000000300202020ff0f0000000000000032bb00001901000076721900000e000000030000a5ffff100000000000000000'))
INIT_PACKETS.append(bytes.fromhex('f0000a3800000032bb00001901000076721900000e0000000300ffffffff110000000000000032bb00001901000076721900000e0000000300ffff0000000000'))
INIT_PACKETS.append(bytes.fromhex('f0000b38ff120000000000000032bb00001901000076721900000e00000003003dff00ff130000000000000032bb00001901000076721900000e000000000000'))
INIT_PACKETS.append(bytes.fromhex('f0000c38000300ff63ffff140000000000000032bb00001901000076721900000e00000003000000ffff150000000000000032bb000019010000767200000000'))
INIT_PACKETS.append(bytes.fromhex('f0000d381900000e000000030000ffffff160000000000000032bb00001901000076721900000e0000000300425c61ff170000000000000032bb000000000000'))
INIT_PACKETS.append(bytes.fromhex('f0000e381901000076721900000e0000000300777777ff180000000000000032bb00001901000076721900000e00000003005e7379ff19000000000000000000'))
INIT_PACKETS.append(bytes.fromhex('f0000f38000032bb00001901000076721900000e0000000400000000001a0000000000000032bb00001901000076721900000e00000004000100000000000000'))
INIT_PACKETS.append(bytes.fromhex('f00010381b0000000000000032bb00001901000076721900000e0000000400020000001c0000000000000032bb00001a01000076721900000100000000000000'))
INIT_PACKETS.append(bytes.fromhex('f00011120232bb00001c010000767219000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000'))

def list_devices() -> list:
    """Find the connected WinWing devices.

    -> list of device dictionaries from hid.enumerate.
    """
    return hid.enumerate(VENDOR_ID, 0)


def find_mcdu() -> dict:
    """Find the first connected MCDU.

    -> device dictionary from hid.enumerate, or None if there is no MCDU.
    """
    for device in list_devices():
        if device['product_id'] in KNOWN_PIDS or 'MCDU' in (device.get('product_string') or '').upper():
            return device
    return None


def encode_character(character: str) -> list:
    """Convert one character into the bytes used by the display.

    character: character to convert.
    -> list of bytes.
    """
    character = SPECIAL_CHARACTERS.get(character, character)
    if character in UTF8_CHARACTERS:
        return list(character.encode('utf-8'))
    if ord(character) < 128:
        return [ord(character)]
    return [ord('?')]


def encode_page(page: list) -> list:
    """Convert a page into the byte stream used by the display.

    page: list of rows, where each cell is a tuple (character, color, small font).
    -> list of bytes.
    """
    data = []
    for row in page:
        for character, color, small in row:
            code = COLOR_CODES.get(color, COLOR_CODES['white'])
            if small:
                code += SMALL_FONT_OFFSET
            data.extend([code & 0xFF, (code >> 8) & 0xFF])
            data.extend(encode_character(character))
    return data


def split_packets(data: list) -> list:
    """Split display bytes into USB packets.

    data: bytes made by encode_page.
    -> list of 64 byte packets.
    """
    packets = []
    for start in range(0, len(data), PACKET_DATA_SIZE):
        chunk = data[start:start + PACKET_DATA_SIZE]
        packets.append(bytes([0xF2] + chunk + [0] * (PACKET_DATA_SIZE - len(chunk))))
    return packets


def decode_keys(report: list) -> int:
    """Read the pressed keys from a USB report.

    report: input report from the MCDU.
    -> integer with one bit per key.
    """
    keys = 0
    for index in range(KEY_BYTES):
        keys |= report[index + 1] << (8 * index)
    return keys


class McduDevice:
    """Open connection to one MCDU."""

    def __init__(self, info: dict) -> None:
        """Open the USB device and prepare the display.

        info: device dictionary from find_mcdu.
        -> None.
        """
        self.info = info
        self.device = hid.device()
        self.device.open_path(info['path'])
        self.device.set_nonblocking(False)
        for packet in INIT_PACKETS:
            self.device.write(packet)

    def show_page(self, page: list) -> None:
        """Draw a full page on the display.

        page: list of rows, where each cell is a tuple (character, color, small font).
        -> None.
        """
        for packet in split_packets(encode_page(page)):
            self.device.write(packet)

    def set_light(self, light: int, value: int) -> None:
        """Set a brightness or a LED.

        light: brightness channel or LED number.
        value: value from 0 to 255.
        -> None.
        """
        self.device.write(bytes([0x02, 0x32, 0xBB, 0, 0, 3, 0x49, light, max(0, min(255, value)), 0, 0, 0, 0, 0]))

    def set_led(self, led: int, is_on: bool) -> None:
        """Turn a LED on or off.

        led: LED number.
        is_on: True to turn it on.
        -> None.
        """
        self.set_light(led, 1 if is_on else 0)

    def read_keys(self, timeout_ms: int) -> int:
        """Wait for a key report.

        timeout_ms: maximum waiting time in milliseconds.
        -> integer with one bit per key, or None if there is no key report.
        """
        report = self.device.read(KEY_REPORT_SIZE, timeout_ms)
        if len(report) != KEY_REPORT_SIZE:
            return None
        return decode_keys(report)

    def close(self) -> None:
        """Close the USB device.

        -> None.
        """
        self.device.close()
