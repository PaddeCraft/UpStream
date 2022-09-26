# UpStream

## Overview

Upstream is a command-line utility to explore files via a web browser.  
It should be very simple to use.

## Disclaimer

This is still work-in-progress. If you experiance a bug or have a feature-request, open an issue.

## Requirements

 - Python 3
 - Pip(x)

## Installation

```shell
# Latest release
python3 -m pip install https://api.github.com/repos/PaddeCraft/UpStream/zipball

# Developement version
python3 -m pip install git+https://github.com/PaddeCraft/UpStream.git
```

## Usage

```shell
python3 -m upstream --port INT          = 55555
                    --directory PATH    = .
                    --host              = 0.0.0.0
                    --foldersizedisplay = false     # Don´t use for big directories,
                                                    # because it needs to read the size
                                                    # of every single file.
```