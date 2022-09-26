# Developers guide for UpStream

## Developement requirements

 - Python 3
 - NodeJS
 - Yarn (optional, but recommended)

## Scripts

UpStream provides some scripts to make developement easier. If some scripts do not work, try changing `python3` to `python`. The following commands are written to be used yarn.

 - `yarn css`

Updates the Tailwind CSS and DaisyUI code from main.css.
Please note: This script runs infinitly and regenerates on every file change.

 - `yarn installandrun`

Pip-installs UpStream and runs it in the current direcory.

## Editor setup

Tailwind CSS has a VSCode IntelliSense plugin. For the best experience, you should have it enabled.  
To install the plugin, go to your command palette (Ctrl + P on Windows and Linux, Cmd + P on MacOS) and type `ext install bradlc.vscode-tailwindcss`.