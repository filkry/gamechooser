import argparse
import csv
from collections import defaultdict

def import_csvs_maindf_helper(file_name):
    vals = defaultdict(list)
    with open(file_name, 'r') as csvfile:
        reader = csv.reader(csvfile)
        rows = list(reader)[1:]

        # pre-iterate data to find all platforms
        owned_on = 4
        sfs = list(set([sf for row in rows 
                      for sf in row[owned_on].split(',')
                      if sf != '']))

        for title, release_year, linux, play_more, owned_on, couch, passes, via in rows:
            vals['title'].append(title)
            vals['release_year'].append(None if release_year == '' else int(release_year))
            vals['linux'].append(linux == 1)
            vals['play_more'].append(play_more == 1)
            vals['couch'].append(couch == 1)
            vals['passes'].append(0 if passes == '' or passes == 'eternal' else int(passes))
            vals['eternal'].append(passes == 'eternal')
            vals['via'].append(via)

            # storefronts are a special case, need to break up list
            for sf in sfs: 
                sfp = 'owned_%s' % sf
                vals[sfp].append(sf in owned_on)

    testlen = lambda x: len(x) == len(vals['title'])
    assert(all(map(testlen, vals.values())))
    
    return pd.DataFrame.from_dict(vals)

#def import_csvs_sessiondf_helper(session_file):

def import_csvs(args):
    main_df = import_csvs_maindf_helper(args.file_name)
    if args.sessions:

    
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
