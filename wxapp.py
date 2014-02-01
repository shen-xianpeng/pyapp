# coding=utf-8
import re
import sqlite3

import wx
from wx.lib.mixins.listctrl import ColumnSorterMixin


DATA = {
0 : (u"shen", "18801794295", u"赤壁"),
1 : (u"Test", "12345600000", u"上海"),
2 : (u"doe", "15678900000", u"深圳"),
3 : (u"John", "13455555555", u"武汉")
}

def init_db():
    with open('contacts.db', 'w') as f:
        pass
    with sqlite3.connect('contacts.db') as conn:
        c = conn.cursor()
        c.execute('''create table contacts
                    (name text,
                     phone text,
                     address text
                     )'''
                  )
        conn.commit()

def insert_entry(data):
    with sqlite3.connect('contacts.db') as conn:
        c = conn.cursor()
        sql = """insert into contacts values ('%s', '%s', '%s')""" % (data[0],data[1],data[2])
        c.execute(sql)
        conn.commit()

def getEntryByName(name):
    try:
        conn = sqlite3.connect('contacts.db')
        c = conn.cursor()
        c.execute("select * from contacts where name = '%s'" % name)
        entry = c.fetchone()
    except:
        pass
    else:
        return entry
    finally:
        conn.close()


class MyApp(wx.App):

    def OnInit(self):
        frame = MyFrame(None, u"通讯录")
        frame.Show()
        self.SetTopWindow(frame)
        return True


class MyFrame(wx.Frame):

    def __init__(self, parent, title):
        wx.Frame.__init__(self, parent, wx.NewId(), title, size=(500, -1))
        wx.Frame.CenterOnScreen(self)
        self.panel = MyPanel(self)


class MyPanel(wx.Panel):

    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        self.list = MyListCtrl(self, 4)
        self.text_input = wx.TextCtrl(self, 2)
        self.search_button = wx.Button(self, 3, label=u"搜索")
        self.add_button = wx.Button(self, 4, label=u"添加")
        h_sizer = wx.BoxSizer(wx.HORIZONTAL)
        h_sizer.Add(self.text_input, proportion=1, flag=wx.ALL, border=5)
        h_sizer.Add(self.search_button, proportion=0, flag=wx.ALL, border=5)
        h_sizer.Add(self.add_button, proportion=0, flag=wx.ALL, border=5)
        v_sizer = wx.BoxSizer(wx.VERTICAL)
        v_sizer.Add(h_sizer, proportion=0, flag=wx.EXPAND)
        v_sizer.Add(self.list, proportion=1, flag=wx.EXPAND, border=5)
        self.SetSizer(v_sizer)
        self.search_button.Bind(wx.EVT_BUTTON,self.onSearch)
        self.add_button.Bind(wx.EVT_BUTTON,self.onAdd)

    def onSearch(self, event):
        str = self.text_input.GetValue().strip()
        if str:
            datas = self.list.itemDataMap
            for i in range(self.list.GetItemCount()):
                self.list.SetItemBackgroundColour(i,
                    self.list.GetMainWindow().BackgroundColour)
                search_str = str.replace('*', '\S*')
                pattern = re.compile(r'^%s$' % search_str)
                if any(pattern.match(data) for data in datas[self.list.GetItemData(i)]):
                    self.list.SetItemBackgroundColour(i,
                            wx.Colour(255,255,0))
                    continue

    def onAdd(self, event):
        self.new_w = NewWindow(self)
        self.new_w.Show()


class MyPopupMenu(wx.Menu):

    def __init__(self,parent, item):
        super(MyPopupMenu,self).__init__()
        self.parent = parent
        self.item = item
        menuEdit = wx.MenuItem(self,wx.NewId(), u'修改 %s' % item[0])
        self.AppendItem(menuEdit)
        self.Bind(wx.EVT_MENU, self.onEdit, menuEdit)
        menuDel = wx.MenuItem(self,wx.NewId(), u'删除 %s' % item[0])
        self.AppendItem(menuDel)
        self.Bind(wx.EVT_MENU, self.OnDelete, menuDel)

    def onEdit(self,e):
        edit_w = EditWindow(self.parent.parent, initials=self.item)
        edit_w.Show()

    def OnDelete(self,e):
        try:
            conn = sqlite3.connect('contacts.db')
            c = conn.cursor()
            c.execute('''delete from contacts where name="%s"''' % self.item[0]
                      )
            conn.commit()
        except:
            pass
        finally:
            conn.close()
        self.parent.refresh_list()


class MyListCtrl(wx.ListCtrl, wx.lib.mixins.listctrl.ColumnSorterMixin):
    def __init__(self, parent, columns):
        wx.ListCtrl.__init__(self, parent, -1, style=wx.LC_REPORT)
        ColumnSorterMixin.__init__(self, columns)
        self.SetFont(wx.Font(16, wx.SWISS, wx.NORMAL, wx.NORMAL))
        self.current = None
        self.parent = parent
        self.R_MOUSE = 0
        self.InsertColumn(0, u"姓名")
        self.InsertColumn(1, u"手机号码")
        self.InsertColumn(2, u"地址")
        self.SetColumnWidth(0, 200)
        self.SetColumnWidth(1, 200)
        self.SetColumnWidth(2, 200)
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnSelect)
        self.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.OnDeSelect)
        self.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK, self.OnRightClick)
        self.data = None
        self.itemDataMap = {}
        self.refresh_list()
        self.il = wx.ImageList(16, 16)
        a={"sm_up":"GO_UP","sm_dn":"GO_DOWN"}
        for k,v in a.items():
            s="self.%s= self.il.Add(wx.ArtProvider_GetBitmap(wx.ART_%s,wx.ART_TOOLBAR,(16,16)))" % (k,v)
            exec(s)
        self.SetImageList(self.il, wx.IMAGE_LIST_SMALL)

    def GetListCtrl(self):
        return self

    def GetSortImages(self):
        return (self.sm_dn, self.sm_up)

    def refresh_list(self):
        self.DeleteAllItems()
        try:
            conn = sqlite3.connect('contacts.db')
            c = conn.cursor()
            c.execute("select * from contacts")
            datas = c.fetchall()
            for i, data in enumerate(datas):
                self.itemDataMap[i]=data
                self.Append(data)
                self.SetItemData(i,i)
        except:
            print "refresh conn error"
        finally:
            conn.close()

    def OnRightClick(self, event):
        position = event.GetPosition()
        index = event.GetIndex()
        item = []
        for i in range(3):
            item.append(self.GetItem(itemId=index, col=i).GetText())
        self.PopupMenu(MyPopupMenu(self, item), position)
        event.Skip()

    def OnDeSelect(self, event):
        for i in range(self.GetItemCount()):
            self.SetItemBackgroundColour(i,
                self.GetMainWindow().BackgroundColour)

    def OnSelect(self, event):
        index = event.GetIndex()
        self.SetItemState(index, 0, wx.LIST_STATE_SELECTED)
        self.SetItemBackgroundColour(index, wx.Colour(255,255,0))


class NewWindow(wx.Frame):

    def __init__(self, parent):
        wx.Frame.__init__(self, parent, size=(400,250), style=wx.DEFAULT_FRAME_STYLE | wx.STAY_ON_TOP)
        self.parent = parent
        self.new_friend = {}
        self.CenterOnParent()
        panel = wx.Panel(self)
        sizer = wx.GridBagSizer(5, 5)

        label1 = wx.StaticText(panel, label=u"姓名")
        sizer.Add(label1, pos=(1, 0), flag=wx.LEFT)
        self.text1 = wx.TextCtrl(panel,wx.ID_ANY,u"", wx.DefaultPosition, wx.DefaultSize, 5 )
        sizer.Add( self.text1, pos=(1, 1), span=(1, 3), flag=wx.TOP|wx.EXPAND )

        label2 = wx.StaticText(panel, label=u"手机")
        sizer.Add(label2, pos=(2, 0), flag=wx.LEFT|wx.TOP)
        self.text2 = wx.TextCtrl(panel,wx.ID_ANY,u"", wx.DefaultPosition, wx.DefaultSize, 5 )
        sizer.Add( self.text2, pos=(2, 1), span=(1, 3), flag=wx.TOP|wx.EXPAND )

        label3 = wx.StaticText(panel, label=u"地址")
        sizer.Add(label3, pos=(3, 0), flag=wx.TOP|wx.LEFT)
        self.text3 = wx.TextCtrl(panel,wx.ID_ANY,u"", wx.DefaultPosition, wx.DefaultSize, 5 )
        sizer.Add( self.text3, pos=(3, 1), span=(1, 3), flag=wx.TOP|wx.EXPAND )

        error = wx.StaticText(panel, label=u"")
        error.SetForegroundColour('red')
        sizer.Add(error, pos=(4, 2), flag=wx.TOP|wx.LEFT)
        self.error = error

        self.button = wx.Button(panel, label=u"添加")
        sizer.Add(self.button, pos=(5, 3))

        sizer.AddGrowableCol(2)

        panel.SetSizer(sizer)

        self.button.Bind(wx.EVT_BUTTON,self.onClick)

        self.SetTitle(u"添加")

    def validate_name(self, name):
        error = ''
        entry = getEntryByName(name)
        if entry:
            error = (u'%s已经存在\n' % entry[0])
            self.text1.SetBackgroundColour("pink")
            self.text1.SetFocus()
            self.text1.Refresh()
        return error

    def validate_phone(self, phone):
        error = ''
        numbers = re.compile('^\d+$')
        if not numbers.match(phone):
            error = u'手机号格式错误\n'
            self.text2.SetBackgroundColour("pink")
            self.text2.SetFocus()
            self.text2.Refresh()
        return error

    def validate(self):
        errors = ''
        textCtrl1 = self.text1
        textCtrl2 = self.text2
        textCtrl3 = self.text3
        name = self.text1.GetValue()
        phone = self.text2.GetValue()
        address = self.text3.GetValue()
        for textCtrl in [textCtrl1, textCtrl2, textCtrl3]:
            textCtrl.SetBackgroundColour(
                wx.SystemSettings_GetColour(wx.SYS_COLOUR_WINDOW))
            textCtrl.Refresh()
        if len(phone) == 0:
            errors = u'请输入手机号码\n' + errors
            textCtrl2.SetBackgroundColour("pink")
            textCtrl2.SetFocus()
            textCtrl2.Refresh()
        else:
            error = self.validate_phone(phone)
            if error:
                errors = error + errors
        if len(name) == 0:
            errors = u'请输入姓名\n' + errors
            textCtrl1.SetBackgroundColour("pink")
            textCtrl1.SetFocus()
            textCtrl1.Refresh()
        else:
            error = self.validate_name(name)
            if error:
                errors = error + errors
        return errors

    def onClick(self,event):
        errors = self.validate()
        if errors:
            self.error.SetLabel(errors)
            return
        try:
            conn = sqlite3.connect('contacts.db')
            c = conn.cursor()
            sql = """insert into contacts values ('%s', '%s', '%s')""" % (self.text1.GetValue(), self.text2.GetValue(), self.text3.GetValue())
            c.execute(sql)
            conn.commit()
        except:
            pass
        else:
            self.parent.list.refresh_list()
        finally:
            conn.close()
        self.Close()


class EditWindow(NewWindow):

    def __init__(self, parent, initials=None):
        super(EditWindow, self).__init__(parent)
        self.initials = initials
        self.button.SetLabel(u"更新")
        self.SetTitle(u"修改")
        self.init_data()

    def validate_name(self, name):
        error = ''
        entry = getEntryByName(name)
        if entry and entry[0] != self.initials[0] :
            error = (u'%s已经存在\n' % entry[0])
            self.text1.SetBackgroundColour("pink")
            self.text1.SetFocus()
            self.text1.Refresh()
        return error

    def onClick(self,event):
        errors = self.validate()
        if errors:
            self.error.SetLabel(errors)
            return
        try:
            conn = sqlite3.connect('contacts.db')
            c = conn.cursor()
            sql = """UPDATE contacts
                     SET name='%s', phone='%s', address='%s' where name='%s'
                  """ % (self.text1.GetValue(),
                         self.text2.GetValue(),
                         self.text3.GetValue(),
                         self.initials[0])
            c.execute(sql)
            conn.commit()
        except sqlite3.Error:
            print sqlite3.Error
        else:
            self.parent.list.refresh_list()
            self.Close()
        finally:
            conn.close()

    def init_data(self):
        self.text1.SetValue(self.initials[0])
        self.text2.SetValue(self.initials[1])
        self.text3.SetValue(self.initials[2])


if __name__ == "__main__":
    init_db()
    for i in DATA:
        insert_entry(DATA[i])
    app = MyApp()
    app.MainLoop()
