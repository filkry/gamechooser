gamechooser
===========

A little script I use to pick video games to play from my fast-growing interest list. Requires Python 3.

usage: main.py [-h] [-d DATA] {sessions,finish,start,select,import,add} ...

Manage a library of video games.

positional arguments:
  {sessions,finish,start,select,import,add}
    sessions            List sessions of games.
    finish              Finish a game session.
    start               Start a session.
    select              Select a random game to play.
    import              Import games from google docs.
    add                 Add a new game.

optional arguments:
  -h, --help            show this help message and exit
  -d DATA, --data DATA  location for storing data files

Before using, you must create a config file ~/.gamechooser with the following contents:

    [main]
    data_directory = <where to read/store gamechooser database>
