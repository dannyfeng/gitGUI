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


import git_repo
import cmds
#import ctrl
from mainWindow import mainSashWindow

#---------------------------------------------------------------------------
TBFLAGS = ( wx.TB_HORIZONTAL
            | wx.NO_BORDER
            | wx.TB_FLAT
            #| wx.TB_TEXT
            #| wx.TB_HORZ_LAYOUT
            )

#---------------------------------------------------------------------------


#---------------------------------------------------------------------------




#---------------------------------------------------------------------------


#---------------------------------------------------------------------------
class CommentsFrame(wx.MiniFrame):

    def __init__(
        self, parent, title, log, pos=wx.DefaultPosition, size=wx.DefaultSize,
        style=wx.DEFAULT_FRAME_STYLE 
        ):

        wx.MiniFrame.__init__(self, parent, -1, title, pos, size, style)
        self.parent = parent
        self.log = log
        panel = wx.Panel(self, -1)

        self.Bind(wx.EVT_CLOSE, self.OnCloseWindow)


        ed = editor.Editor(panel, -1, style=wx.SUNKEN_BORDER)
        self.ed = ed
        box = wx.BoxSizer(wx.VERTICAL)
        box.Add(ed, 1, wx.ALL|wx.GROW, 1)
        panel.SetSizer(box)
        panel.SetAutoLayout(True)

        ed.SetText(["Add your committing comments here!"])



    def OnCloseWindow(self, event):
        comments = self.ed.GetText()

        cmmts = ''
        for line in comments:
            cmmts = cmmts + line + '\n'
        self.log.write(cmmts)
        self.parent.comments = cmmts

        self.Destroy()
#---------------------------------------------------------------------------



#---------------------------------------------------------------------------

class LogSearchCtrl(wx.SearchCtrl):
    maxSearches = 5
    
    def __init__(self, parent, id=-1, value="",
                 pos=wx.DefaultPosition, size=wx.DefaultSize, style=0,
                 doSearch=None):
        style |= wx.TE_PROCESS_ENTER
        wx.SearchCtrl.__init__(self, parent, id, value, pos, size, style)
        self.Bind(wx.EVT_TEXT_ENTER, self.OnTextEntered)
        self.Bind(wx.EVT_MENU_RANGE, self.OnMenuItem, id=1, id2=self.maxSearches)
        self.doSearch = doSearch
        self.searches = []

    def OnTextEntered(self, evt):
        text = self.GetValue()
        if self.doSearch(text):
            self.searches.append(text)
            if len(self.searches) > self.maxSearches:
                del self.searches[0]
            self.SetMenu(self.MakeMenu())
        self.SetValue("")

    def OnMenuItem(self, evt):
        text = self.searches[evt.GetId()-1]
        self.doSearch(text)
        
    def MakeMenu(self):
        menu = wx.Menu()
        item = menu.Append(-1, "Recent Searches")
        item.Enable(False)
        for idx, txt in enumerate(self.searches):
            menu.Append(1+idx, txt)
        return menu

#---------------------------------------------------------------------------



#---------------------------------------------------------------------------

class CustomStatusBar(wx.StatusBar):
    def __init__(self, parent, log):
        wx.StatusBar.__init__(self, parent, -1)

        # This status bar has three fields
        self.SetFieldsCount(3)
        # Sets the three fields to be relative widths to each other.
        self.SetStatusWidths([-3, -1, -2])
        self.log = log

        # Field 0 ... just text
        #self.SetStatusText("A Custom StatusBar...", 0)

        # We're going to use a timer to drive a 'clock' in the last
        # field.
        self.timer = wx.PyTimer(self.Notify)
        self.timer.Start(1000)
        self.Notify()

    # Handles events from the timer we started in __init__().
    # We're using it to drive a 'clock' in field 2 (the third field).
    def Notify(self):
        t = time.localtime(time.time())
        st = time.strftime("%d-%b-%Y   %H:%M:%S", t)
        self.SetStatusText(st, 2)
        #self.log.write("tick...\n")

#---------------------------------------------------------------------------






























#---------------------------------------------------------------------------

#---------------------------------------------------------------------------
class GitFrame(wx.Frame):
    """Git frame."""
    def __init__(self, parent, id):
        wx.Frame.__init__(self, parent, id, 'GIT', wx.DefaultPosition, 
            wx.Size(900, 640))
        self.top_panel = wx.Panel(self, -1)
        #self.middle_panel = wx.Panel(self, -1)
        self.bottom_panel = wx.Panel(self, -1)

        #our git repo
        self.gitRepo = git_repo.model()
        #self.gitCtrl = ctrl.Controller(self.gitRepo)
                
        self.Bind(wx.EVT_CLOSE, self.OnCloseWindow)
        self.createMenuBar1()
        #self.CreateStatusBar()
        self.createStatusBar1()



        self.git_box = wx.FlexGridSizer(3,1)
        #self.git_box = wx.BoxSizer(wx.VERTICAL)

        self.top_panel_box = wx.BoxSizer( wx.HORIZONTAL )
        #self.middle_field_box = wx.BoxSizer(wx.HORIZONTAL)
        self.bottom_tool_box = wx.BoxSizer(wx.HORIZONTAL)
        self.statusBar_box = wx.BoxSizer(wx.HORIZONTAL)





        self.createToolbar()
        self.createButtons()
        self.createField()
        self.createBottomBar()
        #self.createStatusBar()


        self.git_box.AddMany([(self.top_panel), (self.win, 1, wx.EXPAND), 
            (self.bottom_panel)])

        self.git_box.AddGrowableRow(1, 1)
        self.git_box.AddGrowableCol(0, 1)

        self.top_panel.SetSizer(self.top_panel_box)
        self.bottom_panel.SetSizer(self.bottom_tool_box)

        self.SetSizer(self.git_box)




        
        
        
        
    def menuData(self):
        return (("文件(&F)",
                    ("新建(&N)", "New file", self.OnTest),
                    ("打开(&O)", "Open a file", self.OnOpen),
                    ("", "", ""),
                    ("退出(&Q)", "Quit", self.OnCloseWindow)),
                ("编辑(&E)",
                    ("复制(&C)", "Copy", self.OnCopy),
                    ("剪切(&u)", "Cut", self.OnCut),
                    ("粘贴(&P)", "Paste", self.OnPaste),
                    ("", "", ""),
                    ("选项...(&O)", "DisplayOptions", self.OnOptions)),
                ("命令(&C)",
                    ("Tag...(&T)", "Tag", self.OnCopy
                        #('New...(&N)', '新建tag', self.OnOpen)
                        ),
                        
                    ("", "", ""),
                    ("Branch...(&B)", "Branch", self.OnCut),
                    ("Status...(&S)", "Status", self.OnPaste),
                    ("Merge...(&M)", "Paste", self.OnPaste),
                    ("Log...(&L)", "Log", self.OnOptions)),
                ("工具(&T)",
                    ("源码路径(&P)", "Source code path", self.OnCopy),
                    ("", "", ""),

                    ("邮件(&M)", "Mail", self.OnMail),
                    ("选项...(&O)", "Options", self.OnOptions)),
                ("帮助(&H)",
                    #("复制(&C)", "Copy", self.OnCopy),
                    #("剪切(&u)", "Cut", self.OnCut),
                    #("粘贴(&P)", "Paste", self.OnPaste),
                    #("", "", ""),
                    ("关于(&A)", "About", self.OnOptions)))
                    
    def createMenuBar(self):
        menuBar = wx.MenuBar()
        for eachMenuData in self.menuData():
            menuLabel = eachMenuData[0]
            menuItems = eachMenuData[1:]
            menuBar.Append(self.createMenu(menuItems), menuLabel)
        self.SetMenuBar(menuBar)

    def createMenu(self, menuData):
        menu = wx.Menu()
        for eachLabel, eachStatus, eachHandler in menuData:
            if not eachLabel:
                menu.AppendSeparator()
                continue
            menuItem = menu.Append(-1, eachLabel, eachStatus)
            self.Bind(wx.EVT_MENU, eachHandler, menuItem)
        return menu

    def createSubmenu(self, menuData):
        menu = wx.Menu()
        for eachLabel, eachStatus, eachHandler in menuData:
            if not eachLabel:
                menu.AppendSeparator()
                continue
            menuItem = menu.Append(-1, eachLabel, eachStatus)
            self.Bind(wx.EVT_MENU, eachHandler, menuItem)
        return menu












    def createMenuBar1(self):

        # Prepare the menu bar
        menuBar = wx.MenuBar()

        # 1st menu from left
        menu1 = wx.Menu()
        menu1.Append(101, "新建(&N)", "New file")
        menu1.Append(102, "打开(&O)", "Open a file")
        menu1.AppendSeparator()
        menu1.Append(103, "退出(&Q)\tCtrl+Q", "Quit")
        # Add menu to the menu bar
        menuBar.Append(menu1, "文件(&F)")


        # 2nd menu from left
        menu2 = wx.Menu()
        menu2.Append(201, "复制(&C)", "Copy")
        menu2.Append(202, "剪切(&u)", "Cut")
        menu2.Append(203, "粘贴(&P)", "Paste")
        # Append 2nd menu
        menuBar.Append(menu2, "编辑(&E)")




        menu3 = wx.Menu()
        #menu3.Append(301, "Tag...(&T)", "Tag")
        subTag = wx.Menu()
        subTag.Append(3011, 'New...(&N)', 'New tag')
        subTag.Append(3012, 'List...(&L)', 'List all tags')
        menu3.AppendMenu(301, "Tags...(&T)", subTag)
        
        menu3.AppendSeparator()

        menu3.Append(302, "Merge...(&M)", "Merge")
        
        #menu3.Append(303, "Branch...(&B)", "Branch")
        subBranch = wx.Menu()
        subBranch.Append(3031, 'New...(&N)', 'New branch')
        subBranch.Append(3032, 'List...(&L)', 'List all branchs')
        menu3.AppendMenu(303, "Branch...(&B)", subBranch)

        #menu3.Append(304, "Log...(&L)", "Log")
        subLog = wx.Menu()
        subLog.Append(3041, 'Show All(&A)', 'Show all logs')
        subLog.Append(3042, 'Show Latest(&L)', 'Show lastest log')
        subLog.Append(3043, 'gitK...(&K)', 'Open gitk tool')
        menu3.AppendMenu(304, 'Log...(&L)', subLog)

        menuBar.Append(menu3, "命令(&C)")


        menu4 = wx.Menu()
        # Check menu items
        menu4.Append(401, "源码路径(&P)\tCtrl+P", "Go to source code path")
        menu4.AppendSeparator()
        menu4.Append(402, "邮件(&M)", "Mail")
        menu4.Append(403, "选项...(&O)", "Options")
        menuBar.Append(menu4, "工具(&T)")


        menu5 = wx.Menu()
        # Shortcuts
        menu5.Append(501, "关于(&A)\tCtrl+A", "About")
        menuBar.Append(menu5, "帮助(&H)")


        self.SetMenuBar(menuBar)


        # Menu events
        #self.Bind(wx.EVT_MENU, self.OnAddComments, id=101)
        #self.Bind(wx.EVT_MENU, self.Menu102, id=102)
        self.Bind(wx.EVT_MENU, self.OnCloseWindow, id=103)


        #self.Bind(wx.EVT_MENU, self.Menu201, id=201)
        #self.Bind(wx.EVT_MENU, self.Menu202, id=202)
        #self.Bind(wx.EVT_MENU, self.Menu2031, id=203)


        self.Bind(wx.EVT_MENU, self.OnGitAddTag, id=3011)
        self.Bind(wx.EVT_MENU, self.OnGitAddBranch, id=3031)
        self.Bind(wx.EVT_MENU, self.OnGitLog, id=3041)
        self.Bind(wx.EVT_MENU, self.OnGitLogLast, id=3042)
        self.Bind(wx.EVT_MENU, self.OnGitK, id=3043)


        self.Bind(wx.EVT_MENU, self.OnGo2Path, id=401)
        #self.Bind(wx.EVT_MENU, self.OnMail, id=402)

        self.Bind(wx.EVT_MENU, self.Menu501, id=501)




    def OnGo2Path(self, event):

        p = self.TextEntry('Enter your source code path', 'Go 2 path', '/')

        if p == -1:
            self.log.write('Cancled')
        else:
            if os.path.exists(p):
                if os.path.isdir(p):
                    self.win.current_sel_dir = self.win.current_dir = p + '/'
                    self.win.current_file = None
                else:
                    self.win.current_file = p
                    self.win.current_sel_dir = self.win.current_dir = os.path.dirname(p) + '/'
                    
                self.win.treeItemOnOpen(None)
                #self.log.write(self.win.current_dir)
            else:
                self.log.write('Path not exists')


    def Menu501(self, event):
        self.log.write('Look in the code how the shortcut has been realized')










    def createStatusBar(self):
        self.sb = CustomStatusBar(self, self.log)
        self.statusBar_box.Add(self.sb, 1, wx.EXPAND)

    def createStatusBar1(self): # 比上面那种方法好
    
        self.sb = self.CreateStatusBar()
        
        # This status bar has three fields
        self.sb.SetFieldsCount(3)
        # Sets the three fields to be relative widths to each other.
        self.sb.SetStatusWidths([-3, -1, -2])

        # Field 0 ... just text
        #self.sb.SetStatusText("A Custom StatusBar...", 0)

        # We're going to use a timer to drive a 'clock' in the last field.
        self.timer = wx.PyTimer(self.Notify)
        self.timer.Start(1000)
        self.Notify()

    # We're using it to drive a 'clock' in field 2 (the third field).
    def Notify(self):
        t = time.localtime(time.time())
        st = time.strftime("%d-%b-%Y   %I:%M:%S", t)
        self.sb.SetStatusText(st, 2)



    def createToolbar(self):
        
        tb = wx.ToolBar(self.top_panel, style=TBFLAGS)
        
        self.tb = tb
        self.top_panel_box.Add(self.tb, 1, wx.EXPAND)


        tsize = (24,24)
        new_bmp =  wx.ArtProvider.GetBitmap(wx.ART_NEW, wx.ART_TOOLBAR, tsize)
        undo_bmp = wx.ArtProvider.GetBitmap(wx.ART_UNDO, wx.ART_TOOLBAR, tsize)
        redo_bmp = wx.ArtProvider.GetBitmap(wx.ART_REDO, wx.ART_TOOLBAR, tsize)
        go_back_bmp= wx.ArtProvider.GetBitmap(wx.ART_GO_BACK, wx.ART_TOOLBAR, tsize)
        go_to_parent_bmp = wx.ArtProvider.GetBitmap(wx.ART_GO_TO_PARENT, wx.ART_TOOLBAR, tsize)

        tb.SetToolBitmapSize(tsize)
        
        #tb.AddSimpleTool(10, new_bmp, "New", "Long help for 'New'")
        tb.AddLabelTool(10, "New", new_bmp, shortHelp="New", 
            longHelp="Add a new file to current folder")
        self.Bind(wx.EVT_TOOL, self.OnAddComments, id=10)
        #self.Bind(wx.EVT_TOOL_RCLICKED, self.OnOptions, id=10)

        tb.AddSeparator()

        #tb.AddSimpleTool(20, open_bmp, "Open", "Long help for 'Open'")
        tb.AddLabelTool(20, "Undo", undo_bmp, shortHelp="Undo", 
            longHelp="Undo your git command")
        self.Bind(wx.EVT_TOOL, self.OnOptions, id=20)
        #self.Bind(wx.EVT_TOOL_RCLICKED, self.OnOptions, id=20)


        tb.AddLabelTool(30, "Redo", redo_bmp, shortHelp="Redo", 
            longHelp="Redo your git command")
        self.Bind(wx.EVT_TOOL, self.OnOptions, id=30)
        #self.Bind(wx.EVT_TOOL_RCLICKED, self.OnOptions, id=30)

        tb.AddSeparator()

        tb.AddLabelTool(40, "Back", go_back_bmp, shortHelp="Back", 
            longHelp="Go back last dir")
        self.Bind(wx.EVT_TOOL, self.toolOnGoBack, id=40)


        tb.AddLabelTool(50, "Up", go_to_parent_bmp, shortHelp="Go 2 ../", 
            longHelp="Go up to parent dir")
        self.Bind(wx.EVT_TOOL, self.toolOnGoParentDir, id=50)

        #tb.AddTool(60, "Go 2 ../")

        tb.AddSeparator()

        cbID = wx.NewId()
        tb.AddControl(
            wx.ComboBox(
                tb, cbID, "", choices=["", "This", "is a", "wx.ComboBox"],
                size=(150,-1), style=wx.CB_DROPDOWN
                ))
        self.Bind(wx.EVT_COMBOBOX, self.OnOptions, id=cbID)


        tb.Realize()


    def buttonData(self):
        return (#("新建", self.OnFirst),

                ("Add", self.OnGitAdd),
                ("Rm", self.OnGitRm),
                ("", ""),
                ("Diff", self.OnGitDiff),
                ("", ""),
                ("Commit", self.OnGitCommit))

    def createButtons(self):

        for eachLabel, eachHandler in self.buttonData():
            if not eachLabel:
                self.top_panel_box.AddSpacer(20, 50)
                continue

            button = self.buildOneButton(self.top_panel, eachLabel, eachHandler)
            self.top_panel_box.Add(button, 0, wx.EXPAND, 60)


    def buildOneButton(self, parent, label, handler, pos=(0,0)):
        button = wx.Button(parent, -1, label, pos)

        self.Bind(wx.EVT_BUTTON, handler, button)
        return button



    def createField(self):
        self.win = mainSashWindow(self)
        #self.middle_field_box.Add(self.win, 1, wx.EXPAND)
        self.log = self.win.log

    def createBottomBar(self):
        
        tb = wx.ToolBar(self.bottom_panel, style=TBFLAGS)
        
        self.bottom_bar = tb
        self.bottom_tool_box.Add(self.bottom_bar, 0, wx.EXPAND)


        tsize = (14,14)
        new_bmp =  wx.ArtProvider.GetBitmap(wx.ART_NEW, wx.ART_TOOLBAR, tsize)
        #open_bmp = wx.ArtProvider.GetBitmap(wx.ART_FILE_OPEN, wx.ART_TOOLBAR, tsize)
        #copy_bmp = wx.ArtProvider.GetBitmap(wx.ART_COPY, wx.ART_TOOLBAR, tsize)
        #paste_bmp= wx.ArtProvider.GetBitmap(wx.ART_PASTE, wx.ART_TOOLBAR, tsize)

        tb.SetToolBitmapSize(tsize)
        
        #tb.AddSimpleTool(1, new_bmp, "New", "Long help for 'New'")
        tb.AddLabelTool(1, "Clear", new_bmp, shortHelp="Clear", 
            longHelp="Clear logs in log window")
        self.Bind(wx.EVT_TOOL, self.OnLogClear, id=1)
        #self.Bind(wx.EVT_TOOL_RCLICKED, self.OnOptions, id=1)



        tb.AddSeparator()


       
        tb.AddSeparator()
        search = LogSearchCtrl(tb, size=(150,-1), doSearch=self.DoSearch)
        tb.AddControl(search)

        # Final thing to do for a toolbar is call the Realize() method. This
        # causes it to render (more or less, that is).
        tb.Realize()



    def TextEntry(self, note, title, context): 

        dlg = wx.TextEntryDialog(
                self, note,
                title, context)

        #dlg.SetValue("Python is the best!")

        if dlg.ShowModal() == wx.ID_OK:
            text = dlg.GetValue()
            self.log.write('You entered: %s' % text)
            dlg.Destroy()
            return text

        dlg.Destroy()
        return -1
        
    #---------------------------------------------------------------------------
    # Just grouping the empty event handlers together
    def OnTest(self, event):
        p1 = subprocess.Popen(["ls"], stdout=subprocess.PIPE)
        p2 = subprocess.Popen(["grep", "git*"], stdin=p1.stdout, 
	        stdout=subprocess.PIPE)

        output = p2.communicate()[0]
        self.log.write(output)


    def OnNew(self, event): pass
    def OnOpen(self, event): pass
    def OnCopy(self, event): pass
    def OnCut(self, event): pass
    def OnPaste(self, event): pass
    def OnOptions(self, event): pass



    def toolOnGoBack(self, event):
        self.win.treeItemOnOpen(None)
        pass

    def toolOnGoParentDir(self, event):
        self.win.current_dir = os.path.dirname(self.win.current_dir)
        self.win.treeItemOnOpen(None)
        pass


    def OnGitAdd(self, event):
        if self.win.current_sel_dir == None:
            cmd = ['git', 'add', '.']
            self.gitRepo.gitProcess(cmd, self.win.current_dir)

        elif self.win.current_file == None:
            cmd = ['git', 'add', os.path.basename(self.win.current_sel_dir)]
            self.gitRepo.gitProcess(cmd, self.win.current_dir)
        else: # 或者采用OnGitRm()的方法
            cmd = ['git', 'add', self.win.current_file]
            self.gitRepo.gitProcess(cmd, self.win.current_dir)


    def OnGitRm(self, event):
        if self.win.current_sel_dir == None:
            self.log.write('Nothing to do, select one item first!')
        else:
            cmd = ['git', 'rm', '-r', self.win.list.GetItemText(self.win.currentItem)]
            self.gitRepo.gitProcess(cmd, self.win.current_dir)




    def OnGitDiff(self, event):
        if self.win.current_sel_dir == None:
            cmd = ['git', 'diff']
        else:
            cmd = ['git', 'diff', self.win.list.GetItemText(self.win.currentItem)]

        self.gitRepo.gitProcess(cmd, self.win.current_dir)


    def OnGitCommit(self, event):

        cmmts = self.OnAddComments(None)
        
        cmd = ['git', 'commit', '-m', cmmts]

        self.gitRepo.gitProcess(cmd, self.win.current_dir)



    def OnGitLog(self, event):
        cmd = ['git', 'log']
        
        self.gitRepo.gitProcess(cmd, self.win.current_dir)

    def OnGitLogLast(self, event):
        cmd = ['git', 'log', '-p', '-2']
        
        self.gitRepo.gitProcess(cmd, self.win.current_dir)

    def OnGitK(self, event):
        cmd = ['gitk']
        
        self.gitRepo.gitProcess(cmd, self.win.current_dir)


    def OnGitAddTag(self, event):

        tag = self.TextEntry('Enter new tag name', 'New tag')

        if tag == -1:
            self.log.write('Cancled')
        else:
            cmd = ['git', 'tag', tag]
            self.gitRepo.gitProcess(['git', 'tag', tag], self.win.current_dir)


    def OnGitAddBranch(self, event):

        branchName = self.TextEntry('Enter new branch name', 'New branch')

        if branchName == -1:
            self.log.write('Cancled')
        else:
            self.gitRepo.branch(branchName, self.win.current_dir)



    def OnAddComments(self, event):
        frame = CommentsFrame(self, 'Add Comments', self.log)
        frame.Show()
        self.comments = frame.ed.GetText()

        cmmts = ''
        for line in self.comments:
            cmmts = cmmts + line + '\n'
        self.log.write(cmmts)

        return cmmts


    def DoSearch(self,  text):
        # called by TestSearchCtrl
        self.log.write("DoSearch: %s" % text)

        log = self.log.GetValue()
        self.log.SetStyle(0, len(log), wx.TextAttr("BLACK", "WHITE"))

        i = 0
        while i <= len(log)-len(text): 
        
            if text == log[i:(i+len(text))]: 
                self.log.SetStyle(i, i+len(text), wx.TextAttr("RED", "YELLOW"))
                
            i += 1


        # return true to tell the search ctrl to remember the text
        return True


    def OnLogClear(self, event):
        self.log.SetValue("Log cleared...\n")
        
    def OnMail(self, event):
        frame = GitGui()
        frame.Show()
        self.Close()
        
    def OnCloseWindow(self, event):
        self.Destroy()

    #---------------------------------------------------------------------------

#---------------------------------------------------------------------------




