from win32gui import *
import win32gui, win32api, win32con
import time, os
import winutil
import snapshot
import screenresolution

from operations import CheckPoint, Click, Interval, \
                       Snap, Resolution, Orient

operation_classes = dict()
operation_classes['Click'] = Click
operation_classes['Interval'] = Interval
operation_classes['CheckPoint'] = CheckPoint
operation_classes['Snap'] = Snap
operation_classes['Resolution'] = Resolution
operation_classes['Orient'] = Orient

class Recorder:
    opList = []
    recording_state = False
    editPos = 0
    resolution = (0, 0)

    def __init__(self):
        if not os.path.exists(os.path.realpath('snapshots')):
            os.mkdir(os.path.realpath('snapshots'))

    # callbacks
    
    def OnLeftDown(self, pos):
        """callback function"""
        if self.recording_state:
            self.recordClick(pos)

    # interfaces

    def recordInterval(self, itv):
        self.record(Interval(itv))

    def recordClick(self, pos):
        wnd = WindowFromPoint(pos)
        while GetParent(wnd):
            wnd = GetParent(wnd)
        title = GetWindowText(wnd)
        # do not record click on Python Shell, cmd line or taskbar windows
        if not title: return
        if "Python Shell" in title: return
        if "Operation Genius" in title: return
        wPos = winutil.ScreenToWindow(wnd, pos)

        self.record(Click(title, wPos))

    def createCheckpoint(self, windowTitle, filename):
        path = self.imageFileToPath(filename)
        snapshot.snapWindow(windowTitle, path)
        self.record(CheckPoint(windowTitle, path))
    
    def recordCheckpoint(self, windowTitle, filename):
        path = self.imageFileToPath(filename)
        self.record(CheckPoint(windowTitle, path))

    def recordSnap(self, windowTitle, filename):
        path = self.imageFileToPath(filename)
        self.record(Snap(windowTitle, path))

    def recordResolution(self, resolution):
        self.record(Resolution(resolution))

    def recordOrient(self, flag):
        winutil.setOrientation(flag)
        self.record(Orient(flag))

    def erase(self, n):
        for i in range(n):
            if self.editPos > 0:
                self.editPos -= 1
                del self.opList[self.editPos]
            else:
                break
    
    def play(self, interval = 0.5):
        
        self.beforePlay()
        
        for op in self.opList:
            e = op.play()
            if e:
                print "play error: " + e
                break
            time.sleep(interval)
            
        self.afterPlay()
        
    def printOpList(self):
        if not self.opList:
            print "empty"
            print
            return
        for i, op in enumerate(self.opList):
            if i == self.editPos:
                print "------ editting here ------"
            print i + 1, ": " + op.__class__.__name__
            print '\t' + op.script_out()
        
        print

    def setEdit(self, pos):
        if pos == -1:
            self.editPos = len(self.opList)
        elif pos >= 0 and pos <= len(self.opList):
            self.editPos = pos
        else:
            print "position out of index"

    def clear(self):
        self.opList = []
        self.editPos = 0

    def start(self):
        self.recording_state = True

    def stop(self):
        self.recording_state = False

    def save(self, fname):
        with open(self.listFileToPath(fname), 'wb') as f:
            for op in self.opList:
                f.write(op.__class__.__name__ + '\n')
                f.write(op.script_out() + '\n')

    def load(self, fname):
        self.clear()
        with open(self.listFileToPath(fname), 'rb') as f:
            while True:
                n = f.readline().strip()
                s = f.readline().strip()
                if not n or not s: break
                op = operation_classes[n]()
                self.opList.append(op.script_in(s))

            self.editPos = len(self.opList)

    # private methods
    def record(self, op):
        self.opList.insert(self.editPos, op)
        self.editPos += 1

    def imageFileToPath(self, name):
        return 'snapshots/' + name + '.png'

    def listFileToPath(self, name):
        return 'lists/' + name + '.op'

    def beforePlay(self):
        winutil.setOrientation('tl')
        self.resolution = screenresolution.getRes()
        
    def afterPlay(self):
        if screenresolution.getRes() != self.resolution:
            screenresolution.convert(self.resolution)
