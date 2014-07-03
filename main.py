import argparse
import csv
import sqlite3
import db
import os
from datetime import date
import datetime


def instantiate_db(load_csvs = False):
    conn = sqlite3.connect(':memory:')
    conn.row_factory = sqlite3.Row
    db.create_schema(conn)
    path = os.path.expanduser(args.data)

    if load_csvs:
        db.load_csvs(conn, path)

    return conn, path

def dict_from_row(row):
    return dict(zip(row.keys(), row))

def format_games(conn, game_records, header = True, nums = True,
        show_linux = False, show_couch = False, show_play = False,
        show_via = True, show_platforms = True, show_year = False):

    output = []

    fmt = lambda g, ps: format_game(g, ps, show_linux = show_linux,
            show_couch = show_couch, show_play = show_play,
            show_via = show_via, show_platforms = show_platforms,
            show_year = show_year)

    if header:
        title = fmt({'title': 'title', 'release_year': 'year', 'linux': 'linux', 'couch': 'couch',
            'play_more': 'more', 'passes': 'passes', 'via': 'via'}, ['storefronts'])
        output.append('\033[1m' + '   ' + title + '\033[0m')

    for i, game in enumerate(game_records):
        platforms = db.storefronts(conn, game['id'])
        output.append('{0:<3.3}'.format(str(i+1)) + fmt(game, platforms))

    return '\n'.join(output)


def format_game(game_record, platforms, show_linux = False, show_couch = False,
        show_play = False, show_via = True, show_platforms = True,
        show_year = False):
    sections = ['{title:<40.40}']

    game_dict = game_record if game_record['title'] == 'title' else dict_from_row(game_record) 

    if show_year:
        sections.append('{release_year:>4}')

    if show_linux:
        sections.append('{linux:>5}')

    if show_couch:
        sections.append('{couch:>5}')

    if show_play:
        sections.append('{play_more:>4}')

    # Decided to hide passing information
    #sections.append('{passes:>6}')

    if show_via:
        sections.append('{via:<20.20}')
        if game_dict['via'] is None:
            game_dict['via'] = ''

    format_str = ' '.join(sections)
    output = format_str.format(**game_dict)

    if show_platforms:
        output += "  {0:<20.20}".format(', '.join(platforms))

    return output

def handle_import(args):
    conn, path =  instantiate_db(False)

    # TODO: confirmation step? This wipes out existing data
    with open(args.file_name, 'r') as csvfile:
        db.import_gdoc_games(conn, csv.reader(csvfile))

    if args.sessions:
        with open(args.sessions, 'r') as csvfile:
            db.import_gdoc_sessions(conn, csv.reader(csvfile))

    db.dump_csvs(conn, path)

def handle_add(args):
    conn, path = instantiate_db(True)

    title = input("Game title: ")
    year = input("Release year: ")
    year = int(year) if len(year) > 0 else None
    linux = True if input("Linux (y/n): ").lower() == 'y' else False
    couch = True if input("Couch playable (y/n): ").lower() == 'y' else False
    via = input("Via: ")
    owned_on = input("Owned platforms (comma separated): ").split(',')

    db.add_game(conn, title, year, linux, True, couch, 0, via, False, owned_on)

    db.dump_csvs(conn, path)

def handle_starts(args):
    conn, path = instantiate_db(True)

    games = db.search_game(conn, args.title)[:5]

    print('Which game?')
    print(format_games(conn, games, header = True))

    which_game = input('Input number, or q to abort: ')
    if which_game.lower() == 'q':
        return

    gid, title = (games[int(which_game) - 1]['id'],
                  games[int(which_game) - 1]['title'])
    db.create_session(conn, gid)

    print('Created session for %s' % (title))

    db.dump_csvs(conn, path)

def handle_own(args):
    conn, path = instantiate_db(True)

    games = db.search_game(conn, args.title)[:5]

    print('Which game now owned?')
    print(format_games(conn, games, header = True))

    which_game = input('Input number, or q to abort: ')
    if which_game.lower() == 'q':
        return

    gid, title = (games[int(which_game) - 1]['id'],
                  games[int(which_game) - 1]['title'])

    plat = input('Name of platformed purchased on: ')
    db.add_ownership(conn, gid, plat)

    print('Added %s platform for %s' % (plat, title))

    db.dump_csvs(conn, path)

def handle_search(args):
    conn, path = instantiate_db(True)

    games = db.search_game(conn, args.title)[:5]

    print(format_games(conn, games, header = True, nums = True,
        show_linux = True, show_couch = True, 
        show_via = True, show_platforms = True, show_year = True))

def handle_select(args):
    conn, path = instantiate_db(True)

    passed_ids = []
    while True:
        games = db.select_random_games(conn, n = args.n, before_this_year = True if args.old else None,
                linux = True if args.linux else None, couch = True if args.couch else None,
                owned = False if args.buy else True, max_passes = args.max_passes,
                exclude_ids = passed_ids)

        title = format_game({'title': 'title', 'release_year': 'year', 'linux': 'linux',
            'couch': 'couch', 'play_more': 'more', 'passes': 'passes', 'via': 'via'}, ['storefronts'])
        print('\033[1m' + '   ' + title + '\033[0m')

        for i, game in enumerate(games):
            platforms = db.storefronts(conn, game['id'])
            print('{0:<3.3}'.format(str(i+1)) + format_game(game, platforms))

        # If we're just displaying a selection, finish here
        if not args.pick:
            break

        print('\nChoose a game to create a new active session for. Input 0 to pass on all games. Q to abort.')
        selection = input("Selection: ")

        if selection == 'q' or selection == 'Q':
            break

        selection = int(selection)

        if selection == 0:
            # Increment the pass counter on each game
            for game in games:
                # Don't propose game again
                passed_ids.append(game['id'])
        
                # If the game is not out yet, don't increment
                if game['release_year'] != None and game['release_year'] != '' and int(game['release_year']) == date.today().year:
                    freebie = input('%s was released this year. Has it been released? Y/N: ' % game['title'])
                    if freebie == 'N' or freebie == 'n':
                        continue
                new_passes = db.inc_pass(conn, game['id'])

                # Delay next possible proposal according to passes
                if new_passes == 1:
                    db.set_next_valid_date(conn, game['id'],
                        date.today() + datetime.timedelta(days = 7))
                elif new_passes == 2:
                    db.set_next_valid_date(conn, game['id'],
                        date.today() + datetime.timedelta(days = 30))
                else:
                    db.set_next_valid_date(conn, game['id'],
                        date.today() + datetime.timedelta(days = 90))

                # If max passes, give option to make game eternal
                if new_passes > args.max_passes:
                    eternal = input('You have passed on %s enough times that it will stop being suggested. You can avoid this by making this game "eternal". Y/N: ' % game['title'])
                    if eternal == 'Y' or eternal == 'y':
                        db.make_eternal(conn, game['id'])

        else:
            # Create an active session
            game = games[selection - 1]
            db.create_session(conn, game['id'])
            print('Created a new session of %s.' % game['title'])
            break

        print('\n')

    # So scared of commitment
    db.dump_csvs(conn, path)

def format_session(session_record, show_started= True, show_outcome = True):
    sections = ['{title:<40.40}']

    if show_started:
        sections.append('{started:>10.10}')

    if show_outcome:
        sections.append('{outcome:>10.10}')

    output = '  '.join(sections).format(**session_record)

    return output

def print_sessions(conn, session_records):
    title = format_session({'title': 'title', 'started': 'started', 'outcome': 'outcome'})
    print('\033[1m' + '   ' + title + '\033[0m')

    for i, s in enumerate(session_records):
        print('{0:<3.3}'.format(str(i+1)) + format_session(s))


def handle_sessions(args):
    db.load_csvs(conn, path)

    sessions = db.show_sessions(conn, active = not args.inactive,
            session_year = None if args.year == 0 else int(args.year),
            status = 'stuck' if args.stuck else None)

    print_sessions(conn, sessions)

def handle_finish(conn):
    db.load_csvs(conn, path)

    sessions = db.show_sessions(conn, active = True)
    print_sessions(conn, sessions)

    finish = input('Input a session to finish, or Q to abort: ')
    if finish == 'q' or finish == 'Q':
        return
    finish = int(finish)

    finish_session = sessions[finish - 1]
    status = input('Was %s a transient (t) or sticking (s) experience: ' % finish_session['title'])
    if status == 'q' or status == 'Q':
        return

    status = 'transient' if status == 't' or status == 'T' else 'stuck'

    # TODO: allow delays
    more = input('''How long until %s should be suggested again?
1) any time
2) one month
3) one year
4) done forever
q) abort
Input response: ''' % finish_session['title'])
    if more == 'q' or more == 'Q':
        return

    if int(more) == 2:
        db.set_next_valid_date(conn, finish_session['game_id'],
            date.today() + datetime.timedelta(days = 31))
    elif int(more) == 3:
        db.set_next_valid_date(conn, finish_session['game_id'],
            date.today() + datetime.timedelta(days = 365))
    elif int(more) == 4:
        db.retire_game(conn, finish_session['game_id'])

    db.finish_session(conn, finish_session['game_id'], status)

    db.dump_csvs(conn, path)

    
if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser(description="Manage a library of video games.")
    arg_parser.add_argument('-d', '--data', help='location for storing data files',
            action='store', default='~/SpiderOak Hive/gamechooser/')
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
    finish_parser = subparsers.add_parser('finish', help='Finish a game session.')
    finish_parser.set_defaults(func=handle_finish)

    # Parameters for starting sessions
    starts_parser = subparsers.add_parser('start', help='Start a session.')
    starts_parser.add_argument('title', help='Title of game to start a session for.')
    starts_parser.set_defaults(func=handle_starts)

    # Parameters for searching for games
    search_parser = subparsers.add_parser('search', help='Search for a game.')
    search_parser .add_argument('title', help='Title of game to search for.')
    search_parser .set_defaults(func=handle_search)

    # Parameters for adding ownership of a game
    own_parser = subparsers.add_parser('own', help='Add ownership record for a game.')
    own_parser .add_argument('title', help='Title of game now owned.')
    own_parser .set_defaults(func=handle_own)

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
    select_parser.add_argument('-m', '--max_passes',
            help='Maximum number of times a game can be passed before it is retired.',
            action='store', default=2)
    select_parser.add_argument('-p', '--pick',
            help='Start game picking algorithm after showing selection.',
            action='store_true')
    select_parser.set_defaults(func=handle_select)

    # Parameters for importing games from Google Docs
    import_parser = subparsers.add_parser('import', help='Import games from google docs.')
    import_parser.add_argument('file_name', help='Path to file with the main list of games from Google docs.')
    import_parser.add_argument('--sessions', action='store', help='Path to file with list of sessions from Google docs.')
    import_parser.set_defaults(func=handle_import)

    # Parameters for adding games
    # Punting on this due to CSV backend
    add_parser = subparsers.add_parser('add', help='Add a new game.')
    add_parser.set_defaults(func=handle_add)

    # Parameters for modifying games
    # Punting on this due to CSV backend
    #add_parser = subparser.add_parser('edit', help='Edit a game.')

    args = arg_parser.parse_args()
    args.func(args)
