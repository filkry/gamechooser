import sqlite3
import datetime
import csv

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





