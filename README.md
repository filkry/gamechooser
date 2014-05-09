gamechooser
===========

A little script I use to pick video games to play from my fast-growing interest list. Requires Python 3.

usage: main.py [-h] [-d DATA] {sessions,finish,start,select,import} ...

Manage a library of video games.


positional arguments:
  {sessions,finish,start,select,import}
    sessions            List sessions of games.
    finish              Finish a game session.
    start               Start a session.
    select              Select a random game to play.
    import              Import games from google docs.

optional arguments:
  -h, --help            show this help message and exit
  -d DATA, --data DATA  location for storing data files
