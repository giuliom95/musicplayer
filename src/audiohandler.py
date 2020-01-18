#!/bin/python3

import simpleaudio as sa

import subprocess
import pathlib
import os
import threading

class AudioHandler():

    def __init__(self):
        self._waveobj = None
        self._playobj = None
        self._thread = None
        self._bufferfilepath = pathlib.Path('./buffer.wav')

    def playtrack(self, path: pathlib.Path):
        subprocess.Popen([
            'ffmpeg',
            '-i', str(path),
            '-f', 'wav',
            '-c:a', 'pcm_s16le', 
            '-y', self._bufferfilepath
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL)

        self._thread = threading.Thread(target=self._playtrackaftermath)
        self._thread.start()

    def _playtrackaftermath(self):
        while True:
            try:
                # Check if ffmpeg has written something to disk yet
                bufferinfo = os.stat(self._bufferfilepath)
                if bufferinfo.st_size > 0:
                    self._waveobj = sa.WaveObject.from_wave_file(str(self._bufferfilepath))
                    self._playobj = self._waveobj.play()
                    break
            except Exception as e:
                if not isinstance(e, FileNotFoundError):
                    raise


if __name__=='__main__':
    ah = AudioHandler()
    ah.playtrack(pathlib.Path('/home/gmartell/Music/bak/05 - Poor Leno.mp3'))

    while True:
        pass