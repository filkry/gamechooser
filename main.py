import argparse
import csv
import sqlite3
import db
import os
from datetime import date

def handle_import(args):
    conn = sqlite3.connect(':memory:')
    db.create_schema(conn)
    path = os.path.expanduser(args.data)

    # TODO: confirmation step? This wipes out existing data
    with open(args.file_name, 'r') as csvfile:
        db.import_gdoc_games(conn, csv.reader(csvfile))

    if args.sessions:
        with open(args.sessions, 'r') as csvfile:
            db.import_gdoc_sessions(conn, csv.reader(csvfile))

    db.dump_csvs(conn, path)

def handle_select(args):
    conn = sqlite3.connect(':memory:')
    db.create_schema(conn)
    path = os.path.expanduser(args.data)
    db.load_csvs(conn, path)

    games = db.select_random_games(conn, n = args.n, before_this_year = True if args.old else None,
            linux = True if args.linux else None, couch = True if args.couch else None,
            owned = False if args.buy else True)
    print(games)

def handle_sessions(args):
    conn = sqlite3.connect(':memory:')
    db.create_schema(conn)
    path = os.path.expanduser(args.data)
    db.load_csvs(conn, path)

    sessions = db.show_sessions(conn,
            active = not args.inactive,
            session_year = None if args.year == 0 else int(args.year),
            status = 'stuck' if args.stuck else None)

    print(sessions)


if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser(description="Manage a library of video games.")
    arg_parser.add_argument('-d', '--data', help='location for storing data files',
            action='store', default='~/Dropbox/gamechooser/')
    subparsers = arg_parser.add_subparsers()

    # Parameteres for listing sessions
    sessions_parser = subparsers.add_parser('sessions', help='List sessions of games.')
    sessions_parser.add_argument('-i', '--inactive', help='Show inactive sessions.',
            action='store_true')
    sessions_parser.add_argument('-y', '--year',
            help='Limit sessions to a specific year. By default, current year. 0 for all years.',
            action='store', default=date.today().year)
    sessions_parser.add_argument('-s', '--stuck',
            help='Show only sessions which "stuck" (made an impression).',
            action='store_true')
        
    sessions_parser.set_defaults(func=handle_sessions)

    # Parameters for finishing sessions
    finishs_parser = subparsers.add_parser('finish', help='Finish a game session.')

    # Parameters for starting sessions
    starts_parser = subparsers.add_parser('start', help='Start a session.')

    # Parameters for selecting a game to play
    select_parser = subparsers.add_parser('select', help='Select a random game to play.')
    select_parser.add_argument('-l', '--linux', help='Only select games available on linux.',
            action='store_true')
    select_parser.add_argument('-c', '--couch',help='Only select games playable on couch.',
            action='store_true')
    select_parser.add_argument('-o', '--old', help='Only select games from before this year.',
            action='store_true')
    select_parser.add_argument('-b', '--buy', help='Include games that are not owned.',
            action='store_true')
    select_parser.add_argument('-n', help='Number of games to select.',
            action='store', default='1')
    select_parser.set_defaults(func=handle_select)

    # Parameters for importing games from Google Docs
    import_parser = subparsers.add_parser('import', help='Import games from google docs.')
    import_parser.add_argument('file_name', help='Path to file with the main list of games from Google docs.')
    import_parser.add_argument('--sessions', action='store', help='Path to file with list of sessions from Google docs.')
    import_parser.set_defaults(func=handle_import)

    # Parameters for adding games
    # Punting on this due to CSV backend
    #add_parser = subparser.add_parser('add', help='Add a new game.')

    # Parameters for modifying games
    # Punting on this due to CSV backend
    #add_parser = subparser.add_parser('edit', help='Edit a game.')

    args = arg_parser.parse_args()
    args.func(args)
