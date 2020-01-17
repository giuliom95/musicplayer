#!/bin/python3

import sys
import PySide2.QtWidgets as qtw
import PySide2.QtGui as qtg
import PySide2.QtCore as qtc
import PySide2.Qt as qt

import musicdb

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


if __name__ == "__main__":
    db = musicdb.MusicDB('./test.db')

    app = qtw.QApplication(sys.argv)
    
    window = qtw.QWidget()
    mainlayout = qtw.QHBoxLayout()
    mainlayout.setContentsMargins(0,0,0,0)

    albumlist = AlbumList(db)
    mainlayout.addWidget(albumlist)

    window.setLayout(mainlayout)

    window.show()

    sys.exit(app.exec_())

