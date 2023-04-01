#!/bin/bash
pyinstaller --windowed -noconsole --add-binary="$(where lame):." -n "Maple Vocab Utility" --icon resource/icon.icns maple_vocab_utility.py