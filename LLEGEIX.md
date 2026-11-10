# Pont WinWing MCDU per a FlightGear (A320-family)

Connecta el MCDU físic amb l'A320-family: la pantalla mostra el MCDU de l'avió i les tecles hi envien les ordres.

Cal FlightGear 2024.1.1 o posterior, Windows i Python 3.

## 1. Instal·la

1. Descomprimeix aquesta carpeta, per exemple a `C:\mcdu_bridge`.
2. Obre un terminal en aquesta carpeta i executa:

   ```
   py -m pip install -r requirements.txt
   ```

## 2. Prova el maquinari, sense FlightGear

1. Tanca SimAppPro. Si l'has fet servir, desconnecta i torna a connectar el MCDU.
2. Executa:

   ```
   py test_hardware.py
   ```

3. Comprova que veus colors i símbols a la pantalla, que els LED s'encenen d'un en un i que cada tecla escriu el seu nom al terminal.

## 3. Configura FlightGear

Al llançador de FlightGear, escriu això a **Settings > Additional Settings**:

```
--httpd=8080
--addon=C:\mcdu_bridge\fgfs_addon
```

Selecciona un avió de la família **A320-family**.

## 4. Fes-lo servir

1. Inicia FlightGear.
2. Amb SimAppPro tancat, executa:

   ```
   py mcdu_bridge.py
   ```

3. Dona corrent a l'avió. El MCDU necessita corrent elèctric, igual que a l'avió real.

Opcions:

- `--side left` o `--side right`: tria quin MCDU de l'avió controles. Per defecte es dedueix del dispositiu USB.
- `--brightness 180`: brillantor inicial, de 0 a 255.
- `--dump`: escriu al terminal les dades que arriben de FlightGear.

Les tecles BRT i DIM canvien la brillantor del maquinari. SEC F-PLN i les dues tecles sense nom no fan res, perquè aquest avió no hi té cap funció assignada.

## Si alguna cosa falla

| El que veus | Què fer |
|---|---|
| `MCDU not found` | Tanca SimAppPro i revisa el cable USB. |
| `WAITING FOR FLIGHTGEAR` | Comprova `--httpd=8080` i que FlightGear estigui obert. |
| `ADD-ON NOT LOADED` | Revisa la ruta de `--addon`. |
| `A320-FAMILY MCDU NOT FOUND` | Comprova que l'avió sigui l'A320-family. |
| Pantalla negra amb l'avió carregat | Dona corrent a l'avió. |
| Falta text o símbols | Obre `http://localhost:8080/json/mcdu-bridge/missing-elements` i envia el valor, amb la sortida de `--dump`. |

## Llicència

GPL-3.0. El protocol USB i els paquets d'inicialització provenen de XSchenFly, de memo5.
