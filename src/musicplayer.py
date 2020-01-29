#!/bin/python3

import PySide2.QtWidgets

import pyaudio

import subprocess
import pathlib
import threading
import time
import wave
import enum
import os
import sys

import musicdb
import gui

CHUNK = 1024

# pyaudio wants unsigned 16bit so silence is not 0 but 7FFF
SILENCE = b'\x7F\xFF'*2*CHUNK

class BufferStatus(enum.Enum):
    EMPTY       = enum.auto()
    FILLING     = enum.auto()
    READY       = enum.auto()
    BEING_READ  = enum.auto()
    EXPIRED     = enum.auto() 


class Buffer():
    def __init__(self, id: int):
        self.path = pathlib.Path(f'./buf{id}.wav')
        self.status = BufferStatus.EMPTY
        self.fillingprocess = None
        self.wave = None
        self.id = id

    def isReadyToBeFilled(self):
        return  self.status == BufferStatus.EMPTY or \
                self.status == BufferStatus.EXPIRED


class Cache():
    def __init__(self):
        self._bufs = [
            Buffer(0),
            Buffer(1)
        ]
        self.curbuf = self._bufs[0]

    def __del__(self):
        for b in self._bufs:
            try:
                b.path.unlink()
            except FileNotFoundError:
                pass

    def cachetrack(self, trackpath: pathlib.Path, slot=None):
        if slot is None:
            slot = 0
            b = self._bufs[slot]
            if not b.isReadyToBeFilled():
                slot = 1
                b = self._bufs[slot]
                if not b.isReadyToBeFilled():
                    raise Exception('No free buffer')
        b = self._bufs[slot]

        try:
            b.path.unlink()
        except FileNotFoundError:
            pass

        b.fillingprocess = subprocess.Popen([
            'ffmpeg',
            '-i', trackpath,
            '-f', 'wav',
            '-ar', '44100',
            '-c:a', 'pcm_s16le', 
            '-y', b.path
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL)

        b.status = BufferStatus.FILLING

        print(f'[INFO] Started caching "{trackpath}" on buffer #{b.id}')

    def upkeep(self):
        for b in self._bufs:
            if b.status == BufferStatus.FILLING:
                if b.fillingprocess.poll() is not None:
                    b.wave = wave.open(str(b.path), 'rb')
                    b.status = BufferStatus.READY
                    print(f'[INFO] Buffer #{b.id} ready')

    def swap(self):
        self.curbuf.status = BufferStatus.EXPIRED
        oldbufid = self.curbuf.id
        newbufid = (oldbufid + 1) % 2
        self.curbuf = self._bufs[newbufid]
        print(f'[INFO] Swapped from buffer #{oldbufid} to #{newbufid}')

    def expireBoth(self):
        for b in self._bufs:
            b.status = BufferStatus.EXPIRED

class MusicPlayer():

    def __init__(self):

        self._pyaudio = pyaudio.PyAudio()
        self._audiostream = self._pyaudio.open(
            format=pyaudio.paInt16,
            channels=2,
            rate=44100,
            output=True
        )

        self._dbpath = pathlib.Path('./music.db')
        self._db = musicdb.MusicDB(self._dbpath)

        self.curtrack = self._db.getcurrenttrack()
        self.nexttrack = self._db.getnexttrack()
        self._nextrequested = False
        self._prevrequested = False

        self.playing = False

        self._cache = Cache()
        self._cache.cachetrack(self.curtrack['path'])
        self._cache.cachetrack(self.nexttrack['path'])
        
        self._gui = gui.MainWindow(self)
        self._gui.show()
        self._gui.setPaused()
        self._gui.setTrackInfo(self.curtrack)

        # DB will be reopened in the playing thread
        self._db = None
        self._thread = threading.Thread(target=self._mainloop)
        self._thread.start()

    def __del__(self):
        self._audiostream.stop_stream()
        self._audiostream.close()
        self._pyaudio.terminate()

    def _mainloop(self):
        self._db = musicdb.MusicDB(self._dbpath)
        while True:
            self._cache.upkeep()

            # Exit if GUI is closed
            if not self._gui.isVisible():
                self._db = None
                break

            if (self.playing is False or
                self._cache.curbuf.wave is None or
                self._cache.curbuf.status != BufferStatus.READY):

                self._audiostream.write(SILENCE)
            else:
                data = self._cache.curbuf.wave.readframes(CHUNK)
                if len(data) > 0:
                    self._audiostream.write(data)
                else:
                    self.requestnext()

            if self._nextrequested:
                self._next()
                self._nextrequested = False

            if self._prevrequested:
                self._prev()
                self._prevrequested = False
        

    def playpause(self):
        if self.playing:
            self._gui.setPaused()
            self.playing = False
        else:
            self._gui.setPlaying()
            self.playing = True

    def _next(self):
        self.curtrack = self.nexttrack
        self._db.nexttrack()
        self.nexttrack = self._db.getnexttrack()
        self._gui.setTrackInfo(self.curtrack)
        self._cache.swap()
        self._cache.cachetrack(self.nexttrack['path'])

    def requestnext(self):
        self._nextrequested = True

    def _prev(self):
        self._cache.expireBoth()
        self._db.prevtrack()
        self.curtrack = self._db.getcurrenttrack()
        self.nexttrack = self._db.getnexttrack()
        self._gui.setTrackInfo(self.curtrack)
        self._cache.cachetrack(
            self.curtrack['path'], 
            slot=self._cache.curbuf.id
        )
        self._cache.cachetrack(self.nexttrack['path'])

    def requestprev(self):
        self._prevrequested = True



if __name__ == "__main__":

    app = PySide2.QtWidgets.QApplication(sys.argv)
    app.setStyleSheet('''
        QWidget {
            background-color: black;
            color: white;
        }
        QToolButton {
            border: 1px solid DimGray;
            border-radius: 4px;
        }
    ''')
    MusicPlayer()
    sys.exit(app.exec_())