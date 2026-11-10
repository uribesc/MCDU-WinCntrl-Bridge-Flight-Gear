"""Test the MCDU without FlightGear: draw a test page and print the pressed keys."""

import time

import mcdu_hardware as hardware
from mcdu_keys import KEY_NAMES, changed_keys
from mcdu_layout import blank_page, page_to_text, put_text


def test_page() -> list:
    """Create a page that shows colors, fonts and symbols.

    -> page for the display.
    """
    page = blank_page()
    put_text(page, 0, 3, 'MCDU HARDWARE TEST', 'white', False)
    rows = [('WHITE', 'white'), ('AMBER', 'amber'), ('CYAN', 'cyan'), ('GREEN', 'green'), ('MAGENTA', 'magenta'), ('YELLOW', 'yellow'), ('RED', 'red')]
    for index, (name, color) in enumerate(rows):
        put_text(page, index + 2, 0, name, color, False)
        put_text(page, index + 2, 14, name, color, True)
    put_text(page, 10, 0, '← → ↑ ↓ ☐ ° [ ] * /', 'white', False)
    put_text(page, 11, 0, '123456789012345678901234', 'green', False)
    put_text(page, 13, 0, 'PRESS KEYS, CTRL+C ENDS', 'amber', False)
    return page


def main() -> None:
    """Run the hardware test.

    -> None.
    """
    devices = hardware.list_devices()
    print(f'WinWing USB entries found: {len(devices)}')
    for entry in devices:
        print(f'  PID {entry["product_id"]:#06x} | {entry.get("product_string")} | usage {entry.get("usage_page")}:{entry.get("usage")}')
    info = hardware.find_mcdu()
    if info is None:
        print('MCDU not found. Close SimAppPro and check the USB cable.')
        return
    device = hardware.McduDevice(info)
    device.set_light(hardware.BACKLIGHT, 180)
    device.set_light(hardware.SCREEN_BACKLIGHT, 180)
    device.set_light(hardware.LED_BRIGHTNESS, 180)
    device.show_page(test_page())
    print(page_to_text(test_page()))
    for led in hardware.ALL_LEDS:
        device.set_led(led, True)
        time.sleep(0.2)
        device.set_led(led, False)
    print('Press keys. Each name must match the key. Press Ctrl+C to end.')
    previous = 0
    try:
        while True:
            keys = device.read_keys(100)
            if keys is None:
                continue
            for number, pressed in changed_keys(previous, keys):
                if pressed:
                    print(f'{number}: {KEY_NAMES.get(number, "UNKNOWN")}', flush=True)
            previous = keys
    except KeyboardInterrupt:
        print('Test ended.')
    finally:
        device.close()


if __name__ == '__main__':
    main()
