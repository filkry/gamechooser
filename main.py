import argparse
import csv
import sqlite3
import db
from collections import defaultdict

def import_csvs(args):
    conn = sqlite3.connect(':memory:')
    db.create_schema(conn)

    with open(args.file_name, 'r') as csvfile:
        db.import_gdoc_games(conn, csv.reader(csvfile))

    if args.sessions:
        with open(args.sessions, 'r') as csvfile:
            db.import_gdoc_sessions(conn, csv.reader(csvfile))

    db.dump_csvs(conn, 'temp')
    
if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser(description="Manage a library of video games.")
    subparsers = arg_parser.add_subparsers()

    # Parameteres for listing sessions
    sessions_parser = subparsers.add_parser('sessions', help='List sessions of games.')

    # Parameters for selecting a game to play
    select_parser = subparsers.add_parser('select', help='Select a random game to play.')

    # Parameters for importing games from Google Docs
    import_parser = subparsers.add_parser('import', help='Import games from google docs.')
    import_parser.add_argument('file_name', help='Path to file with the main list of games from Google docs.')
    import_parser.add_argument('--sessions', action='store', help='Path to file with list of sessions from Google docs.')
    import_parser.set_defaults(func=import_csvs)

    args = arg_parser.parse_args()
    args.func(args)
