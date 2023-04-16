#!/bin/bash
rm -rf "dist/Maple Vocab Utility"
create-dmg \
  --volname "Maple Vocab Utility Installer" \
  --window-pos 200 120 \
  --window-size 600 400 \
  --icon-size 100 \
  --icon "Maple Vocab Utility.app" 150 150 \
  --hide-extension "Maple Vocab Utility.app" \
  --app-drop-link 450 150 \
  "Maple-Vocab-Utility-Installer.dmg" \
  "dist/"