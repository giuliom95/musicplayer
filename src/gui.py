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

        iconsize = qtc.QSize(32, 32)
        icon = qtg.QIcon('./icons/prev.svg')
        prevbtn = qtw.QToolButton()
        prevbtn.setToolButtonStyle(qtc.Qt.ToolButtonIconOnly)
        prevbtn.setIcon(icon)
        prevbtn.setIconSize(iconsize)

        icon = qtg.QIcon('./icons/next.svg')
        nextbtn = qtw.QToolButton()
        nextbtn.setToolButtonStyle(qtc.Qt.ToolButtonIconOnly)
        nextbtn.setIcon(icon)
        nextbtn.setIconSize(iconsize)

        self._playicon = qtg.QIcon('./icons/play.svg')
        self._pauseicon = qtg.QIcon('./icons/pause.svg')
        self._playpausebtn = qtw.QToolButton()
        self._playpausebtn.setToolButtonStyle(qtc.Qt.ToolButtonIconOnly)
        self._playpausebtn.setIcon(self._playicon)
        self._playpausebtn.setIconSize(iconsize)

        self._albumcoverlabel = qtw.QLabel("Album cover here")

        controlslayout = qtw.QHBoxLayout()
        controlslayout.addStretch()
        controlslayout.addWidget(prevbtn)
        controlslayout.addWidget(self._playpausebtn)
        controlslayout.addWidget(nextbtn)
        controlslayout.addStretch()

        self._titlelabel = qtw.QLabel()
        self._artistlabel = qtw.QLabel()
        self._albumlabel = qtw.QLabel()
        self._titlelabel.setAlignment(qtc.Qt.AlignCenter)
        self._artistlabel.setAlignment(qtc.Qt.AlignCenter)
        self._albumlabel.setAlignment(qtc.Qt.AlignCenter)

        infoboxlayout = qtw.QVBoxLayout()
        infoboxlayout.addWidget(self._titlelabel)
        infoboxlayout.addWidget(self._artistlabel)
        infoboxlayout.addWidget(self._albumlabel)

        bottombarlayout = qtw.QVBoxLayout()
        bottombarlayout.addLayout(controlslayout)
        bottombarlayout.addLayout(infoboxlayout)

        mainlayout.addWidget(self._albumcoverlabel)
        mainlayout.addLayout(bottombarlayout)

        self.setLayout(mainlayout)

        bottombarlayout.setContentsMargins(5,0,5,5)
        infoboxlayout.setMargin(0)
        infoboxlayout.setSpacing(0)
        mainlayout.setMargin(0)

        self.connect(self._playpausebtn, qtc.SIGNAL('clicked()'), self.playpausePressed)
        self.connect(nextbtn, qtc.SIGNAL('clicked()'), self.nextPressed)
        self.connect(prevbtn, qtc.SIGNAL('clicked()'), self.prevPressed)

    def playpausePressed(self):
        self._mp.playpause()

    def setPaused(self):
        self._playpausebtn.setIcon(self._playicon)

    def setPlaying(self):
        self._playpausebtn.setIcon(self._pauseicon)

    def nextPressed(self):
        self._mp.requestnext()

    def prevPressed(self):
        self._mp.requestprev()

    def setTrackInfo(self, trackinfo):
        self.setFixedSize(self.sizeHint())
        self._titlelabel.setText(f'<b>{trackinfo["title"]}</b>')
        self._artistlabel.setText(trackinfo['artist'])
        self._albumlabel.setText(trackinfo['album'])

        img = qtg.QImage()
        img.loadFromData(trackinfo['albumcover'])
        img = img.scaledToHeight(300, qtc.Qt.TransformationMode.SmoothTransformation)
        img = img.copy(qtc.QRect(0, 0, 300, 300))
        self._albumcoverlabel.setPixmap(qtg.QPixmap.fromImage(img))