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
SILENCE = b'0'*4

class BufferStatus(enum.Enum):
    EMPTY       = enum.auto()
    FILLING     = enum.auto()
    READY       = enum.auto()
    BEING_READ  = enum.auto()
    EXHAUSTED   = enum.auto() 


class Buffer():
    def __init__(self, path: pathlib.Path):
        self.path = path
        self.status = BufferStatus.EMPTY
        self.fillingprocess = None
        self.wave = None

    def isReadyToBeFilled(self):
        return  self.status == BufferStatus.EMPTY or \
                self.status == BufferStatus.EXHAUSTED


class Cache():
    def __init__(self):
        self._bufs = [
            Buffer(pathlib.Path('./buf0.wav')),
            Buffer(pathlib.Path('./buf1.wav'))
        ]

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
                if b.isReadyToBeFilled():
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

        print(f'[INFO] Started chaching "{trackpath}" on buffer {b.path.name}')

    def upkeep(self):
        for b in self._bufs:
            if b.status == BufferStatus.FILLING:
                if b.fillingprocess.poll() is not None:
                    b.wave = wave.open(str(b.path), 'rb')
                    b.status = BufferStatus.READY
                    print(f'[INFO] Buffer {b.path.name} ready')


class MusicPlayer():

    def __init__(self):

        self._pyaudio = pyaudio.PyAudio()
        self._audiostream = self._pyaudio.open(
            format=pyaudio.paInt16,
            channels=2,
            rate=44100,
            output=True
        )

        dbpath = pathlib.Path('./music.db')
        self._db = musicdb.MusicDB(dbpath)

        self.curtrack = self._db.getnexttrack()

        self._cache = Cache()
        self._cache.cachetrack(self.curtrack['path'])
        
        self._gui = gui.MainWindow(self)
        self._gui.setTrackInfo(
            self.curtrack['title'],
            self.curtrack['artist'],
            self.curtrack['album']
        )
        self._gui.show()

        self._thread = threading.Thread(target=self._mainloop)
        self._thread.start()

    def __del__(self):
        self._audiostream.stop_stream()
        self._audiostream.close()
        self._pyaudio.terminate()

    def _mainloop(self):
        while True:
            self._cache.upkeep()
            time.sleep(.1)

            if not self._gui.isVisible():
                break

            self._audiostream.write(SILENCE)


if __name__ == "__main__":

    app = PySide2.QtWidgets.QApplication(sys.argv)
    MusicPlayer()
    sys.exit(app.exec_())