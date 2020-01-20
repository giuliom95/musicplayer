#!/bin/python3

import sqlite3
import pathlib
import mutagen.id3
import random

import os

class MusicDB:
    SHUFFLEALLNAME = 'Shuffle all'

    def __init__(self, dbpath: pathlib.Path, reset=False):
        self.dbpath = dbpath
        self.dbconn = sqlite3.connect(str(self.dbpath))
        if reset: self.resetdb()
        else: self.init()

    def __del__(self):
        self.dbconn.close()

    def init(self):
        c = self.dbconn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS artists 
            (
                name     TEXT UNIQUE ON CONFLICT IGNORE
            )
        ''')
        c.execute('''
            CREATE TABLE IF NOT EXISTS albums
            (
                title    TEXT UNIQUE ON CONFLICT IGNORE,
                cover    BLOB
            )
        ''')
        c.execute('''
            CREATE TABLE IF NOT EXISTS tracks
            (
                tracknum INTEGER,
                title    TEXT,
                album    INTEGER REFERENCES albums(rowid),
                artist   INTEGER REFERENCES artists(rowid),
                path     TEXT UNIQUE ON CONFLICT IGNORE
            )
        ''')
        c.execute('''
            CREATE TABLE IF NOT EXISTS playqueues
            (
                name         TEXT
            )
        ''')
        c.execute('''
            CREATE TABLE IF NOT EXISTS playqueues2tracks
            (
                playqueue INTEGER REFERENCES playqueues(rowid),
                position  INTEGER,
                track     INTEGER REFERENCES tracks(rowid),
                PRIMARY KEY (playqueue, position)
            )
        ''')
        try:
            c.execute('''
                ALTER TABLE playqueues
                ADD currenttrack INTEGER REFERENCES playqueues2tracks(position)
            ''')
        except sqlite3.OperationalError:
            pass
        self.dbconn.commit()
        c.close()


    def resetdb(self):
        self.dbconn.close()
        self.dbpath.unlink()
        self.__init__(self.dbpath)


    def scandir(self, path: pathlib.Path):
        c = self.dbconn.cursor()
        for f in path.iterdir():
            fname = str(f)
            if f.is_dir():
                self.scandir(f)
                continue
            
            try:
                ftags = mutagen.id3.ID3(fname)
            except mutagen.id3.ID3NoHeaderError:
                print(f'WARNING: No ID3 header found in "{fname}". Probably not an MP3. Skipping.')
                continue

            try:
                tracknum = ftags['TRCK'].text[0].split('/')[0]
                album = ftags['TALB'].text[0]
                artist = ftags['TPE1'].text[0]
                title = ftags['TIT2'].text[0]
            except KeyError as e:
                print(f'WARNING: Tag {e} not found in "{fname}". Skipping.')
                continue

            try:
                apictag = [t for t in ftags.keys() if 'APIC' in t][0]
                coverart = ftags[apictag].data
            except IndexError:
                print(f'WARNING: No image found in "{fname}". Skipping.')
                continue
            
            c.execute('INSERT INTO artists (name) VALUES (?)', (artist,))
            c.execute('INSERT INTO albums (title, cover) VALUES (?, ?)', (album, coverart))
            c.execute('''
                INSERT INTO tracks 
                (
                    tracknum, 
                    title, 
                    album, 
                    artist, 
                    path
                ) SELECT ?, ?, albums.rowid, artists.rowid, ? FROM albums, artists
                WHERE albums.title=? AND artists.name=?;
            ''', (tracknum, title, fname, album, artist))
        
        self.dbconn.commit()
        c.close()


    def getalbums(self):
        c = self.dbconn.cursor()
        c.execute('''
            SELECT * FROM albums
            ORDER BY title;
        ''')
        while True:
            row = c.fetchone()
            if row is None: break
            yield row

        c.close()
        return None


    def gettracksnum(self):
        c = self.dbconn.cursor()
        c.execute('''
            SELECT COUNT(rowid) FROM tracks
        ''')
        tracksnum = c.fetchone()[0]
        c.close()
        return tracksnum


    def shuffleall(self):
        c = self.dbconn.cursor()

        # Remove all entries in the old shuffle all queue
        c.execute(
            'SELECT rowid FROM playqueues WHERE name=?',
            (self.SHUFFLEALLNAME,)
        )
        suffleallid = c.fetchone()
        if suffleallid is not None:
            c.execute('''
                DELETE FROM playqueues2tracks
                WHERE playqueue=?
            ''', (suffleallid[0],))
            c.execute('''
                DELETE FROM playqueues
                WHERE rowid=?
            ''', (suffleallid[0],))
        
        # New entry for shuffle all playqueue
        c.execute(
            'INSERT INTO playqueues (name, currenttrack) VALUES (?, ?)',
            (self.SHUFFLEALLNAME, 1)
        )
        suffleallid = c.lastrowid

        tracksnum = self.gettracksnum()

        l = list(range(tracksnum))
        random.shuffle(l)
        l = [(suffleallid, i+1, e+1) for i,e in enumerate(l)]
        
        c.executemany('''
            INSERT INTO playqueues2tracks 
            (playqueue, position, track)
            VALUES(?, ?, ?)
        ''', l)
        self.dbconn.commit()
        c.close()

    def getcurrenttrack(self, playqueue=None):
        if playqueue is None: playqueue = self.SHUFFLEALLNAME
        return self._gettrack(playqueue, 0)

    def getnexttrack(self, playqueue=None):
        if playqueue is None: playqueue = self.SHUFFLEALLNAME
        return self._gettrack(playqueue, 1)

    def _gettrack(self, playqueue, offset):
        c = self.dbconn.cursor()

        c.execute('''
            SELECT tracks.title, artists.name, albums.title, albums.cover, tracks.path
            FROM playqueues, playqueues2tracks, tracks, albums, artists
            WHERE   playqueues.name=?                                    AND
                    playqueues2tracks.position=playqueues.currenttrack+? AND
                    playqueues2tracks.playqueue=playqueues.rowid         AND
                    tracks.rowid=playqueues2tracks.track                 AND
                    artists.rowid=tracks.artist                          AND
                    albums.rowid=tracks.album
        ''', (playqueue, offset))

        values = c.fetchone()
        c.close()
        keys = [
            'title',
            'artist',
            'album',
            'albumcover',
            'path'
        ]
        track = dict(zip(keys, values))
        track['path'] = pathlib.Path(track['path'])
        return track

    def nexttrack(self, playqueue=None):
        c = self.dbconn.cursor()

        if playqueue is None: playqueue = self.SHUFFLEALLNAME

        c.execute('''
            UPDATE playqueues
            SET currenttrack=currenttrack+1
            WHERE name=?
        ''', (playqueue,))

        self.dbconn.commit()
        c.close()


if __name__=='__main__':
    
    db = MusicDB(pathlib.Path('./music.db'), reset=True)
    db.scandir(pathlib.Path('/home/gmartell/Music/bak'))

    #for i in db.getalbums():
    #    print(i[1])

    db.shuffleall()
    db.shuffleall()

    db.getcurrenttrack()
    db.getcurrenttrack()

    db.getnexttrack()
    db.nexttrack()
    db.getcurrenttrack()



