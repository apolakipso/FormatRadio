#!/usr/bin/env python


##!/usr/bin/env python
##!/usr/bin/python
from Tkinter import *
import tkMessageBox

class App:

    def __init__(self, master):

        frame = Frame(master, padx=10, pady=10, bg="yellow")
        frame.pack()

        self.scrollbar = Scrollbar(frame, orient=VERTICAL)
        self.listbox = Listbox(frame, yscrollcommand=self.scrollbar.set)
        self.scrollbar.config(command=self.listbox.yview)
        self.scrollbar.pack(side=RIGHT, fill=Y)
        self.listbox.pack(side=RIGHT, fill=BOTH, expand=1)
        #self.listbox.insert(END, "a list entry")

        for item in ("a,b,c," * 10).split(','):
            self.listbox.insert(END, item)
        self.button = Button(frame, text="QUIT", fg="red", command=frame.quit)
        self.button.pack(side=LEFT)

        self.hi_there = Button(frame, text="Hello", command=self.say_hi)
        self.hi_there.pack(side=LEFT)

        self.btnWarn = Button(frame, text="Show Warning", command=self.warn)
        self.btnWarn.pack(side=LEFT, anchor="n")

    def warn(self):
        # showinfo, showwarning, showerror, askquestion, askokcancel, askyesno, askretrycancel
        r = tkMessageBox.showwarning("Open file", "This is a warning", type="abortretryignore")
        self.listbox.insert(END, r)

    def say_hi(self):
        print "hi there, everyone!"

root = Tk()
app = App(root)
root.mainloop()
root.destroy()
