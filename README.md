# Pont WinWing MCDU per a FlightGear (A320-family)

Aquest projecte connecta un MCDU físic de WinWing / WINCTRL amb el MCDU de l'avió **A320-family** de FlightGear:

- La **pantalla** del MCDU físic mostra el mateix que el MCDU de l'avió, amb colors i lletra gran i petita.
- Les **tecles** del MCDU físic fan el mateix que clicar les tecles de l'avió.
- Alguns **LED** indiquen l'estat de la connexió.

Requisits: Windows, Python 3, FlightGear 2024.1.1 o posterior i l'avió A320-family.

## Com funciona

El sistema té tres peces que parlen entre elles:

```
 MCDU físic  <── USB ──>  mcdu_bridge.py  <── HTTP ──>  FlightGear + add-on  ──>  MCDU de l'A320
 (pantalla,               (programa Python              (fgfs_addon, en Nasal)
  tecles, LED)             al teu ordinador)
```

### 1. L'add-on de FlightGear (`fgfs_addon`)

És un petit programa en Nasal, el llenguatge intern de FlightGear, que es carrega amb l'opció `--addon`. No modifica l'avió. Fa dues feines:

- **Exporta la pantalla.** Cada 0,2 segons llegeix els textos visibles del MCDU de l'avió (text, color i mida de lletra) i també els símbols, com fletxes, caixes i asteriscs. Ho guarda com a text a les propietats `/mcdu-bridge/unit0` (MCDU esquerre) i `/mcdu-bridge/unit1` (MCDU dret).
- **Rep les tecles.** Quan el programa Python escriu una tecla a `/mcdu-bridge/key-input`, l'add-on crida la funció corresponent de l'avió, la mateixa que s'executa quan cliques la tecla al cockpit. Només accepta les funcions de tecla del MCDU, i només si l'avió té corrent elèctric.

També escriu l'estat a `/mcdu-bridge/status` (`loading`, `no-mcdu` o `ready`).

### 2. El servidor web de FlightGear (`--httpd=8080`)

FlightGear té un servidor web intern que permet llegir i escriure propietats en format JSON. El programa Python el fa servir per comunicar-se amb l'add-on, a l'adreça `http://localhost:8080/json/mcdu-bridge/...`.

### 3. El programa Python (`mcdu_bridge.py`)

S'executa al teu ordinador i fa de pont:

1. Busca el MCDU per USB (fabricant WinWing, `0x4098`) i el prepara.
2. Cada 0,1 segons llegeix de FlightGear la pantalla exportada.
3. Converteix aquestes dades en una graella de **14 files × 24 columnes**, que és la mida de la pantalla física, i l'envia per USB. Només la redibuixa quan canvia alguna cosa.
4. Llegeix les tecles del MCDU físic i les envia a FlightGear.

Si FlightGear o l'add-on no responen, la pantalla mostra un missatge que explica què passa, i el programa torna a provar-ho automàticament. Si desconnectes el cable USB, també es reconnecta sol.

## Fitxers

| Fitxer | Què fa |
|---|---|
| `mcdu_bridge.py` | Programa principal: connecta el MCDU amb FlightGear. |
| `test_hardware.py` | Prova el MCDU sense FlightGear: pantalla, LED i tecles. |
| `mcdu_hardware.py` | Controlador USB del MCDU: pantalla, LED, brillantor i lectura de tecles. |
| `mcdu_keys.py` | Taula de tecles: número de cada tecla i funció de l'avió que crida. |
| `mcdu_layout.py` | Converteix les dades de FlightGear en la graella de 14 × 24 caràcters. |
| `mcdu_layout_data.py` | Posició de cada element de la pantalla de l'A320, calculada a partir del dibuix original de l'avió. |
| `fgfs_addon/addon-main.nas` | Add-on de FlightGear: exporta la pantalla i executa les tecles. |
| `fgfs_addon/addon-metadata.xml` | Dades de l'add-on que FlightGear necessita per carregar-lo. |
| `requirements.txt` | Paquet de Python necessari (`hidapi`). |

## Instal·lació

1. Descomprimeix el zip, per exemple a `C:\mcdu_bridge`.
2. Obre un terminal en aquesta carpeta i instal·la la dependència:

   ```
   py -m pip install -r requirements.txt
   ```

## Prova del maquinari (sense FlightGear)

1. Tanca **SimAppPro**. Si l'has fet servir, desconnecta i torna a connectar el MCDU.
2. Executa:

   ```
   py test_hardware.py
   ```

3. Comprova que:
   - La pantalla mostra colors, lletra gran i petita i símbols.
   - Els LED s'encenen d'un en un.
   - Cada tecla que prems escriu el seu nom al terminal.

## Configuració de FlightGear

Al llançador de FlightGear, a **Settings > Additional Settings**, afegeix:

```
--httpd=8080
--addon=C:\mcdu_bridge\fgfs_addon
```

La ruta de `--addon` ha de ser la carpeta on hi ha `addon-metadata.xml` i `addon-main.nas`. Per trobar-la:

1. A l'Explorador de fitxers, entra a la carpeta `fgfs_addon`.
2. Copia la ruta de la barra d'adreces i enganxa-la després de `--addon=`.

Vigila que, en descomprimir, Windows sovint crea una carpeta dins d'una altra, per exemple `C:\mcdu_bridge\mcdu_bridge\fgfs_addon`. Si la ruta té espais, posa-la entre cometes: `--addon="C:\la meva carpeta\fgfs_addon"`.

Després, selecciona un avió de la família **A320-family**.

## Ús

1. Inicia FlightGear amb l'A320-family.
2. Amb SimAppPro tancat, executa:

   ```
   py mcdu_bridge.py
   ```

3. Dona corrent elèctric a l'avió. Igual que a l'avió real, el MCDU no funciona sense corrent.

### Opcions

| Opció | Què fa |
|---|---|
| `--side left` / `--side right` | Tria quin MCDU de l'avió controles. Per defecte es dedueix del model de MCDU (capità o primer oficial). |
| `--brightness 180` | Brillantor inicial, de 0 a 255. |
| `--port 8080` | Port del servidor web de FlightGear, si n'has posat un altre a `--httpd`. |
| `--host 127.0.0.1` | Ordinador on s'executa FlightGear, si no és el mateix. |
| `--dump` | Escriu al terminal les dades de pantalla que arriben de FlightGear. Serveix per trobar errors. |

### Tecles especials

- **BRT** i **DIM** canvien la brillantor del MCDU físic.
- Si mantens premuda **CLR**, s'esborra tota la línia d'entrada (scratchpad), igual que a l'avió.
- **SEC F-PLN** i les dues tecles sense nom no fan res, perquè l'A320-family no hi té cap funció.

### LED

- **FM1** s'encén si controles el MCDU esquerre, i **FM2** si controles el dret.
- **FAIL** s'encén quan no arriben dades de FlightGear.
- L'avió no exposa la resta de llums, així que es queden apagats.

## Missatges a la pantalla

| Missatge | Què vol dir | Què fer |
|---|---|---|
| `WAITING FOR FLIGHTGEAR` | El programa no pot connectar amb FlightGear. | Comprova que FlightGear estigui obert i que tingui `--httpd=8080`. |
| `ADD-ON NOT LOADED` | FlightGear respon però l'add-on no s'ha carregat. | Revisa la ruta de `--addon`. |
| `A320-FAMILY MCDU NOT FOUND` | L'avió carregat no és l'A320-family. | Carrega un avió de l'A320-family. |
| `LOADING AIRCRAFT` | L'avió encara s'està carregant. | Espera uns segons. |
| Pantalla negra | L'avió està carregat però no té corrent. | Dona corrent a l'avió. |

## Resolució de problemes

| Problema | Solució |
|---|---|
| `MCDU not found` al terminal | Tanca SimAppPro i revisa el cable USB. |
| `Unable to find add-on metadata file` a FlightGear | La ruta de `--addon` no és la carpeta `fgfs_addon`. Mira la secció de configuració. |
| Falta text o símbols, o surten desplaçats | Executa `py mcdu_bridge.py --dump` i obre `http://localhost:8080/json/mcdu-bridge/missing-elements` al navegador. Guarda el número i la sortida del terminal per revisar-ho. |
| Una tecla fa una acció equivocada | Executa `py test_hardware.py` i apunta el número i el nom que surten en prémer-la. |

## Limitacions

- Només funciona amb l'avió **A320-family**.
- La pantalla física és una graella de caràcters, així que els símbols gràfics de l'avió es converteixen en caràcters (`☐`, `←`, `↑`, `*`). Algun text pot quedar lleugerament desplaçat.
- No es pot fer servir alhora que SimAppPro.

## Llicència

GPL-3.0. El protocol USB i els paquets d'inicialització de la pantalla provenen del projecte [XSchenFly](https://github.com/schenlap/XSchenFly), de memo5.
