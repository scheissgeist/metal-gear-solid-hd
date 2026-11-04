```
 __  __ ___ _____ _   _       ___ ___   _   ___     ___  ___  _    ___ ___
|  \/  | __|_   _/_\ | |     / __| __| /_\ | _ \   / __|/ _ \| |  |_ _|   \
| |\/| | _|  | |/ _ \| |__  | (_ | _| / _ \|   /   \__ \ (_) | |__ | || |) |
|_|  |_|___| |_/_/ \_\____|  \___|___/_/ \_\_|_\   |___/\___/|____|___|___/
```

## Install (3 steps)

1. **Close METAL GEAR SOLID**, then download the zip from [Releases](../../releases/latest).
2. **Unzip it into the game folder**: in Steam, right-click METAL GEAR SOLID > Manage > Browse local files. Put everything next to `METAL GEAR SOLID.exe`. Back up any existing files you are replacing, then say yes to replace.
3. **Double-click `INSTALL.bat`**, wait for "installed", then play from Steam.

## Keys

| Key | Does | Starts |
|-----|------|--------|
| F8 | New lighting / original lighting | On |
| F7 | HD textures / original textures | On |
| F6 | Image effects (sharpen, bloom, grade) | Off |

## What it does

- HD textures for the whole game, made from the original art.
- HD weapon and item icons in the menus and the HUD.
- Real, motivated lighting. The HUD, text and radar stay as the game draws them. The lighting is experimental: F8 turns it off.
- No ReShade needed. Saves are not touched.

## Uninstall

1. **Close METAL GEAR SOLID.**
2. **Double-click `UNINSTALL.bat`** and wait for confirmation that the stock game files are restored. Do this before deleting the mod folders. If it reports an error, use Steam > Properties > Installed Files > Verify integrity of game files to restore the game data before continuing.
3. **Delete these two folders from the game folder:**

   ```text
   MGSModernHUD
   MGSModernTextures
   ```

4. **Delete these files from the game folder:**

   ```text
   d3d11.dll
   dinput8.dll
   INSTALL.bat
   install.ps1
   LICENSES.txt
   MGSM2Fix-README.md
   MGSM2Fix.ini
   MGSM2Fix32.asi
   MGSM2Fix64.asi
   MGSModernEmitters.txt
   MGSModernLights.txt
   MGSModernStages.txt
   MGSModernTextureIDs.txt
   README.txt
   UNINSTALL.bat
   uninstall.ps1
   ```

This list covers the files supplied by this release. If any were present before installing, restore your backed-up versions instead of deleting files needed by another mod.

After the stock files have been restored, you can also remove the installer's backup file `windata\alldata.psb.m.stock`. Keep the `windata` folder, the game executable and your saves.

## Problems

- **"not the stock files this pack was built for"**: your game data is already modified (another mod or a game update). Verify integrity of game files in Steam, then run `INSTALL.bat` again.
- **Image effects on at start**: `MGSM2Fix.ini` > `[ImageFx]` > `StartOn = true`.
- Steam Deck / Linux: not tested yet.

## Credits

Built on [MGSM2Fix](https://github.com/nuggslet/MGSM2Fix) by nuggslet and Ultimate ASI Loader by ThirteenAG (both MIT, see `LICENSES.txt`). METAL GEAR SOLID is (c) KONAMI; this is an unofficial fan mod and needs your own copy of the game.
