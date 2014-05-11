#!/usr/bin/env python
# -*- coding: utf-8 -*- 

"""Git-GUI with mail function."""

#---------------------------------------------------------------------------

import os
import sys
import time
import re
import subprocess
import wx
import  wx.lib.editor    as  editor
import  wx.lib.mixins.listctrl  as  listmix

from mainField import MixinListCtrlPanel

#---------------------------------------------------------------------------
# A custom wxLog class

class MyLog(wx.PyLog):

    def __init__(self, textCtrl, logTime=0):
        wx.PyLog.__init__(self)
        self.tc = textCtrl
        self.logTime = logTime
        #print 'Log! shit......'
    
    ''' 
    def DoLog(self, message, timeStamp):
        #print message, timeStamp
        #if self.logTime:
        #    message = time.strftime("%X", time.localtime(timeStamp)) + \
        #              ": " + message
        print 'hahah'
        if self.tc:
            self.tc.AppendText(message + '\n')
    '''
    
    def DoLogString(self, message, timeStamp):
        #print message, timeStamp
        if self.logTime:
            message = time.strftime("%H:%M:%S", time.localtime(timeStamp)) + \
                      " : " + message

        if self.tc:
            self.tc.AppendText(message + '\n')

#---------------------------------------------------------------------------

#---------------------------------------------------------------------------
class MyLogWindow(wx.TextCtrl):

    def __init__(self, parent, Id=-1, value='', pos=wx.DefaultPosition, size=wx.DefaultSize, 
        style = wx.TE_MULTILINE|wx.TE_READONLY|wx.HSCROLL):

        wx.TextCtrl.__init__(self, parent, id=Id, value=value, pos=pos, size=size, style=style)


    def write(self, msg):

        t = time.localtime(time.time())
        st = time.strftime("%H:%M:%S", t)
        
        wx.TextCtrl.write(self, st + ' : ' + msg + '\n')

    def SetValue(self, msg):

        t = time.localtime(time.time())
        st = time.strftime("%H:%M:%S", t)
        
        wx.TextCtrl.SetValue(self, st + ' : ' + msg + '\n')

#---------------------------------------------------------------------------



#---------------------------------------------------------------------------
class mainSashWindow(wx.Panel):

    def __init__(self, parent):
        wx.Panel.__init__(self, parent, -1)

        self.parent = parent
        self.gitRepo = parent.gitRepo

        self.currentItem = None

        self.current_dir = '/home' #os.path.abspath('~')
        self.current_sel_dir = None
        self.current_file = None
        #self.current_sel_item = [None, 0]
        #self.last_sel_item = None
        #self.edited_item = None
        self.clipboard = [0, None]

        self.is_git_dir = False
        self.listItems = {}


        winids = []

        # Create some layout windows
        # A window like a statusbar
        bottomwin = wx.SashLayoutWindow(
                self, -1, wx.DefaultPosition, (200, 30), 
                wx.NO_BORDER|wx.SW_3D
                )

        bottomwin.SetDefaultSize((1000, 120))
        bottomwin.SetOrientation(wx.LAYOUT_HORIZONTAL)
        bottomwin.SetAlignment(wx.LAYOUT_BOTTOM)
        #bottomwin.SetBackgroundColour(wx.Colour(0, 0, 255))
        bottomwin.SetSashVisible(wx.SASH_TOP, True)
        #bottomwin.SetExtraBorderSize(10)
        
        self.bottomWindow = bottomwin
        
        self.bottomBox = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.bottomBox)


        self.createTextCtrl()
        #self.createBottomBar()
        winids.append(bottomwin.GetId())


        # A window to the left of the client window

        leftwin =  wx.SashLayoutWindow(
                self, -1, wx.DefaultPosition, (200, 30), 
                wx.NO_BORDER|wx.SW_3D
                )

        leftwin.SetDefaultSize((200, 1000))
        leftwin.SetOrientation(wx.LAYOUT_VERTICAL)
        leftwin.SetAlignment(wx.LAYOUT_LEFT)
        #leftwin.SetBackgroundColour(wx.Colour(0, 255, 0))
        leftwin.SetSashVisible(wx.SASH_RIGHT, True)
        #bottomwin.SetExtraBorderSize(10)

        self.leftWindow = leftwin
        self.createDirCtrl()
        winids.append(leftwin.GetId())


        # will occupy the space not used by the Layout Algorithm
        self.remainingSpace = wx.Panel(self, -1, style=wx.SUNKEN_BORDER)
        self.lcBox = wx.BoxSizer(wx.VERTICAL)
        self.createGitField1()
        self.remainingSpace.SetSizer(self.lcBox)

        self.remainingSpace.SetAutoLayout(True)
        
        self.Bind(
            wx.EVT_SASH_DRAGGED_RANGE, self.OnSashDrag,
            id=min(winids), id2=max(winids)
            )

        self.Bind(wx.EVT_SIZE, self.OnSize)






    def createDirCtrl(self):

        self.dir = wx.GenericDirCtrl(self.leftWindow, -1, dir=self.current_dir, 
            pos=wx.DefaultPosition, size=wx.DefaultSize, style=wx.DIRCTRL_DIR_ONLY)

        self._tree=self.dir.GetTreeCtrl()

        #self.dir.Bind(wx.EVT_TREE_END_LABEL_EDIT, self.treeItemOnOpen, self._tree)
        self.dir.Bind(wx.EVT_TREE_SEL_CHANGED, self.treeItemOnSelChanged, self._tree)
        self.dir.Bind(wx.EVT_TREE_ITEM_MENU, self.treeItemOnMenu, self._tree)

        
        
    def createTextCtrl(self):

        # Set up a log window
        self.log = MyLogWindow(self.bottomWindow)
        self.bottomBox.Add(self.log, 1, wx.ALL|wx.GROW, 1)

        #if wx.Platform == "__WXMAC__":
        #    self.log.MacCheckSpelling(False)
        self.log.SetValue("Log output window...")
        
        # Set the wxWindows log target to be this textctrl
        #wx.Log_SetActiveTarget(wx.LogTextCtrl(self.log))

        # But instead of the above we want to show how to use our own wx.Log class
        self.mylog = MyLog(self.log)
        wx.Log_SetActiveTarget(self.mylog)




    def createGitField(self):

    	il = wx.ImageList(16,16,True)

        self.fileidx = il.Add(wx.ArtProvider.GetBitmap(wx.ART_NORMAL_FILE, wx.ART_OTHER, (16,16)))
        self.fldridx = il.Add(wx.ArtProvider.GetBitmap(wx.ART_FOLDER, wx.ART_OTHER, (16,16)))
        #self.fldropenidx = il.Add(wx.ArtProvider.GetBitmap(wx.ART_FILE_OPEN, 
        #    wx.ART_OTHER, (32,32)))

        self.list = wx.ListCtrl(self.remainingSpace, -1, 
            style= wx.LC_LIST 
                #| wx.LC_AUTOARRANGE
                #| wx.BORDER_SUNKEN
                | wx.BORDER_NONE

                #| wx.LC_EDIT_LABELS
                | wx.LC_SORT_ASCENDING
                #| wx.LC_NO_HEADER
                #| wx.LC_VRULES
                #| wx.LC_HRULES
                #| wx.LC_SINGLE_SEL
            )

        self.lcBox.Add(self.list, 1, wx.ALL|wx.GROW, 1)
        #self.list.SetColumnWidth(width = 0, col = 50)
        #self.list.SetColumnWidth(width = 1, col = 50)
        #self.list.SetColumnWidth(width = 2, col = 50)


        #self.list.SetImageList(il, wx.IMAGE_LIST_SMALL)
        #self.list.AssignImageList(il, wx.IMAGE_LIST_SMALL)


        #self.treeItemOnOpen(None)

        #self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.listItemOnSelChanged, self.list)
        #self.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.listItemDeselected, self.list)
        #self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.listItemOnOpen, self.list)
        #self.Bind(wx.EVT_LIST_END_LABEL_EDIT, self.listEndLabelEdit, self.list)

        #self.list.Bind(wx.EVT_RIGHT_UP, self.listItemOnMenu)



    def createGitField1(self):
        
        self.main_field = MixinListCtrlPanel(self.remainingSpace, self, self.log)
        self.lcBox.Add(self.main_field, 1, wx.ALL|wx.GROW, 1)
        self.list = self.main_field.list
        self.showFolderItems = self.main_field.showFolderItems
        self.showFolderItems1 = self.main_field.showFolderItems1

    def OnSashDrag(self, event):
        if event.GetDragStatus() == wx.SASH_STATUS_OUT_OF_RANGE:
            self.log.write('drag is out of range')
            return

        eobj = event.GetEventObject()

        if eobj is self.leftWindow:
            #self.log.write('leftwin received drag event\n')
            self.leftWindow.SetDefaultSize((event.GetDragRect().width, 2000))

        elif eobj is self.bottomWindow:
            #self.log.write('bottomwin received drag event\n')
            self.bottomWindow.SetDefaultSize((1000, event.GetDragRect().height))

        wx.LayoutAlgorithm().LayoutWindow(self, self.remainingSpace)
        self.remainingSpace.Refresh()
        


    def OnSize(self, event):
        wx.LayoutAlgorithm().LayoutWindow(self, self.remainingSpace)





    def treeItemOnOpen(self, event):

        #self.log.write("On open\n")
        self.list.DeleteAllItems()
        self.listItems = {}
        
        self.currentItem = None
        self.current_sel_dir = None

        self.is_git_dir = self.gitRepo.is_in_git_repo(self.current_dir)
        if self.is_git_dir:
            self.gitRepo.update_status()
        self.showFolderItems1(self.current_dir)

        #print self.listItems




    def treeItemOnSelChanged(self, event):

        p = self.dir.GetPath()
        if os.path.isdir(p):
            self.current_dir = p
            self.current_file = None

            #event.Skip()

        else:

            self.current_file = p
            self.current_dir = os.path.dirname(p)

        self.log.write( self.current_dir + '\n' )

        self.treeItemOnOpen(None)



    def treeItemOnMenu(self, event):

        self.log.write("OnContextMenu")

        # only do this part the first time so the events are only bound once
        #
        # Yet another anternate way to do IDs. Some prefer them up top to
        # avoid clutter, some prefer them close to the object of interest
        # for clarity. 

        if self.current_file == None:
            self.popupID_init = wx.NewId()


            # make a menu
            menu = wx.Menu()
            # add some items
            menu.Append(self.popupID_init, "init here")

        #else:


        self.popupID_commit = wx.NewId()
        #self.Bind(wx.EVT_MENU, self.OnPopupOne, id=self.popupID1)
        menu.Append(self.popupID_commit, "commit")

        # Popup the menu.  If an item is selected then its handler
        # will be called before PopupMenu returns.
        self.PopupMenu(menu)
        menu.Destroy()






