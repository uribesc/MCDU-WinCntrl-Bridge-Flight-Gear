"""Convert the MCDU data exported by FlightGear into a 14 x 24 character page."""

import re
from mcdu_layout_data import OVERLAYS, TEXTS

ROWS = 14
COLS = 24
LARGE_IDS = {'Scratchpad', 'Simple_Title', 'Simple_Title2'}
SMALL_LIMIT = 56
PALETTE = {'white': (255, 255, 255), 'green': (13, 192, 75), 'cyan': (23, 154, 183), 'amber': (187, 97, 0), 'yellow': (238, 238, 0), 'magenta': (176, 85, 192), 'red': (255, 0, 0)}
SYMBOLS = {'box': '☐', 'star': '*', 'left': '←', 'right': '→', 'up': '↑', 'down': '↓'}
OVERLAY_DEFAULT_COLORS = {'box': 'amber'}


def blank_page() -> list:
    """Create an empty page.

    -> list of rows, where each cell is a tuple (character, color, small font).
    """
    return [[(' ', 'white', False) for _ in range(COLS)] for _ in range(ROWS)]


def color_name(value: str, default: str = 'white') -> str:
    """Find the closest display color for a FlightGear color string.

    value: color such as '#ffffff', 'rgb(13,192,75)' or 'rgba(1,1,1,1)'.
    default: color name used when the value cannot be read.
    -> color name from PALETTE.
    """
    rgb = parse_color(value)
    if rgb is None:
        return default
    return min(PALETTE, key=lambda name: sum((a - b) ** 2 for a, b in zip(PALETTE[name], rgb)))


def parse_color(value: str) -> tuple:
    """Read red, green and blue values from a color string.

    value: color string from the FlightGear canvas.
    -> tuple of three values from 0 to 255, or None if the text is not a color.
    """
    text = (value or '').strip().lower()
    if re.fullmatch('#[0-9a-f]{6}', text):
        return tuple(int(text[i:i + 2], 16) for i in (1, 3, 5))
    if re.fullmatch('#[0-9a-f]{3}', text):
        return tuple(int(text[i] * 2, 16) for i in (1, 2, 3))
    match = re.fullmatch(r'rgba?\(([^)]*)\)', text)
    if match is None:
        return None
    numbers = [float(part) for part in match.group(1).split(',')[:3]]
    if len(numbers) != 3:
        return None
    if max(numbers) <= 1:
        numbers = [number * 255 for number in numbers]
    return tuple(numbers)


def text_start(text: str, position: float, anchor: str) -> int:
    """Find the first column of a text.

    text: text to place.
    position: anchor position in columns.
    anchor: 'start', 'middle' or 'end'.
    -> column of the first character. It can be outside the screen.
    """
    if anchor == 'end':
        return round(position) - len(text)
    if anchor == 'middle':
        return int(position - len(text) / 2 + 0.5)
    return round(position)


def put_text(page: list, row: int, start: int, text: str, color: str, small: bool) -> None:
    """Write text on a page. Spaces keep the characters already on the page.

    page: page to change.
    row: row number.
    start: first column.
    text: text to write.
    color: color name.
    small: True to use the small font.
    -> None.
    """
    if row < 0 or row >= ROWS:
        return
    for offset, character in enumerate(text):
        column = start + offset
        if character != ' ' and 0 <= column < COLS:
            page[row][column] = (character, color, small)


def build_page(export: str) -> list:
    """Build a page from the text exported by the add-on.

    export: one element per line, as id, text, color and font size separated by tabs.
    -> page made by blank_page.
    """
    page = blank_page()
    overlays = []
    for line in export.split('\n'):
        fields = line.split('\t')
        if len(fields) != 4:
            continue
        element_id, text, color, size = fields
        if element_id in OVERLAYS:
            overlays.append((element_id, color))
        elif element_id in TEXTS:
            row, position, anchor = TEXTS[element_id]
            small = is_small(element_id, size)
            put_text(page, row, text_start(text, position, anchor), text, color_name(color), small)
    for element_id, color in overlays:
        row, columns, symbol = OVERLAYS[element_id]
        symbol_color = color_name(color, OVERLAY_DEFAULT_COLORS.get(symbol, 'white'))
        for column in columns:
            put_text(page, row, column, SYMBOLS[symbol], symbol_color, False)
    return page


def is_small(element_id: str, size: str) -> bool:
    """Decide if a text uses the small font.

    element_id: canvas element id.
    size: font size as text.
    -> True when the small font must be used.
    """
    if element_id in LARGE_IDS:
        return False
    try:
        return float(size) <= SMALL_LIMIT
    except ValueError:
        return False


def message_page(lines: list) -> list:
    """Create a page that shows a message from the bridge.

    lines: list of tuples (row, text, color name).
    -> page made by blank_page.
    """
    page = blank_page()
    for row, text, color in lines:
        put_text(page, row, text_start(text, 12, 'middle'), text, color, False)
    return page


def page_to_text(page: list) -> str:
    """Convert a page into plain text for logs and tests.

    page: page made by blank_page.
    -> text with one line per row.
    """
    return '\n'.join(''.join(cell[0] for cell in row) for row in page)
