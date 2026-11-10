# WinWing MCDU Bridge for FlightGear (A320-family)

This project connects a physical WinWing / WINCTRL MCDU to the MCDU of the **A320-family** aircraft in FlightGear:

- The **screen** of the physical MCDU shows the same as the aircraft MCDU, with colors and large and small fonts.
- The **keys** of the physical MCDU do the same as clicking the keys in the aircraft.
- Some **LEDs** show the connection status.

Requirements: Windows, Python 3, FlightGear 2024.1.1 or later, and the A320-family aircraft.

## How it works

The system has three parts that talk to each other:

```
 Physical MCDU  <── USB ──>  mcdu_bridge.py  <── HTTP ──>  FlightGear + add-on  ──>  A320 MCDU
 (screen,                    (Python program               (fgfs_addon, in Nasal)
  keys, LEDs)                 on your computer)
```

### 1. The FlightGear add-on (`fgfs_addon`)

This is a small program in Nasal, the internal language of FlightGear. It is loaded with the `--addon` option and does not change the aircraft. It has two jobs:

- **Export the screen.** Every 0.2 seconds it reads the visible texts of the aircraft MCDU (text, color and font size) and the symbols, such as arrows, boxes and stars. It stores them as text in the properties `/mcdu-bridge/unit0` (left MCDU) and `/mcdu-bridge/unit1` (right MCDU).
- **Receive the keys.** When the Python program writes a key to `/mcdu-bridge/key-input`, the add-on calls the matching aircraft function, the same one that runs when you click the key in the cockpit. It only accepts MCDU key functions, and only when the aircraft has electrical power.

It also writes the status to `/mcdu-bridge/status` (`loading`, `no-mcdu` or `ready`).

### 2. The FlightGear web server (`--httpd=8080`)

FlightGear has an internal web server that can read and write properties in JSON format. The Python program uses it to talk to the add-on, at `http://localhost:8080/json/mcdu-bridge/...`.

### 3. The Python program (`mcdu_bridge.py`)

It runs on your computer and works as the bridge:

1. It finds the MCDU over USB (vendor WinWing, `0x4098`) and prepares it.
2. Every 0.1 seconds it reads the exported screen from FlightGear.
3. It converts this data into a grid of **14 rows × 24 columns**, the size of the physical screen, and sends it over USB. It only redraws the screen when something changes.
4. It reads the keys of the physical MCDU and sends them to FlightGear.

If FlightGear or the add-on does not answer, the screen shows a message that explains the problem, and the program keeps trying. If you unplug the USB cable, it also reconnects by itself.

## Files

| File | What it does |
|---|---|
| `mcdu_bridge.py` | Main program: connects the MCDU to FlightGear. |
| `test_hardware.py` | Tests the MCDU without FlightGear: screen, LEDs and keys. |
| `mcdu_hardware.py` | USB driver for the MCDU: screen, LEDs, brightness and key reading. |
| `mcdu_keys.py` | Key table: number of each key and the aircraft function it calls. |
| `mcdu_layout.py` | Converts the FlightGear data into the 14 × 24 character grid. |
| `mcdu_layout_data.py` | Position of each element of the A320 screen, computed from the original aircraft drawing. |
| `fgfs_addon/addon-main.nas` | FlightGear add-on: exports the screen and runs the keys. |
| `fgfs_addon/addon-metadata.xml` | Add-on data that FlightGear needs to load it. |
| `requirements.txt` | Required Python package (`hidapi`). |

## Installation

1. Unzip the file, for example to `C:\mcdu_bridge`.
2. Open a terminal in this folder and install the dependency:

   ```
   py -m pip install -r requirements.txt
   ```

## Hardware test (without FlightGear)

1. Close **SimAppPro**. If you used it, unplug the MCDU and plug it in again.
2. Run:

   ```
   py test_hardware.py
   ```

3. Check that:
   - The screen shows colors, large and small fonts, and symbols.
   - The LEDs turn on one by one.
   - Each key you press prints its name in the terminal.

## FlightGear setup

In the FlightGear launcher, under **Settings > Additional Settings**, add:

```
--httpd=8080
--addon=C:\mcdu_bridge\fgfs_addon
```

The `--addon` path must be the folder that contains `addon-metadata.xml` and `addon-main.nas`. To find it:

1. In File Explorer, open the `fgfs_addon` folder.
2. Copy the path from the address bar and paste it after `--addon=`.

Note that when you unzip, Windows often creates a folder inside another folder, for example `C:\mcdu_bridge\mcdu_bridge\fgfs_addon`. If the path has spaces, put it in quotes: `--addon="C:\my folder\fgfs_addon"`.

Then select an aircraft from the **A320-family**.

## Usage

1. Start FlightGear with the A320-family.
2. With SimAppPro closed, run:

   ```
   py mcdu_bridge.py
   ```

3. Turn on electrical power in the aircraft. As in the real aircraft, the MCDU does not work without power.

### Options

| Option | What it does |
|---|---|
| `--side left` / `--side right` | Chooses which aircraft MCDU you control. By default it comes from the MCDU model (captain or first officer). |
| `--brightness 180` | First brightness, from 0 to 255. |
| `--port 8080` | FlightGear web server port, if you set another one in `--httpd`. |
| `--host 127.0.0.1` | Computer that runs FlightGear, if it is not the same one. |
| `--dump` | Prints the screen data from FlightGear in the terminal. Useful to find problems. |

### Special keys

- **BRT** and **DIM** change the brightness of the physical MCDU.
- Holding **CLR** clears the whole entry line (scratchpad), as in the aircraft.
- **SEC F-PLN** and the two blank keys do nothing, because the A320-family has no function for them.

### LEDs

- **FM1** is on when you control the left MCDU, and **FM2** when you control the right one.
- **FAIL** is on when no data comes from FlightGear.
- The aircraft does not export the other lights, so they stay off.

## Screen messages

| Message | Meaning | What to do |
|---|---|---|
| `WAITING FOR FLIGHTGEAR` | The program cannot connect to FlightGear. | Check that FlightGear is running with `--httpd=8080`. |
| `ADD-ON NOT LOADED` | FlightGear answers, but the add-on is not loaded. | Check the `--addon` path. |
| `A320-FAMILY MCDU NOT FOUND` | The loaded aircraft is not the A320-family. | Load an A320-family aircraft. |
| `LOADING AIRCRAFT` | The aircraft is still loading. | Wait a few seconds. |
| Black screen | The aircraft is loaded but has no power. | Turn on aircraft power. |

## Troubleshooting

| Problem | Solution |
|---|---|
| `MCDU not found` in the terminal | Close SimAppPro and check the USB cable. |
| `Unable to find add-on metadata file` in FlightGear | The `--addon` path is not the `fgfs_addon` folder. See the setup section. |
| Text or symbols are missing or shifted | Run `py mcdu_bridge.py --dump` and open `http://localhost:8080/json/mcdu-bridge/missing-elements` in a browser. Save the number and the terminal output for review. |
| A key does the wrong action | Run `py test_hardware.py` and note the number and name printed when you press it. |

## Limitations

- It only works with the **A320-family** aircraft.
- The physical screen is a character grid, so the graphic symbols of the aircraft become characters (`☐`, `←`, `↑`, `*`). Some text may be slightly shifted.
- It cannot be used at the same time as SimAppPro.

## License

This project is free software, released under the **GNU General Public License v3.0**. See the `LICENSE` file for the full text.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.

## Credits

### XSchenFly by memo5

The USB protocol of the MCDU (screen data format, color codes, LED and brightness commands, key reports) and the screen init packets in `mcdu_hardware.py` come from [XSchenFly](https://github.com/schenlap/XSchenFly) by memo5, licensed under GPL-3.0.

This code has been **modified**: it was rewritten as a separate driver and adapted to work with FlightGear instead of X-Plane.

### A320-family

The screen element names and positions in `mcdu_layout_data.py` were computed from the MCDU display drawing (`Models/Instruments/MCDU/res/mcdu.svg`) of the [A320-family](https://github.com/legoboyvdlp/A320-family) for FlightGear, by Josh Davidson, Jonathan Redpath, merspieler, Matthew Maring, Thorsten Herrmann, Semir Gebran and contributors. The A320-family is licensed under GPL-2.0.

This file only contains technical data (element names, rows and columns). It does not contain any code or graphics from the A320-family. The add-on calls the public functions of the aircraft at run time, and it does not include any part of the aircraft.

The A320-family is not included in this project. You must install it separately in FlightGear.

### Other references

- [pywinwing](https://devleaks.github.io/pywinwing) by devleaks, used as a reference for the WinWing devices.

## Disclaimer

This is an independent community project. It is not affiliated with or endorsed by WinWing, the FlightGear project, the A320-family developers or Airbus. All trademarks belong to their owners.
