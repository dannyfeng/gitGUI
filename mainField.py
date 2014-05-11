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
import  wx.lib.mixins.listctrl  as  listmix

import core
import utils
import gitcmds
import controller
import ctrl
import signals

import git_repo
#---------------------------------------------------------------------------


#---------------------------------------------------------------------------

class MixinListCtrl(wx.ListCtrl, listmix.ListCtrlAutoWidthMixin):
    def __init__(self, parent, ID, pos=wx.DefaultPosition,
                 size=wx.DefaultSize, style=0):
        wx.ListCtrl.__init__(self, parent, ID, pos, size, style)
        listmix.ListCtrlAutoWidthMixin.__init__(self)

#---------------------------------------------------------------------------

#---------------------------------------------------------------------------
class MixinListCtrlPanel(wx.Panel, listmix.ColumnSorterMixin):
    def __init__(self, parent, mainWin, log):
        wx.Panel.__init__(self, parent, -1, style=wx.WANTS_CHARS)

        self.log = log
        self.win = mainWin
        self.gitFrame = mainWin.parent
        self.gitRepo = mainWin.gitRepo #mainWin.parent.gitRepo
        self.gitCtrl = ctrl.Controller(self.gitRepo)
        
        tID = wx.NewId()

        sizer = wx.BoxSizer(wx.VERTICAL)


            
        self.il = wx.ImageList(28, 28)
        
        self.sm_up = self.il.Add(wx.ArtProvider.GetBitmap(wx.ART_GO_UP, wx.ART_OTHER, (28,28)))
        self.sm_dn = self.il.Add(wx.ArtProvider.GetBitmap(wx.ART_GO_UP, wx.ART_OTHER, (28,28)))

        self.fileidx = self.il.Add(wx.ArtProvider.GetBitmap(wx.ART_NORMAL_FILE, wx.ART_OTHER, (28,28)))
        self.fldridx = self.il.Add(wx.ArtProvider.GetBitmap(wx.ART_FOLDER, wx.ART_OTHER, (28,28)))
        self.fldropenidx = self.il.Add(wx.ArtProvider.GetBitmap(wx.ART_FILE_OPEN, wx.ART_OTHER, (28,28)))

        self.untrackedidx = self.il.Add(wx.ArtProvider.GetBitmap(wx.ART_GO_UP, wx.ART_OTHER, (28,28)))
        self.modifiedidx = self.il.Add(wx.ArtProvider.GetBitmap(wx.ART_GO_DOWN, wx.ART_OTHER, (28,28)))
        self.stagedidx = self.il.Add(wx.ArtProvider.GetBitmap(wx.ART_GO_BACK, wx.ART_OTHER, (28,28)))
        self.unmergedidx = self.il.Add(wx.ArtProvider.GetBitmap(wx.ART_GO_FORWARD, wx.ART_OTHER, (28,28)))
        self.commitedidx = self.il.Add(wx.ArtProvider.GetBitmap(wx.ART_NEW, wx.ART_OTHER, (28,28)))


        self.list = MixinListCtrl(self, tID,
                                 style=wx.LC_REPORT 
                                 #| wx.BORDER_SUNKEN
                                 | wx.BORDER_NONE
                                 #| wx.LC_EDIT_LABELS
                                 | wx.LC_SORT_ASCENDING
                                 #| wx.LC_NO_HEADER
                                 #| wx.LC_VRULES
                                 #| wx.LC_HRULES
                                 #| wx.LC_SINGLE_SEL
                                 )
        
        self.list.SetImageList(self.il, wx.IMAGE_LIST_SMALL)
        sizer.Add(self.list, 1, wx.EXPAND)

        self.PopulateList()

        # Now that the list exists we can init the other base class,
        # see wx/lib/mixins/listctrl.py
        self.itemDataMap = self.win.listItems
        listmix.ColumnSorterMixin.__init__(self, 4)
        self.SortListItems(0, True)

        self.SetSizer(sizer)
        self.SetAutoLayout(True)

        '''
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnItemSelected, self.list)
        self.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.OnItemDeselected, self.list)
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnItemActivated, self.list)
        self.Bind(wx.EVT_LIST_DELETE_ITEM, self.OnItemDelete, self.list)
        self.Bind(wx.EVT_LIST_BEGIN_LABEL_EDIT, self.OnBeginEdit, self.list)

        self.list.Bind(wx.EVT_LEFT_DCLICK, self.OnDoubleClick)
        self.list.Bind(wx.EVT_RIGHT_DOWN, self.OnRightDown)

        # for wxMSW
        self.list.Bind(wx.EVT_COMMAND_RIGHT_CLICK, self.OnRightClick)

        # for wxGTK
        self.list.Bind(wx.EVT_RIGHT_UP, self.OnRightClick)
        '''

        self.Bind(wx.EVT_LIST_COL_CLICK, self.OnColClick, self.list)
        self.Bind(wx.EVT_LIST_COL_RIGHT_CLICK, self.OnColRightClick, self.list)
        self.Bind(wx.EVT_LIST_COL_BEGIN_DRAG, self.OnColBeginDrag, self.list)
        self.Bind(wx.EVT_LIST_COL_DRAGGING, self.OnColDragging, self.list)
        self.Bind(wx.EVT_LIST_COL_END_DRAG, self.OnColEndDrag, self.list)


        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.listItemOnSelChanged, self.list)
        self.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.listItemDeselected, self.list)
        self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.listItemOnOpen, self.list)
        self.Bind(wx.EVT_LIST_END_LABEL_EDIT, self.listEndLabelEdit, self.list)

        self.list.Bind(wx.EVT_RIGHT_UP, self.listItemOnMenu)




    def PopulateList(self):

        # but since we want images on the column header we have to do it the hard way:
        info = wx.ListItem()
        info.m_mask = wx.LIST_MASK_TEXT | wx.LIST_MASK_IMAGE | wx.LIST_MASK_FORMAT
        info.m_image = -1
        info.m_format = 0
        info.m_text = "名称"
        self.list.InsertColumnInfo(0, info)

        info.m_format = wx.LIST_FORMAT_RIGHT
        info.m_text = "大小"
        self.list.InsertColumnInfo(1, info)

        info.m_format = 0
        info.m_text = "类型"
        self.list.InsertColumnInfo(2, info)

        info.m_format = 0
        info.m_text = "修改时间"
        self.list.InsertColumnInfo(3, info)


        self.showFolderItems(self.win.current_dir)

        self.list.SetColumnWidth(0, 300)
        self.list.SetColumnWidth(1, 60)
        self.list.SetColumnWidth(2, 100)
        self.list.SetColumnWidth(3, wx.LIST_AUTOSIZE)

        self.currentItem = None



    # Used by the ColumnSorterMixin, see wx/lib/mixins/listctrl.py
    def GetListCtrl(self):
        return self.list

    # Used by the ColumnSorterMixin, see wx/lib/mixins/listctrl.py
    def GetSortImages(self):
        return (self.sm_dn, self.sm_up)


    def OnRightDown(self, event):
        x = event.GetX()
        y = event.GetY()
        self.log.WriteText("x, y = %s\n" % str((x, y)))
        item, flags = self.list.HitTest((x, y))

        if item != wx.NOT_FOUND and flags & wx.LIST_HITTEST_ONITEM:
            self.list.Select(item)

        event.Skip()


    def getColumnText(self, index, col):
        item = self.list.GetItem(index, col)
        return item.GetText()


    def OnItemSelected(self, event):
        ##print event.GetItem().GetTextColour()
        self.currentItem = event.m_itemIndex
        self.log.write("OnItemSelected: %s, %s, %s, %s" %
                           (self.currentItem,
                            self.list.GetItemText(self.currentItem),
                            self.getColumnText(self.currentItem, 1),
                            self.getColumnText(self.currentItem, 2)))

        if self.currentItem == 10:
            self.log.write("OnItemSelected: Veto'd selection")
            #event.Veto()  # doesn't work
            # this does
            self.list.SetItemState(10, 0, wx.LIST_STATE_SELECTED)

        event.Skip()


    def OnItemDeselected(self, evt):
        item = evt.GetItem()
        self.log.write("OnItemDeselected: %d" % evt.m_itemIndex)

        # Show how to reselect something we don't want deselected
        if evt.m_itemIndex == 11:
            wx.CallAfter(self.list.SetItemState, 11, wx.LIST_STATE_SELECTED, wx.LIST_STATE_SELECTED)


    def OnItemActivated(self, event):
        self.currentItem = event.m_itemIndex
        self.log.WriteText("OnItemActivated: %s\nTopItem: %s" %
                           (self.list.GetItemText(self.currentItem), self.list.GetTopItem()))

    def OnBeginEdit(self, event):
        self.log.WriteText("OnBeginEdit")
        event.Allow()

    def OnItemDelete(self, event):
        self.log.WriteText("OnItemDelete\n")

    def OnColClick(self, event):
        self.log.WriteText("OnColClick: %d\n" % event.GetColumn())
        event.Skip()

    def OnColRightClick(self, event):
        item = self.list.GetColumn(event.GetColumn())
        self.log.WriteText("OnColRightClick: %d %s\n" %
                           (event.GetColumn(), (item.GetText(), item.GetAlign(),
                                                item.GetWidth(), item.GetImage())))

    def OnColBeginDrag(self, event):
        self.log.WriteText("OnColBeginDrag\n")
        ## Show how to not allow a column to be resized
        #if event.GetColumn() == 0:
        #    event.Veto()


    def OnColDragging(self, event):
        self.log.WriteText("OnColDragging\n")

    def OnColEndDrag(self, event):
        self.log.WriteText("OnColEndDrag\n")

    def OnDoubleClick(self, event):
        self.log.WriteText("OnDoubleClick item %s\n" % self.list.GetItemText(self.currentItem))
        event.Skip()

    def OnRightClick(self, event):
        self.log.WriteText("OnRightClick %s\n" % self.list.GetItemText(self.currentItem))

        # only do this part the first time so the events are only bound once
        if not hasattr(self, "popupID1"):
            self.popupID1 = wx.NewId()
            self.popupID2 = wx.NewId()
            self.popupID3 = wx.NewId()
            self.popupID4 = wx.NewId()
            self.popupID5 = wx.NewId()
            self.popupID6 = wx.NewId()

            self.Bind(wx.EVT_MENU, self.OnPopupOne, id=self.popupID1)
            self.Bind(wx.EVT_MENU, self.OnPopupTwo, id=self.popupID2)
            self.Bind(wx.EVT_MENU, self.OnPopupThree, id=self.popupID3)
            self.Bind(wx.EVT_MENU, self.OnPopupFour, id=self.popupID4)
            self.Bind(wx.EVT_MENU, self.OnPopupFive, id=self.popupID5)
            self.Bind(wx.EVT_MENU, self.OnPopupSix, id=self.popupID6)

        # make a menu
        menu = wx.Menu()
        # add some items
        menu.Append(self.popupID1, "FindItem tests")
        menu.Append(self.popupID2, "Iterate Selected")
        menu.Append(self.popupID3, "ClearAll and repopulate")
        menu.Append(self.popupID4, "DeleteAllItems")
        menu.Append(self.popupID5, "GetItem")
        menu.Append(self.popupID6, "Edit")

        # Popup the menu.  If an item is selected then its handler
        # will be called before PopupMenu returns.
        self.PopupMenu(menu)
        menu.Destroy()


    def OnPopupOne(self, event):
        self.log.WriteText("Popup one\n")
        print "FindItem:", self.list.FindItem(-1, "Roxette")
        print "FindItemData:", self.list.FindItemData(-1, 11)

    def OnPopupTwo(self, event):
        self.log.WriteText("Selected items:\n")
        index = self.list.GetFirstSelected()

        while index != -1:
            self.log.WriteText("      %s: %s\n" % (self.list.GetItemText(index), self.getColumnText(index, 1)))
            index = self.list.GetNextSelected(index)

    def OnPopupThree(self, event):
        self.log.WriteText("Popup three\n")
        self.list.ClearAll()
        wx.CallAfter(self.PopulateList)

    def OnPopupFour(self, event):
        self.list.DeleteAllItems()

    def OnPopupFive(self, event):
        item = self.list.GetItem(self.currentItem)
        print item.m_text, item.m_itemId, self.list.GetItemData(self.currentItem)

    def OnPopupSix(self, event):
        self.list.EditLabel(self.currentItem)
    #---------------------------------------------------------------------------


    #---------------------------------------------------------------------------
    def showFolderItems(self, p):

        a = os.listdir(p)
        a.sort()

        for tmp in a:
            item = os.path.join(p, tmp)
            if os.path.isdir(item):
                if tmp[0] == '.':
                    pass
                    
                else:
                    if self.win.is_git_dir:
                        state_dict = gitcmds.specified_worktree_state_dict(head='HEAD', 
                            p=item[len(self.gitRepo.git.worktree()) + 1:])
                        is_clean = True
                        for v in state_dict.values():
                            if v:
                                is_clean = False
                                break

                        if is_clean:
                            self.listInsertOneItem(item, self.fldridx)
                        else:
                            self.listInsertOneItem(item, self.fldropenidx)
                    else:
                        self.listInsertOneItem(item, self.fldridx)

        for tmp in a:
            item = os.path.join(p, tmp)
            if os.path.isfile(item):
                if tmp[0] == '.':
                    pass
                    
                else:
                    if self.win.is_git_dir:
                        #self.gitRepo.update_status()
                        gitItem = item[len(self.gitRepo.git.worktree()) + 1:]
                        if core.encode(gitItem) in self.gitRepo.untracked:
                            self.listInsertOneItem(item, self.untrackedidx)
                            
                        elif core.encode(gitItem) in self.gitRepo.modified:
                            self.listInsertOneItem(item, self.modifiedidx)
                            
                        elif core.encode(gitItem) in self.gitRepo.staged:
                            self.listInsertOneItem(item, self.stagedidx)
                            
                        elif core.encode(gitItem) in self.gitRepo.unmerged:
                            self.listInsertOneItem(item, self.unmergedidx)
                            
                        else:
                            self.listInsertOneItem(item, self.commitedidx)
                            
                    else:
                        self.listInsertOneItem(item, self.fileidx)


    def showFolderItems1(self, p):

        a = os.listdir(p)
        a.sort()

        for tmp in a:
            item = os.path.join(p, tmp)
            if os.path.isdir(item):
                if tmp[0] == '.':
                    pass
                    
                else:
                    self.listInsertOneItem1(item, self.fldridx)

        for tmp in a:
            item = os.path.join(p, tmp)
            if os.path.isfile(item):
                if tmp[0] == '.':
                    pass
                    
                else:
                    self.listInsertOneItem1(item, self.fileidx)

    def listInsertOneItem1(self, pathName, imgIdx):
        """Return the status for the entry's path."""

        t = time.localtime(os.path.getmtime(pathName))
        st = time.strftime("%H:%M %d-%m-%Y", t)

        itemName = os.path.basename(pathName)
        itemAttr = [itemName, None, None, st, imgIdx]


        model = self.gitRepo
        unmerged = utils.add_parents(set(model.unmerged))
        modified = utils.add_parents(set(model.modified))
        staged = utils.add_parents(set(model.staged))
        untracked = utils.add_parents(set(model.untracked))
        upstream_changed = utils.add_parents(set(model.upstream_changed))

        if imgIdx == self.fldridx:
            itemAttr[1] = '<DIR>'
            itemAttr[2] = 'Dir'

            if self.win.is_git_dir:
            
                if itemName in unmerged:
                    itemAttr[4] = self.fldropenidx
                    
                elif itemName in modified and self.path in staged:
                    itemAttr[4] = self.fldropenidx
                    
                elif itemName in modified:
                    itemAttr[4] = self.fldropenidx
                    
                elif itemName in staged:
                    itemAttr[4] = self.fldropenidx
                    
                elif itemName in upstream_changed:
                    itemAttr[4] = self.fldropenidx
                            
                elif itemName in untracked:
                    itemAttr[4] = self.fldropenidx
                    
                else:
                    itemAttr[4] = self.fldridx
                    
        elif imgIdx == self.fileidx:
            itemAttr[1] = str(os.path.getsize(pathName)) + 'B'
            itemAttr[2] = os.path.splitext(pathName)[1][1:]

            if self.win.is_git_dir:
            
                if itemName in unmerged:
                    itemAttr[4] = self.unmergedidx
                    
                elif itemName in modified and itemName in staged:
                    itemAttr[4] = self.modifiedidx
                    
                elif itemName in modified:
                    itemAttr[4] = self.modifiedidx
                    
                elif itemName in staged:
                    itemAttr[4] = self.stagedidx
                    
                elif itemName in upstream_changed:
                    itemAttr[4] = self.modifiedidx
                            
                elif itemName in untracked:
                    itemAttr[4] = self.untrackedidx
                    
                else:
                    itemAttr[4] = self.commitedidx

        index = self.list.InsertImageStringItem(sys.maxint, itemAttr[0], itemAttr[4])
        self.list.SetStringItem(index, 1, itemAttr[1])
        self.list.SetStringItem(index, 2, itemAttr[2])
        self.list.SetStringItem(index, 3, itemAttr[3])

        self.win.listItems[index] = itemAttr



    def listInsertOneItem(self, pathName, imgIdx):
        
        t = time.localtime(os.path.getmtime(pathName))
        st = time.strftime("%H:%M %d-%m-%Y", t)

        itemAttr = [os.path.basename(pathName), None, None, st, imgIdx]
        if imgIdx == self.fldridx or imgIdx == self.fldropenidx:
            itemAttr[1] = '<DIR>'
            itemAttr[2] = 'Dir'
        else:
            itemAttr[1] = str(os.path.getsize(pathName)) + 'B'
            itemAttr[2] = os.path.splitext(pathName)[1][1:]
            
        index = self.list.InsertImageStringItem(sys.maxint, itemAttr[0], imgIdx)
        self.list.SetStringItem(index, 1, itemAttr[1])
        self.list.SetStringItem(index, 2, itemAttr[2])
        self.list.SetStringItem(index, 3, itemAttr[3])

        self.win.listItems[index] = itemAttr





    def listItemOnSelChanged(self, event):

        self.win.currentItem = event.m_itemIndex
        #print self.win.listItems[self.win.currentItem]
        itemName = self.list.GetItemText(self.win.currentItem)

        self.log.write("OnTreeItemSelected: %s, %s" %
                           (self.win.currentItem, itemName))

        p = os.path.join(self.win.current_dir, itemName)
        if os.path.isdir(p):
            self.win.current_sel_dir = p
            self.win.current_file = None

        else:
            self.win.current_sel_dir = self.win.current_dir
            self.win.current_file = p

        self.log.write( self.win.current_sel_dir)

        #event.Skip()




    def listItemDeselected(self, event):

        self.win.current_sel_dir = None
        self.win.current_file = None

        #self.last_sel_item = self.currentItem
        #if self.edited_item != None:
        #    os.chdir(self.current_dir)
        #    os.rename(self.edited_item, self.list.GetItemText(self.currentItem))
        #    self.edited_item = None


    def listItemOnOpen(self, event):

        if self.win.current_file == None:

            self.win.current_dir = self.win.current_sel_dir

            self.win.treeItemOnOpen(None)

            '''
            self.win.current_sel_dir = None

            self.list.DeleteAllItems()
            self.win.currentItem = None
            self.showFolderItems(self.win.current_dir)
            '''



    def listEndLabelEdit(self, event):
        self.win.edited_item = self.list.GetItemText(self.win.currentItem)
        print self.win.edited_item


    def listItemOnMenu(self, event):

        # only do this part the first time so the events are only bound once
        #
        # Yet another anternate way to do IDs. Some prefer them up top to
        # avoid clutter, some prefer them close to the object of interest
        # for clarity. 

        # make a menu
        menu = wx.Menu()

        # add some items
        if self.win.current_sel_dir == None:

            #self.win.git_path = self.win.current_dir
            
            self.popupID_new_file = wx.NewId()
            self.popupID_new_folder = wx.NewId()

            menu.Append(self.popupID_new_file, "new file")
            menu.Append(self.popupID_new_folder, "new folder")
            menu.AppendSeparator()

            self.Bind(wx.EVT_MENU, self.listPopupNewFile, id=self.popupID_new_file)
            self.Bind(wx.EVT_MENU, self.listPopupNewFolder, id=self.popupID_new_folder)
            
            if self.win.clipboard[0] != 0:
            
                self.popupID_paste = wx.NewId()
                menu.Append(self.popupID_paste, "粘贴")
                self.Bind(wx.EVT_MENU, self.listPopupPaste, id=self.popupID_paste)
                menu.AppendSeparator()

            if self.win.is_git_dir:

                self.listItemOnGitMenu(menu)

                self.popupID_commit = wx.NewId()
                menu.Append(self.popupID_commit, "commit")
                menu.AppendSeparator()

            else:
            
                self.popupID_init = wx.NewId()
                menu.Append(self.popupID_init, "init here")
                menu.AppendSeparator()


        else:

            if self.win.is_git_dir:

                self.listItemOnGitMenu(menu)


            else:
            
                if self.win.current_file == None:

                    self.popupID_init = wx.NewId()
                    menu.Append(self.popupID_init, "init here")
                    menu.AppendSeparator()

            self.popupID_rename = wx.NewId()
            self.popupID_copy = wx.NewId()
            self.popupID_cut = wx.NewId()
            self.popupID_remove = wx.NewId()

            menu.Append(self.popupID_copy, "复制")
            menu.Append(self.popupID_cut, "剪切")
            menu.AppendSeparator()
            menu.Append(self.popupID_remove, "删除")
            menu.Append(self.popupID_rename, "重命名")

            self.Bind(wx.EVT_MENU, self.listPopupRename, id=self.popupID_rename)
            self.Bind(wx.EVT_MENU, self.listPopupCopy, id=self.popupID_copy)
            self.Bind(wx.EVT_MENU, self.listPopupCut, id=self.popupID_cut)
            self.Bind(wx.EVT_MENU, self.listPopupRemove, id=self.popupID_remove)


        # Popup the menu.  If an item is selected then its handler
        # will be called before PopupMenu returns.
        self.PopupMenu(menu)
        menu.Destroy()


    def listItemOnGitMenu(self, menu):

        gitmenu = wx.Menu()
        
        self.popupID_git = wx.NewId()
        self.popupID_diff = wx.NewId()
        self.popupID_add = wx.NewId()
        self.popupID_rm = wx.NewId()
        
        gitmenu.Append(self.popupID_diff, "diff")
        gitmenu.AppendSeparator()
        gitmenu.Append(self.popupID_add, "add")
        gitmenu.Append(self.popupID_rm, "rm")
        
        menu.AppendMenu(self.popupID_git, "Git...(&G)", gitmenu)
        menu.AppendSeparator()

        self.Bind(wx.EVT_MENU, self.temp, id=self.popupID_add)

    def temp(self, event):

        self.gitCtrl.do_wrapper(signals.stage)(self.win.current_sel_dir)

    def listPopupRename(self, event):
        #self.list.EditLabel(self.currentItem) # style 1
        
        oldName = self.list.GetItemText(self.win.currentItem)
        newName = self.gitFrame.TextEntry('Enter new name', 'Rename', oldName)

        if newName == -1:
            self.log.write('User cancelled or error')
        else:
            os.chdir(self.win.current_dir)
            os.rename(oldName, newName)

            self.win.treeItemOnOpen(None)


    def listPopupNewFolder(self, event):

        newFolderName = 'new folder'
        orgName = newFolderName

        i = 1
        while True:
            if os.path.exists(os.path.join(self.win.current_dir, newFolderName)):
                newFolderName = orgName + str(i)
                i += 1
            else:
                break

        os.chdir(self.win.current_dir)
        os.mkdir(newFolderName)
        self.listInsertOneItem(os.path.join(self.win.current_dir, newFolderName), self.fldridx)

        print self.win.listItems
        self.win.currentItem = self.list.GetItemCount() - 1
        self.listPopupRename(None)



    def listPopupNewFile(self, event):
    
        newFileName = 'new file'
        orgName = newFileName

        i = 1
        while True:
            if os.path.exists(os.path.join(self.win.current_dir, newFileName)):
                newFileName = orgName + str(i)
                i += 1
            else:
                break

        cmd = ['touch', newFileName]
        self.gitRepo.gitProcess(cmd, self.win.current_dir)

        self.listInsertOneItem(os.path.join(self.win.current_dir, newFileName), self.fileidx)
        #self.list.EditLabel(self.listItemNum)
        self.win.currentItem = self.list.GetItemCount() - 1
        self.listPopupRename(None)


    def listPopupCopy(self, event):

        self.win.clipboard = [1, 
            os.path.join(self.win.current_dir, self.list.GetItemText(self.win.currentItem))]
        


    def listPopupCut(self, event):

        self.win.clipboard = [2, 
            os.path.join(self.win.current_dir, self.list.GetItemText(self.win.currentItem))]
        


    def listPopupPaste(self, event):

        if self.win.clipboard[0] == 0:
            self.log.write('Paste error')
            return -1

        elif not os.path.exists(self.win.clipboard[1]):
            self.win.clipboard = [0, None]
            self.log.write('错误：源文件已被移除')
            return -1

        elif os.path.exists(os.path.join(self.win.current_dir, os.path.basename(self.win.clipboard[1]))):
            self.log.write('错误：目标地址文件（夹）重名')
            return -1

        elif re.match(self.win.clipboard[1], self.win.current_dir):
            self.log.write('错误：请勿将文件夹粘贴到其子目录')
            return -1

        #可在此处加一个目录是否可写的判断


        elif self.win.clipboard[0] == 1:
            cmd = ['cp', '-r', self.win.clipboard[1], self.win.current_dir]
            self.gitRepo.gitProcess(cmd, self.win.current_dir)
            #self.win.clipboard = [0, None]
            self.win.treeItemOnOpen(None)

        elif self.win.clipboard[0] == 2:
            cmd = ['mv', self.win.clipboard[1], self.win.current_dir]
            self.gitRepo.gitProcess(cmd, self.win.current_dir)
            self.win.clipboard = [0, None]
            self.win.treeItemOnOpen(None)



    def listPopupRemove(self, event):

        cmd = ['rm', '-r', self.list.GetItemText(self.win.currentItem)]
        self.gitRepo.gitProcess(cmd, self.win.current_dir)

        self.win.treeItemOnOpen(None)
        '''
        cmd = ['mv', self.list.GetItemText(self.win.currentItem), 
            './.Trash/'] # os.path.join(self.win.current_dir, .Trash)]
        self.gitRepo.gitProcess(cmd, self.win.current_dir)

        self.win.treeItemOnOpen(None)
        #self.win.listItemNum -= 1
        '''

#---------------------------------------------------------------------------
