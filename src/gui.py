#!/bin/python3

import sys
import PySide2.QtWidgets as qtw
import PySide2.QtGui as qtg
import PySide2.QtCore as qtc
import PySide2.Qt as qt

import musicdb
import audiohandler

class MusicPlayer():

    def __init__(self):
        self._db = musicdb.MusicDB('./test.db')
        self._ah = audiohandler.AudioHandler()
        self.playing = False

    def play(self):
        print('PLAY')
        self.playing = True

    def pause(self):
        print('PAUSE')
        self.playing = False

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

    def __init__(self, db: musicdb.MusicDB):
        albumlist_gridlayout = qtw.QGridLayout()
        i = 0
        j = 0
        img = qtg.QImage()
        for album in db.getalbums():
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

    def __init__(self, musicplayer: MusicPlayer):
        self._mp = musicplayer
        super().__init__()

        mainlayout = qtw.QVBoxLayout()

        prevbtn = qtw.QPushButton('Prev')
        self._playpausebtn = qtw.QPushButton('Play')
        nextbtn = qtw.QPushButton('Next')

        infolabel = qtw.QLabel('Title\nArtist\nAlbum')

        layout = qtw.QHBoxLayout()
        layout.addWidget(prevbtn)
        layout.addWidget(self._playpausebtn)
        layout.addWidget(nextbtn)
        layout.addWidget(infolabel)
        layout.addStretch()

        mainlayout.addLayout(layout)

        self.setLayout(mainlayout)
        self.connect(self._playpausebtn, qtc.SIGNAL('clicked()'), self.playpausePressed)

    def playpausePressed(self):
        if self._mp.playing:
            self._mp.pause()
            self._playpausebtn.setText('Play')
        else:
            self._mp.play()
            self._playpausebtn.setText('Pause')

    



if __name__ == "__main__":
    app = qtw.QApplication(sys.argv)
    musicplayer = MusicPlayer()
    window = MainWindow(musicplayer)
    window.show()

    sys.exit(app.exec_())

