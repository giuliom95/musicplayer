#!/bin/python3

import sqlite3
import pathlib
import mutagen.id3

import os

class MusicDB:

    def __init__(self, dbpath: pathlib.Path):
        self.dbconn = sqlite3.connect(str(dbpath))

    def __del__(self):
        self.dbconn.close()

    def initnew(self):
        c = self.dbconn.cursor()
        c.execute('DROP TABLE IF EXISTS artists')
        c.execute('''
        CREATE TABLE artists
        (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            name     TEXT UNIQUE ON CONFLICT IGNORE
        )
        ''')
        c.execute('DROP TABLE IF EXISTS albums')
        c.execute('''
        CREATE TABLE albums
        (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            title    TEXT UNIQUE ON CONFLICT IGNORE,
            cover    BLOB
        )
        ''')
        c.execute('DROP TABLE IF EXISTS tracks')
        c.execute('''
        CREATE TABLE tracks
        (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            tracknum INTEGER,
            title    TEXT,
            album    INTEGER REFERENCES albums(id),
            artist   INTEGER REFERENCES artists(id),
            path     TEXT UNIQUE ON CONFLICT IGNORE
        )
        ''')
        self.dbconn.commit()
        c.close()


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


    def db_getalbums(self):
        c = self.dbconn.cursor()
        c.close()



if __name__=='__main__':
    
    db = MusicDB(pathlib.Path('test.db'))

    db.initnew()
    db.scandir(pathlib.Path('/home/gmartell/Music/bak'))



