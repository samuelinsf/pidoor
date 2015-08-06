#!/usr/bin/python

import lazytable
import sys
import os.path
import optparse

def dump(t):
    all = list(t.get({}))
    print '      card     door       is_allowed    note'
    print '====================================================='
    for c in all:
        print '%12d %12s %4d            %s' % (c['card'], c['door'], c['is_allowed'], c['note'])


def main():
    path = '/data'

    usage = """%prog [--data-dir PATH] [card door is_allowed note]"""
    parser = optparse.OptionParser(usage)
    parser.add_option("--data-dir", dest="data_dir", default=path,
                      action="store", help="path to dir with logs and carddb")
    (options, args) = parser.parse_args()

    card_db = os.path.join(options.data_dir, 'cards_db.sqlite')
    t = lazytable.open(card_db, 'cards')

    if len(args) == 4:
        # card door is_allowed note
        (card, door, is_allowed, note) = args
        new = {'card':int(card), 'door':door, 'is_allowed':int(is_allowed), 'note':note}
        t.upsert({'card':card, 'door':door}, new)
    else:
        dump(t)
        parser.print_usage()
        exit()

if __name__ == '__main__':
    main()
