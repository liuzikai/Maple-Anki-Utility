Maple Anki Utility for Vocabulary Learners
==========================================

This tool was initially developed to help me make Anki flashcards from the Kindle Vocabulary Builder. 
Tools like [https://fluentcards.com/kindle](https://fluentcards.com/kindle) can batch convert the
vocabulary list, but I wanted something that can record which words I have processed and which I haven't.

With this tool, just plug in your Kindle, and you get a vocabulary list to process. 
The word, the example sentence, and the citation are automatically filled for you.
Combined with the automation built in the [Maple Anki Template](https://github.com/liuzikai/Maple-Anki-Template),
you can quickly make flashcards that suit your taste.
One you process a word, the tool marks it as learned, and it will no longer appear at your next import.

As time goes, more functionalities are added to it, including import from CSV and Things 3 todo lists, a side-by-side
automatic web query view for online dictionary, etc.

![Maple Anki Utility](resource/utility.png)

* Import from Kindle Vocabulary Builder, CSV, Thing 3 List, or manually create new cards.
* Built-in audio generator using macOS's native text-to-speech.
* Side-by-side web browser to automatically query web directory, image search, and translation, with auto pre-loading.
* Combined with [Maple Anki Template](https://github.com/liuzikai/Maple-Anki-Template), providing auto parts of speech 
  highlighting, auto keyword highlight, etc.

![Maple Anki Utility](resource/template.png)

## Getting Started

**This application only supports macOS for now** (it uses macOS built-in features such as text-to-speech and
AppleScript).
The main part of it is in PyQt6 and should be portable. Contributions are welcomed!

Download the pre-built application in the release page.

=> [User Manual](resource/user-manual.md). You may want to at least get familiar basic workflow of the tool.

If you want to run the tool manually in Python, download the repo and run `pip3 install -r requirements.txt`.
In addition, you will need the following tools:

* `lame` (run `brew install lame`, used for converting audio files)
* `tar` (macOS built-in, used by data_source to backup file)
* `say` (macOS built-in, used for pronunciation)
* `osascript` (macOS built-in, used to connect Things 3)

## License

The code is released under the MIT License.

The icon uses Maple by Adrien Coquet from [Noun Project](https://thenounproject.com/browse/icons/term/maple/) (CCBY3.0).
