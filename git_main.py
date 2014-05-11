#!/usr/bin/env python
# -*- coding: utf-8 -*- 

"""Git-GUI with mail function."""

#---------------------------------------------------------------------------
import wx

from gitGui import GitFrame

#---------------------------------------------------------------------------

#---------------------------------------------------------------------------

class App(wx.App):
    """Application class."""

    def OnInit(self):
        #image = wx.Image('wxPython.jpg', wx.BITMAP_TYPE_JPEG)
        self.frame = GitFrame(parent=None, id=-1)

        self.frame.Show()
        self.SetTopWindow(self.frame)
        return True

def main():
    app = App()
    app.MainLoop()

if __name__ == '__main__': #pass
    main()


#---------------------------------------------------------------------------
#if __name__ == '__main__':
#    app = wx.PySimpleApp()
#    frame = GitFrame(parent=None, id=-1)
#    frame.Show()
#    app.MainLoop()
#---------------------------------------------------------------------------
