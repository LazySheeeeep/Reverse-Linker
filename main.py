import ttkbootstrap as tk
import input_window as iw
import revise_window as rw

class LoginWindow:
    def __init__(self, master):
        self.master = master
        self.master.title("Password Verification")
        self.master.geometry("300x100+400+300")
        self.master.resizable(False, False)

        self.label = tk.Label(self.master, text="Please enter the password:")
        self.label.pack(pady=(20, 5))
        self.entry = tk.Entry(self.master, show="*")
        self.entry.pack(pady=(0, 10))
        self.entry.bind("<Return>", self.check_password)  # 绑定回车键
        self.submit = tk.Button(self.master, text="Submit", command=self.check_password)
        self.submit.pack(pady=(0, 10))

    def check_password(self, event=None):
        password = self.entry.get()
        if password == "12345":
            self.master.destroy()
            MainWindow()
        else:
            self.label.config(text="Invalid password, please try again.")


subwin = [("Dictation", iw.DictationWindow),
          ("Import File", iw.ImportFileWindow),
          ("Refresh", rw.RefreshWindow),
          ("Respell", rw.RespellWindow),
          ("Misc", rw.ConfigWindow)]


class MainWindow:
    def __init__(self):
        self.master = tk.Window(alpha=0.8)
        self.master.place_window_center()
        self.master.title("Function Selection")
        for i, (win_name, _) in enumerate(subwin):
            tk.Button(self.master, text=win_name, width=10,
                      command=lambda i=i: self.show_subwindow(i)).pack(side=tk.LEFT, padx=10)

        self.subwindow_list = [None] * len(subwin)

        self.master.mainloop()

    def show_subwindow(self, num: int):
        self.master.withdraw()
        if self.subwindow_list[num]:
            self.subwindow_list[num].top.deiconify()
        else:
            self.subwindow_list[num] = subwin[num][1](self.master)


if __name__ == "__main__":
    MainWindow()
