#!/usr/bin/python2.7

import wx
import sys
import random
import select

from wx import glcanvas

# The Python OpenGL package can be found at
# http://PyOpenGL.sourceforge.net/
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *

try:
    from PIL.Image import open
except ImportError, err:
    from Image import open

"""
This code is based on code from:
        http://wxpython-users.1045709.n5.nabble.com/Resizing-GLCanvas-Panel-td2341501.html
as well as:
        http://wiki.wxpython.org/GLCanvas
"""
class MyCanvasBase(glcanvas.GLCanvas):
    def __init__(self, parent):
        # The size of the GLCanvas is set here. Since the canvas will resize to
        # fit the window, this actually just sets the aspect ratio of the
        # canvas.
        glcanvas.GLCanvas.__init__(self, parent, -1, size=(100, 150))
        self.init = False
        # Record initial mouse position.
        self.lastx = self.x = 30
        self.lasty = self.y = 30
        self.size = None

        self.Bind(wx.EVT_ERASE_BACKGROUND, self.OnEraseBackground)
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_LEFT_DOWN, self.OnMouseDown)
        self.Bind(wx.EVT_LEFT_UP, self.OnMouseUp)
        self.Bind(wx.EVT_MOTION, self.OnMouseMotion)

    def OnEraseBackground(self, event):
        pass # Do nothing, to avoid flashing on MSW.

    def OnSize(self, event):
        (w, h) = self.GetGLExtents()
        if self.GetContext():
            self.SetCurrent()
            glViewport(0, 0, w, h)
        event.Skip()

    def OnPaint(self, event):
        dc = wx.PaintDC(self)
        self.SetCurrent()
        if not self.init:
            self.InitGL()
            self.init = True
        self.OnDraw()

    def GetGLExtents(self):
        """Get the extents of the OpenGL canvas."""
        return self.GetClientSize()

    def OnMouseDown(self, evt):
        self.CaptureMouse()
        self.x, self.y = self.lastx, self.lasty = evt.GetPosition()

    def OnMouseUp(self, evt):
        self.ReleaseMouse()
        x = evt.GetX()
        y = evt.GetY()
        print "left click at %d, %d" % (x, y)

    def OnMouseMotion(self, evt):
        if evt.Dragging() and evt.LeftIsDown():
            self.lastx, self.lasty = self.x, self.y
            self.x, self.y = evt.GetPosition()
            self.Refresh(False)

    def OnInitGL(self):
        """Initialize OpenGL for use in the window."""
        glClearColor(1, 0, 0, 1)

    def OnDraw(self, *args, **kwargs):
        """Draw the window."""
        glClear(GL_COLOR_BUFFER_BIT)

        # Drawing an example triangle in the middle of the screen
        glBegin(GL_TRIANGLES)
        glColor(0, 0, 0)
        glVertex(-.25, -.25)
        glVertex(.25, -.25)
        glVertex(0, .25)
        glEnd()

        self.SwapBuffers()

class CubeCanvas(MyCanvasBase):
    def __init__(self, parent=None, app=None):
        MyCanvasBase.__init__(self, parent)

        self.app = app

        self.graphFile = "graph.png"
        
        self.Bind(wx.EVT_KEY_DOWN, self.onKeyPress)

        self.graphs = makeRandomGraph(3)

    def update(self, graphs=None, updateNetwork=False):
        if updateNetwork:
            self.modifyImage()
            self.reloadGraph(self.im)
            self.OnDraw()
        if graphs:
            for count, graph in enumerate(graphs):
                if graph:
                    if count < len(self.graphs):
                        self.graphs[count] = graph
                    else:
                        self.graphs.append(graph)
            self.OnDraw()

    def InitGL(self):
        # Set viewing projection
        glMatrixMode(GL_PROJECTION)

        # Use 2-dimensional orthographic projection.
        gluOrtho2D(-1.0, 1.0, -1.0, 1.0)

        # Enable depth testing. This isn't really necessary, but doesn't hurt.
        glEnable(GL_DEPTH_TEST)

        # Open graph.png.
        self.im = open(self.graphFile)

        # Generate texture for network graph.
        self.graphTex = self.loadImage(self.im)
        
        #glEnable(GL_TEXTURE_2D)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)

    def setupTexture(self):
        """Render-time texture environment setup"""
        glEnable(GL_TEXTURE_2D)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        
    def loadImage(self, im):
        try:
            ix, iy, image = im.size[0], im.size[1], \
                    im.tostring("raw", "RGBA", 0, -1)
        except SystemError:
            ix, iy, image = im.size[0], im.size[1], \
                    im.tostring("raw", "RGBX", 0, -1)
        ID = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, ID)
        glPixelStorei(GL_UNPACK_ALIGNMENT, 1)

        glTexImage2D(GL_TEXTURE_2D, 0, 3, ix, iy, 0,
                     GL_RGBA, GL_UNSIGNED_BYTE, image)
        return ID

    def reloadGraph(self, im):
        im = open(self.graphFile)
        try:
            ix, iy, image = im.size[0], im.size[1], \
                    im.tostring("raw", "RGBA", 0, -1)
        except SystemError:
            ix, iy, image = im.size[0], im.size[1], \
                    im.tostring("raw", "RGBX", 0, -1)
        
        # Reload network graph.
        glBindTexture(GL_TEXTURE_2D, self.graphTex)
        glPixelStorei(GL_UNPACK_ALIGNMENT, 1)

        glTexImage2D(GL_TEXTURE_2D, 0, 3, ix, iy, 0,
                     GL_RGBA, GL_UNSIGNED_BYTE, image)

    # For debugging purposes only. Modifies graph.png to demonstrate that it is
    # being reloaded.
    def modifyImage(self):
        self.im = self.im.rotate(1)
        self.im.save(self.graphFile)

    def OnDraw(self):
        # Clear color and depth buffers.
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        # Set up texture mapping.
        self.setupTexture()

        self.drawGraphs(0.45, 0.0125, 0.0125, 0.0125)

        self.SwapBuffers()

    def drawGraphs(self, topWeight, topGap=0.0, midGap=0.0, bottomGap=0.0):
        """Assumes that weight is a float between 0.0 and 1.0"""
        # Draw top graph area.
        self.drawTopGraph(topWeight, topGap)
        # Draw bottom graph area.
        self.drawBottomGraphs(1.0 - topGap - midGap - topWeight - bottomGap, bottomGap)

    def drawTopGraph(self, weight, pad=0.0):
        glBindTexture(GL_TEXTURE_2D, self.graphTex)
        glColor3f(1.0, 1.0, 1.0)
        range = 2.0
        min = -1.0
        max = 1.0
        top = max - range * pad
        bottom = top - range * weight
        left = min
        right = max
        glBegin(GL_QUADS)
        glTexCoord2f(0.0, 1.0); glVertex2f(left, top)
        glTexCoord2f(0.0, 0.0); glVertex2f(left, bottom)
        glTexCoord2f(1.0, 0.0); glVertex2f(right, bottom)
        glTexCoord2f(1.0, 1.0); glVertex2f(right, top)
        glEnd()
        glColor3f(1.0, 1.0, 1.0)
        glBindTexture(GL_TEXTURE_2D, -1)

    def drawBottomGraphs(self, weight, pad=0.0):
        # Calculate graph area boundaries.
        range = 2.0
        min = -1.0
        max = 1.0
        bottom = min + range * pad
        curTop = top = bottom + range * weight
        graphHeight = (range * weight) / (float)(len(self.graphs))
        curBottom = curTop - graphHeight
        left = min
        right = max
        # Draw each graph in the list of graphs.
        for graph in self.graphs:
            graph.draw(left, right, curTop, curBottom)
            curTop = curBottom
            curBottom = curBottom - graphHeight

    def onKeyPress(self, event):
        keycode = event.GetKeyCode()
        if chr(keycode) >= 'A' and chr(keycode) <= 'Z':
            print "key pressed: %c" % (chr(keycode))
        else:
            print keycode
        if keycode == wx.WXK_SPACE:
            print "you pressed the spacebar!"
        elif chr(keycode) == 'Q':
            print "quitting"
            self.app.Exit()
        elif chr(keycode) == 'W':
            self.update()
        elif chr(keycode) == 'E':
            newGraphs = makeRandomGraph(3)
            self.update(newGraphs)
        elif chr(keycode) == 'R':
            newGraphs = makeRandomGraph(3)
            self.update(newGraphs, True)
        elif chr(keycode) == 'T':
            newGraphs = makeRandomGraph(4)
            newGraphs[1] = None
            self.update(newGraphs, True)
        elif chr(keycode) == 'F':
            self.update(updateNetwork=True)
        event.Skip()

class Graph():
    def __init__(self, size=20):
        self.size = size
        bgNum = random.random()
        self.fg = [random.random(), random.random(), random.random()]
        self.bg = [0.9, 0.9, 0.9]
        self.data = []
        for i in range(self.size):
            self.data.append(random.random())
    
    def random(self):
        for i in range(self.size):
            self.data[i] = (random.random())

    def draw(self, left, right, top, bottom):
        # Draw the graph borders.
        glColor3f(0.0, 0.0, 0.0)
        glBegin(GL_LINES)
        glVertex2f(left, top)
        glVertex2f(right, top)
        glVertex2f(left, bottom)
        glVertex2f(right, bottom)
        glEnd()

        # Draw the graph data (first because OpenGL draws in reverse).
        glColor3f(1.0, 0.0, 0.0)
        #glBegin(GL_LINE_STRIP)
        glBegin(GL_TRIANGLE_STRIP)
        for count, point in enumerate(self.data):
            curX = left + (float)(count) * (right - left) / (float)(len(self.data) - 1)
            curY = bottom + point * (top - bottom)
            glVertex2f(curX, curY)
            glVertex2f(curX, bottom)
        glEnd()

        # Draw the graph background.
        glColor3f(self.bg[0], self.bg[1], self.bg[2])
        glBegin(GL_QUADS)
        glVertex2f(left, top)
        glVertex2f(left, bottom)
        glVertex2f(right, bottom)
        glVertex2f(right, top)
        glEnd()

        glColor3f(1.0, 1.0, 1.0)

class InfoPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        t = wx.StaticText(self, -1, "This is an InfoPanel object", (40,40))

class VisFrame(wx.Frame):
    def __init__(self, parent, id, title='theframe', pos=wx.DefaultPosition,
                 size=wx.DefaultSize, style=wx.DEFAULT_FRAME_STYLE,
                 name='Netflow Visualization', app=None, filter=None):

        super(VisFrame, self).__init__(parent, id, title, pos, size, style, name)

        #self.Bind (wx.EVT_IDLE, self.OnIdle)

        self.filter = filter

        # Create a panel and a notebook on the panel.
        p = wx.Panel(self)
        nb = wx.Notebook(p)

        # Create the page windows as children of the notebook.
        visPage = wx.Panel(nb)
        # Create the GLCanvas.
        self.canvas = CubeCanvas(visPage, app=app)
        self.canvas.InitGL()
        # Create the node info panel.
        nodePanel = InfoPanel(visPage)
        # Add a sizer to visPage to manage its children.
        visSizer = wx.BoxSizer()
        visSizer.Add(self.canvas, 1, wx.SHAPED | wx.ALIGN_LEFT)
        visPage.SetSizer(visSizer)

        dataPage = InfoPanel(nb)

        # Add the pages to the notebook with the label to show on the tab
        nb.AddPage(visPage, "Visualization")
        nb.AddPage(dataPage, "Data")

        # Put the notebook in a sizer for the panel to manage the layout
        mainSizer = wx.BoxSizer()
        mainSizer.Add(nb, 1, wx.EXPAND)
        p.SetSizer(mainSizer)

        # Set a timer for filter updates.
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.OnTimer, self.timer)
        self.timer.Start(100)

    def OnTimer(self, event):
        self.update();
        # TODO: Make this get stuff from filter.

    #def OnIdle(self, event):
        #self.update();

    def update(self, graphs=None, updateNetwork=False):
        self.canvas.update(graphs, updateNetwork)

    def update(self):
        newGraphs, newImage = self.filter.update()
        self.canvas.update(newGraphs, newImage)

    def OnCloseMe(self, event):
        self.Close(True)

    def OnCloseWindow(self, event):
        self.Destroy()

def makeRandomGraph(size):
    graph = []
    for i in range(size):
        graph.append(Graph())
    return graph

class VisualizeWindow():
    def __init__(self):
        app = wx.App(0)
        myFilter = TestFilter()
        theFrame = VisFrame(None, -1, size=(600,600), name="The Frame",
                            app=app, filter=myFilter)
        theFrame.Show()
        app.MainLoop()

class TestFilter():
    def __init__(self, length=4):
        self.length = length
        self.graphs = []
        for i in range(length):
            self.graphs.append(Graph())

    def update(self):
        for g in self.graphs:
            g.random()
        if (random.random() > 0.8):
            return self.graphs, True
        else:
            return self.graphs, False

def main():
    vis = VisualizeWindow()

if __name__ == "__main__":
    main()
