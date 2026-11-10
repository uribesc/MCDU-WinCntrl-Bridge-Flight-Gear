"""Key numbers of the MCDU and the A320-family function used by each key."""

KEY_NAMES = {}
KEY_ACTIONS = {}
LOCAL_BRIGHTER = 18
LOCAL_DIMMER = 25
CLEAR_KEY = 73

for index in range(6):
    KEY_NAMES[index] = f'LSK{index + 1}L'
    KEY_ACTIONS[index] = ('lskbutton', str(index + 1))
    KEY_NAMES[index + 6] = f'LSK{index + 1}R'
    KEY_ACTIONS[index + 6] = ('rskbutton', str(index + 1))

PAGE_KEYS = {12: ('DIR', 'dirto'), 13: ('PROG', 'prog'), 14: ('PERF', 'perf'), 15: ('INIT', 'init'), 16: ('DATA', 'data'), 19: ('F-PLN', 'f-pln'), 20: ('RAD NAV', 'radnav'), 21: ('FUEL PRED', 'fuel-pred'), 23: ('ATC COMM', 'atc'), 24: ('MCDU MENU', 'mcdu'), 26: ('AIRPORT', 'airport')}
for number, (name, page) in PAGE_KEYS.items():
    KEY_NAMES[number] = name
    KEY_ACTIONS[number] = ('pagebutton', page)

ARROW_KEYS = {28: 'left', 29: 'up', 30: 'right', 31: 'down'}
for number, direction in ARROW_KEYS.items():
    KEY_NAMES[number] = f'ARROW {direction.upper()}'
    KEY_ACTIONS[number] = ('arrowbutton', direction)

DIGIT_ORDER = {32: '1', 33: '2', 34: '3', 35: '4', 36: '5', 37: '6', 38: '7', 39: '8', 40: '9', 42: '0'}
for number, digit in DIGIT_ORDER.items():
    KEY_NAMES[number] = digit
    KEY_ACTIONS[number] = ('button', digit)

for index in range(26):
    letter = chr(ord('A') + index)
    KEY_NAMES[44 + index] = letter
    KEY_ACTIONS[44 + index] = ('button', letter)

SYMBOL_KEYS = {41: ('.', 'DOT'), 43: ('+/-', 'PLUSMINUS'), 70: ('/', 'SLASH'), 71: ('SP', 'SP'), 72: ('OVFY', 'OVFY'), 73: ('CLR', 'CLR')}
for number, (name, value) in SYMBOL_KEYS.items():
    KEY_NAMES[number] = name
    KEY_ACTIONS[number] = ('button', value)

KEY_NAMES[17] = 'BLANK 1'
KEY_NAMES[18] = 'BRT'
KEY_NAMES[22] = 'SEC F-PLN'
KEY_NAMES[25] = 'DIM'
KEY_NAMES[27] = 'BLANK 2'


def changed_keys(previous: int, current: int) -> list:
    """Find the keys that changed between two USB reports.

    previous: earlier key bits.
    current: new key bits.
    -> list of tuples (key number, True if pressed).
    """
    difference = previous ^ current
    return [(number, bool(current >> number & 1)) for number in range(74) if difference >> number & 1]
