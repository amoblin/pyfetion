#!/usr/bin/env python
# -*- coding: utf-8 -*-
#Using GPL v2
#Author: cocobear.cn@gmail.com
#A simple calculator wrote in wxPython

import wx
import sys 
class Panel(wx.Panel):
    def __init__(self,parent,id):
        #box[0]:last result;box[1]:operator
        self.box = ['','']
        #stands for new calculate
        self.flag = False

        wx.Panel.__init__(self,parent,id,style=wx.BORDER_SUNKEN)
        self.Bind(wx.EVT_RIGHT_DOWN,self.OnRightDown,self)

        sizer = wx.BoxSizer(wx.VERTICAL)
        self.display = wx.TextCtrl(self,-1,'',style=wx.TE_RIGHT)
        sizer.Add(self.display,0,wx.wx.EXPAND | wx.BOTTOM, 9)

        gs = wx.GridSizer(4,4,5,5)
        texts = ['Bksp','CE','Clr','+/-','7','8','9','/','4','5','6','*','1','2','3','-','0','.','=','+']
        for t in texts:
            button = wx.Button(self,-1,t)
            self.Bind(wx.EVT_BUTTON,self.OnClick,button)
            button.Bind(wx.EVT_RIGHT_DOWN,self.OnRightDown,button)

            gs.Add(button,0,wx.EXPAND)


        sizer.Add(gs,1,wx.EXPAND | wx.RIGHT | wx.BOTTOM,15)
        self.SetSizer(sizer)
    def OnRightDown(self,event):
        description = "Just a simple calculator"
        licence = "GPL v2"
        info = wx.AboutDialogInfo()
        info.SetVersion('1.0')
        info.SetName('CoCal')
        info.SetCopyright('(C) 2008 cocobear')
        info.SetWebSite('http://cocobear.info')
        info.SetDescription(description)
        info.SetLicence(licence)
        info.AddDeveloper('cocobear')

        wx.AboutBox(info)
    def click_b_bksp(self,event):
        s = self.display.GetValue()
        if s:
            s = s[0:-1]
            self.display.SetValue(s)

    def click_b_ce(self,event):
        self.display.SetValue("")

    def click_b_clr(self,event):
        self.display.SetValue("")
        self.box[0] = ''
        self.box[1] = ''

    def click_b_ch(self,event):
        s = self.display.GetValue()
        if s:
            if s[0] == '-':
                s = s[1:]
            else:
                s = "-"+s
            self.display.SetValue(s)




    def OnClick(self, event):
        label = event.EventObject.GetLabel()
        nums = range(10)
        nums.append('.')
        for n in [str(n) for n in nums]:
            if label == n:
                s = self.display.GetValue()
                if not self.flag:
                    #avoid display many '.'
                    if n == '.' and '.' in s:
                        pass
                    else:
                        s += n
                        self.display.SetValue(s)
                else:
                    self.display.SetValue(n)
                    self.flag = False
                print self.box

        for s in ['+','-','*','/','=']:
            if label == s:
                print s
                x = self.display.GetValue()
                if not self.box[0] and not self.box[1]:
                    self.box[1] = s
                    self.box[0] = float(x)


                elif self.box[0] and self.box[1] and self.flag:
                    if s != '=':
                        self.box[1] = s
                else:
                    y = {
                        '+': lambda :self.box[0]+float(x),
                        '-': lambda :self.box[0]-float(x),
                        '*': lambda :self.box[0]*float(x),
                        '/': lambda :self.box[0]/float(x),
                        }[self.box[1]]()
                    self.box[1] = s
                    self.display.SetValue(str(y))
                    self.box[0] = y
            
                self.flag = True
                if s == '=':
                    self.box[0] = ''
                    self.box[1] = ''
                print self.box
        for s in ['Bksp','CE','Clr','+/-']:
            if label == s:
                {'Bksp':self.click_b_bksp,
                'CE':self.click_b_ce,
                'Clr':self.click_b_clr,
                '+/-':self.click_b_ch}[s](event)


 
class Cal(wx.Frame):
    def __init__(self, parent, id, title):
        wx.Frame.__init__(self, parent, id, title, size=(300, 250))
        panel = Panel(self,-1)
        hbox = wx.BoxSizer()
        hbox.Add(panel,-1,wx.EXPAND)

        self.SetSizer(hbox)
        self.Centre()
        self.Show(True)
def main():

    app = wx.App()
    Cal(None,-1,'CoCal')
    app.MainLoop()

if __name__ == "__main__":
    sys.exit(main())
