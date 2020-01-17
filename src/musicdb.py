#!/bin/python3

import sqlite3
import pathlib
import mutagen.id3

import os

class MusicDB:

    def __init__(self, dbpath: pathlib.Path):
        self.dbpath = dbpath
        self.dbconn = sqlite3.connect(str(self.dbpath))
        self.init()

    def __del__(self):
        self.dbconn.close()


    def init(self):
        c = self.dbconn.cursor()
        c.execute('''
        CREATE TABLE IF NOT EXISTS artists 
        (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            name     TEXT UNIQUE ON CONFLICT IGNORE
        )
        ''')
        c.execute('''
        CREATE TABLE IF NOT EXISTS albums
        (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            title    TEXT UNIQUE ON CONFLICT IGNORE,
            cover    BLOB
        )
        ''')
        c.execute('''
        CREATE TABLE IF NOT EXISTS tracks
        (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            tracknum INTEGER,
            title    TEXT,
            album    INTEGER REFERENCES albums(id),
            artist   INTEGER REFERENCES artists(id),
            path     TEXT UNIQUE ON CONFLICT IGNORE
        )
        ''')
        c.execute('''
        CREATE TABLE IF NOT EXISTS trackqueue
        (
            trackid  INTEGER PRIMARY KEY REFERENCES tracks(id)
        )
        ''')
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
                ) SELECT ?, ?, albums.id, artists.id, ? FROM albums, artists
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


if __name__=='__main__':
    
    db = MusicDB(pathlib.Path('test.db'))

    db.resetdb()
    db.scandir(pathlib.Path('/home/gmartell/Music/bak'))

    for i in db.getalbums():
        print(i[1])



