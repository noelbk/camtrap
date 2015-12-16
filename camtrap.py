#! /usr/bin/env python
#
# camtrap.py - 

import os
import datetime
import errno
import random
import sys
from PyQt4 import QtGui, QtCore
from PyQt4.phonon import Phonon
import cv2
import numpy
import captions

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

        # clear the screen after 30 seconds
        self.clear_timer = QtCore.QTimer()
        self.clear_timer.setInterval(30 * 1000)
        self.clear_timer.setSingleShot(True)
        self.clear_timer.timeout.connect(self.clear)

        # record video at 10 fps
        self.capture_fourcc = cv2.cv.CV_FOURCC(*'XVID')
        self.capture_fps = 10
        self.camera = None
        self.writer = None
        self.capture_frame_timer = QtCore.QTimer(self)
        self.capture_frame_timer.setInterval(1000/self.capture_fps)
        self.capture_frame_timer.timeout.connect(self.capture_frame_timer_handler)

        # stop recording after 10 seconds
        self.capture_stop_timer = QtCore.QTimer(self)
        self.capture_stop_timer.setInterval(10 * 1000)
        self.capture_stop_timer.setSingleShot(True)
        self.capture_stop_timer.timeout.connect(self.capture_stop_timer_handler)

        # load captions
        self.captions = captions.load_captions()
        self.caption_top, self.caption_bottom = captions.choose(self.captions)

    def clear(self):
        self.clear_timer.stop()
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

    def quit(self):
        self.capture_stop()
        QtGui.qApp.quit()

    def keyPressEvent(self, event):
        if event.key() in (QtCore.Qt.Key_Control, QtCore.Qt.Key_Alt):
            self.quit()
        else:
            self.capture()

    def capture(self):
        try:
            random.choice(self.alarms).play()
        except Exception as e:
            print "WARNING: couldn't play alarm: %s" % e

        self.captions = captions.load_captions()
        self.caption_top, self.caption_bottom = captions.choose(self.captions)
        self.capture_start()
        
    def capture_start(self):  
        self.capture_stop_timer.start()
        self.clear_timer.start()
        
        if not self.camera:
            try:
                self.camera = cv2.VideoCapture(0)
                if not self.camera.isOpened():
                    self.camera.open()
                self.camera.set(cv2.cv.CV_CAP_PROP_FRAME_WIDTH, self.capture_width)
                self.camera.set(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT, self.capture_height)

                stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S.%f")
                self.writer = cv2.VideoWriter(os.path.join(self.caught_dir, stamp) + ".avi",
                                              self.capture_fourcc,
                                              self.capture_fps,
                                              (self.capture_width, self.capture_height))
                
                self.capture_frame_timer.start()
                self.capture_frame_timer_handler()
            except Exception as e:
                print "WARNING: couldn't capture video: %s" % e
                self.capture_stop()

    def capture_stop_timer_handler(self, event=None):
        self.capture_stop()
        
    def capture_stop(self):
        self.capture_frame_timer.stop()
        if self.camera:
            self.camera.release()
            self.camera = None
        if self.writer:
            self.writer.release()
            self.writer = None
        
    def capture_frame_timer_handler(self, event=None):
        ret, frame = self.camera.read()
        if not ret:
            return

        try:
            self.writer.write(frame)
            
            height, width, byteValue = frame.shape
            byteValue = byteValue * width
            cv2.cvtColor(frame, cv2.COLOR_BGR2RGB, frame)
            image = QtGui.QImage(frame, width, height, byteValue, QtGui.QImage.Format_RGB888)
            pix = QtGui.QPixmap(image)
            self.pix = pix

            # add caption
            painter = QtGui.QPainter(pix)
            painter.setFont(self.font)
            painter.setPen(QtGui.QColor('yellow'))
            painter.setBrush(QtGui.QColor('yellow'))
            rect = QtCore.QRect(0, 0, self.capture_width, self.capture_height)
            painter.drawText(rect, QtCore.Qt.AlignTop + QtCore.Qt.AlignHCenter, self.caption_top)
            painter.drawText(rect, QtCore.Qt.AlignBottom + QtCore.Qt.AlignHCenter, self.caption_bottom)
            painter.end()
            
            for label in self.labels:
                label.setPixmap(self.pix)

            self.clear_timer.start()

        except Exception as e:
            print "WARNING: couldn't save video: %s" % e

app = QtGui.QApplication(sys.argv)
w = CamTrapWindow()
w.show()
w.grabKeyboard()
w.grabMouse()
app.exec_()
