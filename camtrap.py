#! /usr/bin/env python

import os
import datetime
import errno
import random
import sys
from PyQt4 import QtGui, QtCore
from PyQt4.phonon import Phonon
import cv

class CamTrapWindow(QtGui.QMainWindow):
    def __init__(self):
        QtGui.QMainWindow.__init__(self)
        self.setWindowFlags(
            QtCore.Qt.WindowStaysOnTopHint
            | QtCore.Qt.FramelessWindowHint
            | QtCore.Qt.X11BypassWindowManagerHint
            )
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.setStyleSheet("background-color:transparent;")
        desktop = QtGui.qApp.desktop()
        self.setGeometry(desktop.rect())

        self.capture_width=640
        self.capture_height=480
        self.labels = []
        self.pix = None
        
        #self.audio = Phonon.AudioOutput(Phonon.MusicCategory, self)
        
        self.alarms = []
        for (dirpath, dirnames, filenames) in os.walk("assets/alarms"):
            for filename in filenames:
                if os.path.splitext(filename)[1] == '.mp3':
                    m = Phonon.MediaSource(os.path.join(dirpath, filename))
                    self.alarms.append(Phonon.createPlayer(Phonon.MusicCategory, m))
                    print "loaded %s" % filename

        self.font = QtGui.QFont('Impact', 50)
        self.font.setHintingPreference(QtGui.QFont.PreferDefaultHinting)
        self.font.setStyleStrategy(QtGui.QFont.PreferAntialias)
        self.font.setStyle(QtGui.QFont.StyleNormal)
        self.font.setWeight(QtGui.QFont.Normal)

        self.caught_dir = 'caught'
        try:
            os.makedirs(self.caught_dir)
        except OSError as e:
            if e.errno not in (errno.EEXIST,):
                raise
        print "saving captures to %s" % self.caught_dir

        self.clear_timer = QtCore.QTimer()
        self.clear_timer.timeout.connect(self.clear)

    def clear(self):
        for label in self.labels:
            label.clear()
        
    def resizeEvent(self, event=None):
        desktop = QtGui.qApp.desktop()
        for label in self.labels:
            label.deleteLater()
        self.labels = []
            
        for screen_idx in range(desktop.numScreens()):
            rect = desktop.screenGeometry(screen_idx)
            label = QtGui.QLabel('', self)
            label.move(rect.x(), rect.y())
            label.resize(rect.width(), rect.height())
            label.setScaledContents(True)
            if self.pix:
                label.setPixmap(self.pix)
            self.labels.append(label)
        
    def mousePressEvent(self, event):
        self.capture()

    def keyPressEvent(self, event):
        if event.nativeScanCode() in (50 # left-shift
                                      ,62 # right-shift
                                      ,64 # left-alt
                                      ):
            QtGui.qApp.quit()
        else:
            self.capture()

    def capture(self):
        try:
            #self.audio.setMuted(False)
            #self.audio.setVolume(0.8)
            random.choice(self.alarms).play()
        except Exception as e:
            print "WARNING: couldn't play alarm: %s" % e

        try:
            cap = cv.CaptureFromCAM(-1)
            cv.SetCaptureProperty(cap, cv.CV_CAP_PROP_FRAME_WIDTH, self.capture_width)
            cv.SetCaptureProperty(cap, cv.CV_CAP_PROP_FRAME_HEIGHT, self.capture_height)
            frame = cv.QueryFrame(cap)
            im = QtGui.QImage(frame.tostring(), frame.width, frame.height, QtGui.QImage.Format_RGB888).rgbSwapped()
            pix = QtGui.QPixmap(im)

            # save pix
            stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S.%f")
            pix.save(os.path.join(self.caught_dir, stamp) + ".png")

            # add caption
            painter = QtGui.QPainter(pix)
            painter.setFont(self.font)
            painter.setPen(QtGui.QColor('yellow'))
            painter.setBrush(QtGui.QColor('yellow'))
            rect = QtCore.QRect(0, 0, self.capture_width, self.capture_height)
            painter.drawText(rect, QtCore.Qt.AlignTop + QtCore.Qt.AlignHCenter, "Yo! Hands Off")
            painter.drawText(rect, QtCore.Qt.AlignBottom + QtCore.Qt.AlignHCenter, "My Junk!")
            painter.end()
            
            self.pix = pix
            for label in self.labels:
                label.setPixmap(self.pix)

            self.clear_timer.start(600 * 1000)

        except Exception as e:
            print "WARNING: couldn't capture video: %s" % e

app = QtGui.QApplication(sys.argv)
w = CamTrapWindow()
w.show()
w.grabKeyboard()
w.grabMouse()
app.exec_()
