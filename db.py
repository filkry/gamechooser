import sqlite3
import datetime
import csv
from datetime import date

def create_schema(conn):
    with conn:
        conn.execute('''CREATE TABLE game
            (id integer primary key autoincrement,
            title text, release_year integer, linux integer,
            play_more integer, couch integer, passes integer,
            via text, eternal integer)''')

        conn.execute('''CREATE TABLE own
            (game_id integer, storefront text,
            foreign key (game_id) references game(id))''') 

        conn.execute('''CREATE TABLE sessions
            (game_id integer, started datetime,
            outcome text,
            foreign key (game_id) references game(id))''')


def import_gdoc_sessions(conn, rows):
    with conn:
        skipped = 0
        for title, start_date, status, keep, notes in rows:
            if title == 'Title' or len(title) == 0:
                continue
            gid = None 
            for game_id in conn.execute("""SELECT id FROM game WHERE title = ?""", (title,)):
                gid = game_id[0]
                break

            if gid is None:
                skipped += 1
                gid = add_game(conn, title, None, None, None, None,
                        0, None, False, [])

            # munge
            status = None if status == '' else status
            if len(start_date) == 0:
                start_date = None
            else:
                day, month, year = start_date.split('/')
                start_date = datetime.datetime(int(year), int(month), int(day))

            conn.execute("""INSERT INTO
                sessions(game_id, started, outcome)
                VALUES (?, ?, ?)""", (gid, start_date, status))

    print("Added %i games due to mismatched titles." % skipped)


def add_game(conn, title, release_year, linux, play_more, couch, passes, via, eternal, storefronts):
    c = conn.cursor()

    c.execute('''insert into
            game(title, release_year, linux, play_more,
                couch, passes, via, eternal)
            values(?, ?, ?, ?, ?, ?, ?, ?)''',
            (title, release_year, linux, play_more,
                couch, passes, via, eternal))
    game_id = c.lastrowid
    assert(game_id != None)

    for sf in storefronts:
        if sf == '':
            continue
        c.execute('''insert into
            own(game_id, storefront) values(?, ?)''',
            (game_id, sf))

    conn.commit()
    return game_id

def import_gdoc_games(conn, rows):
    for title, release_year, linux, play_more, owned_on, couch, passes, via in rows:
        if title == 'title' or title == '':
            continue

        # munge data
        release_year = None if release_year == '' else int(release_year)
        linux = linux == 1 or linux == '1'
        play_more = play_more == 1 or play_more == '1'
        couch = couch == 1 or couch == '1'
        passes = 0 if passes == '' or passes == 'eternal' else int(passes)
        eternal = 1 if passes == 'eternal' else 0

        add_game(conn, title, release_year, linux, play_more, couch, passes, via, eternal, owned_on.split(','))


def dump_csvs(conn, fn_prefix):
    with conn:
        with open("%s_game.csv" % fn_prefix, 'w') as game:
            writer = csv.writer(game)
            writer.writerow(['id', 'title', 'release_year', 'linux',
                'play_more', 'couch', 'passes', 'via',
                'eternal'])
            for row in conn.execute('SELECT * FROM game'):
                writer.writerow(row)

        with open("%s_own.csv" % fn_prefix, 'w') as own:
            writer = csv.writer(own)
            writer.writerow(['game_id', 'storefront'])
            for row in conn.execute('SELECT * FROM own'):
                writer.writerow(row)

        with open("%s_session.csv" % fn_prefix, 'w') as session:
            writer = csv.writer(session)
            writer.writerow(['game_id', 'started', 'outcome'])
            for row in conn.execute('SELECT * FROM sessions'):
                writer.writerow(row)

def load_csvs(conn, fn_prefix):
    with conn:
        with open("%s_game.csv" % fn_prefix, 'r') as game:
            reader = csv.reader(game)
            for i, row in enumerate(reader):
                if i == 0: # skip title line
                    continue
                conn.execute('''insert into game(id, title, release_year,
                    linux, play_more, couch, passes, via, eternal)
                    values (?, ?, ?, ?, ?, ?, ?, ?, ?)''', row)
                    
        with open("%s_own.csv" % fn_prefix, 'r') as own:
            reader = csv.reader(own)
            for i, row in enumerate(reader):
                if i == 0: # skip title line
                    continue
                conn.execute('''insert into own(game_id, storefront)
                    values (?, ?)''', row)

        with open("%s_session.csv" % fn_prefix, 'r') as session:
            reader = csv.reader(session)
            for i, row in enumerate(reader):
                if i == 0: # skip title line
                    continue
                conn.execute('''insert into sessions(game_id, started,
                    outcome)
                    values (?, ?, ?)''', row)

def select_random_games(conn, n = 1, before_this_year = None, linux = None,
        play_more = True, couch = None, max_passes = 2, owned=True):
    with conn:
        # Construct query
        conditions = []

        if before_this_year is True:
            conditions.append('release_year < ' + str(date.today().year))
        elif before_this_year is False:
            conditions.append('release_year == ' + str(date.today().year))

        if linux == True:
            conditions.append('linux == 1')
        elif linux == False:
            conditions.append('linux == 0')

        if play_more == True:
            conditions.append('play_more == 1')
        elif play_more == False:
            conditions.append('play_more == 0')

        if couch == True:
            conditions.append('couch == 1')
        elif couch == False:
            conditions.append('couch == 0')

        conditions.append('passes <= ' + str(max_passes))

        if owned:
            select = 'SELECT * FROM own JOIN game ON own.game_id=game.id'
        else:
            select = 'SELECT * FROM game'

        query = select + ' WHERE ' + ' AND '.join(conditions) + ' ORDER BY RANDOM() LIMIT ' + str(n)
        return list(conn.execute(query))

def show_sessions(conn, active = True, status = None,
        session_year = date.today().year):
    with conn:
        conditions = []

        if active is True:
            conditions.append('outcome is null OR outcome == ""')
        elif active is False:
            conditions.append('outcome is not null AND outcome != ""')

        if status is not None:
            conditions.append('outcome == ' + status)

        if session_year is not None:
            conditions.append('started BETWEEN "%i-01-01" AND "%i-12-31"' % (session_year, session_year))

        query = '''SELECT game_id, title, started, outcome FROM 
            sessions AS s JOIN game AS g ON s.game_id=g.id WHERE ''' + ' AND '.join(conditions)

        return list(conn.execute(query))


