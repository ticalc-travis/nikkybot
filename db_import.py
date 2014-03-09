#!/usr/bin/env python2

# Quick & dirty script/module to copy data from the old markov.py
# and DBM files to the PostgreSQL DB (it's much faster than retraining
# everything from scratch again)

import sys
import psycopg2
import cPickle

import nikkyai
import markovmixai

def do_import(name, date):
    cn = psycopg2.connect('dbname=markovmix user=markovmix')
    c = cn.cursor()

    for o in (2, 3, 4, 5):
        if name == 'nikky':
            m = nikkyai.markovs[o]
        else:
            m = markovmixai.markovs[name, o]
        for d, ts in ((m.word_forward, 'wf'),
                    (m.word_backward, 'wb'),
                    (m.chain_forward, 'cf'),
                    (m.chain_backward, 'cb')):
            c.execute('create table if not exists "{}.{}.{}" (key varchar primary key, value bytea)'.format(name, o, ts))
            c.execute('delete from "{}.{}.{}"'.format(name, o, ts))
            n = len(d.keys())
            sys.stdout.write('\n\n{}.{}.{}\n'.format(name, o, ts))
            for i, k in enumerate(d.keys()):
                sys.stdout.write('{}/{}          \r'.format(i+1, n))
                sys.stdout.flush()
                key = repr(k)
                value = psycopg2.Binary(cPickle.dumps(d[k], protocol=2))
                c.execute('insert into "{}.{}.{}" values (%s, %s)'.format(name, o, ts), (key, value))
                
            c.execute('create table if not exists ".last-updated" (name varchar primary key, updated timestamp default now())')
            c.execute('update ".last-updated" set updated=%s where name=%s',
                    (date, '{}.{}'.format(name, o)))
            if not c.rowcount:
                c.execute('insert into ".last-updated" values (%s, %s)',
                    ('{}.{}'.format(name, o), date))
            cn.commit()

    sys.stdout.write('\n\n')
    
if __name__ == '__main__':
    do_import('bb010g', '2013-12-28')
    do_import('brandonw', '2014-03-01')
    do_import('calebh', '2013-12-28')
    do_import('chronomex', '2014-03-01')
    do_import('comic', '2014-03-03')
    do_import('cricket_b', '2014-03-01')
    do_import('cvsoft-d', '2013-12-28')
    do_import('debrouxl', '2013-12-28')
    do_import('e-j', '2014-03-01')
    do_import('glk', '2014-03-01')
    do_import('joeyoung', '2014-03-03')
    do_import('jonimus', '2014-03-03')
    do_import('juju', '2014-01-07')
    do_import('kerm', '2014-03-01')
    do_import('kevin_o', '2014-03-01')
    do_import('merth', '2014-03-01')
    do_import('michael_v', '2014-03-01')
    do_import('netham45', '2014-03-01')
    do_import('nikky', '2014-03-05')
    do_import('randomist', '2014-03-01')
    do_import('sir_lewk', '2014-03-01')
    do_import('tev', '2014-03-01')

