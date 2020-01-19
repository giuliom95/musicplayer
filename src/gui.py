#!/bin/python3

import typing
import threading

import PySide2.QtWidgets as qtw
import PySide2.QtGui as qtg
import PySide2.QtCore as qtc
import PySide2.Qt as qt

import sys


class AlbumWidget(qtw.QToolButton):
    _rect = qtc.QRect(0, 0, 300, 300)

    def __init__(self, title: str, cover: qtg.QImage):
        super().__init__()

        cover = cover.scaledToHeight(300, qtc.Qt.TransformationMode.SmoothTransformation)
        cover = cover.copy(self._rect)
        icon = qtg.QIcon(qtg.QPixmap.fromImage(cover))
        self.setToolButtonStyle(qtc.Qt.ToolButtonIconOnly)
        self.setIcon(icon)
        self.setIconSize(qtc.QSize(300, 300))
        self.setToolTip(title)
        self.setToolTipDuration(0)


class AlbumList(qtw.QScrollArea):

    def __init__(self, albums: typing.Callable):
        albumlist_gridlayout = qtw.QGridLayout()
        i = 0
        j = 0
        img = qtg.QImage()
        for album in albums():
            img.loadFromData(album[2])
            widget = AlbumWidget(album[1], img)
            albumlist_gridlayout.addWidget(widget, j, i)

            i += 1
            if i == 3:
                i = 0
                j += 1

        containerwidget = qtw.QWidget()
        containerwidget.setLayout(albumlist_gridlayout)

        super().__init__()
        self.setHorizontalScrollBarPolicy(qtc.Qt.ScrollBarAlwaysOff)
        self.setWidget(containerwidget)


class MainWindow(qtw.QWidget):

    def __init__(self, musicplayer):
        
        self._mp = musicplayer
        super().__init__()

        mainlayout = qtw.QVBoxLayout()

        prevbtn = qtw.QPushButton('Prev')
        self._playpausebtn = qtw.QPushButton('Play')
        nextbtn = qtw.QPushButton('Next')

        self._infolabel = qtw.QLabel('\n\n')

        layout = qtw.QHBoxLayout()
        layout.addWidget(prevbtn)
        layout.addWidget(self._playpausebtn)
        layout.addWidget(nextbtn)
        layout.addWidget(self._infolabel)
        layout.addStretch()

        mainlayout.addLayout(layout)

        self.setLayout(mainlayout)
        self.connect(self._playpausebtn, qtc.SIGNAL('clicked()'), self.playpausePressed)

    def playpausePressed(self):
        self._mp.playpause()

    def setPaused(self):
        self._playpausebtn.setText('Play')

    def setPlaying(self):
        self._playpausebtn.setText('Pause')

    def setTrackInfo(self, title: str, artist: str, album: str):
        self._infolabel.setText(f'{title}\n{artist}\n{album}')