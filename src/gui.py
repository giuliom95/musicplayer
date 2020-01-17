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
        if len(title) > 30:
            title = title[:35] + '...'
        icon = qtg.QIcon(qtg.QPixmap.fromImage(cover))
        self.setToolButtonStyle(qtc.Qt.ToolButtonTextUnderIcon)
        self.setIcon(icon)
        self.setIconSize(qtc.QSize(300, 300))
        self.setText(title)
        



if __name__ == "__main__":
    db = musicdb.MusicDB('./test.db')

    app = qtw.QApplication(sys.argv)
    
    window = qtw.QWidget()
    mainlayout = qtw.QHBoxLayout()

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

    albumlist_containerwidget = qtw.QWidget()
    albumlist_containerwidget.setLayout(albumlist_gridlayout)
    
    albumlist_scrollarea = qtw.QScrollArea()
    albumlist_scrollarea.setWidget(albumlist_containerwidget)
    mainlayout.addWidget(albumlist_scrollarea)

    window.setLayout(mainlayout)

    window.show()

    sys.exit(app.exec_())

