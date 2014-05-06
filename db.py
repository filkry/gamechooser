import sqlite3

def create_schema(conn):
    c = conn.cursor()

    c.execute('''CREATE TABLE games
        (title text, release_year integer, linux integer,
        play_more integer, couch integer, passes integer,
        via text)''')


