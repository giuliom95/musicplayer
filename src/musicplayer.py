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

    def isReadyToBeFilled(self):
        return  self.status == BufferStatus.EMPTY or \
                self.status == BufferStatus.EXHAUSTED


class Cache():
    def __init__(self):
        self._bufs = [
            Buffer(pathlib.Path('./buf0.wav')),
            Buffer(pathlib.Path('./buf1.wav'))
        ]
        self._processes = [None, None]

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

        self._processes[slot] = subprocess.Popen([
            'ffmpeg',
            '-i', trackpath,
            '-f', 'wav',
            '-c:a', 'pcm_s16le', 
            '-y', b.path
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL)

        b.status = BufferStatus.FILLING

        print(f'[INFO] Started chaching {trackpath} on slot #{slot}')


class MusicPlayer():

    def __init__(self):

        self._pyaudio = pyaudio.PyAudio()

        self._cache = Cache()

        self._thread = threading.Thread(target=self._mainloop)
        self._thread.start()

        dbpath = pathlib.Path('./music.db')
        self._db = musicdb.MusicDB(dbpath)

        self.curtrack = self._db.getnexttrack()
        self._cache.cachetrack(self.curtrack['path'])

        
        self._gui = gui.MainWindow(self)
        self._gui.setTrackInfo(
            self.curtrack['title'],
            self.curtrack['artist'],
            self.curtrack['album']
        )
        self._gui.show()


    def __del__(self):
        #self._audiostream.stop_stream()
        #self._audiostream.close()
        self._pyaudio.terminate()


    '''
    def _looping(self):
        while True:
            try:
                audiofileinfo = os.stat(self._wavfilepath)
                if audiofileinfo.st_size > 0:
                    break
            except Exception as e:
                if not isinstance(e, FileNotFoundError):
                    raise
        
        CHUNK = 1024
        wf = wave.open(str(self._wavfilepath), 'rb')
        self._audiostream = self._pyaudio.open(
            format=pyaudio.paInt16,
            channels=2,
            rate=wf.getframerate(),
            output=True
        )

        data = wf.readframes(CHUNK)
        # play stream (3)
        while len(data) > 0:
            self._audiostream.write(data)
            data = wf.readframes(CHUNK)
    '''

    def _mainloop(self):
        while True:
            break


if __name__ == "__main__":

    app = PySide2.QtWidgets.QApplication(sys.argv)
    MusicPlayer()
    sys.exit(app.exec_())