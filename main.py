import tkinter as tk
import input_window as iw
from util import sqlhelper as sh
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


class MainWindow:
    def __init__(self):
        self.master = tk.Tk()
        self.master.title("Function Selection")
        self.master.geometry("300x100+400+300")
        self.master.resizable(False, False)

        self.button1 = tk.Button(self.master, text="Input", width=10, command=self.show_input_window)
        self.button1.pack(side=tk.LEFT, padx=10)
        self.button2 = tk.Button(self.master, text="Revise", width=10, command=self.show_revise_window)
        self.button2.pack(side=tk.LEFT, padx=10)
        self.button3 = tk.Button(self.master, text="Config", width=10, command=self.show_config_window)
        self.button3.pack(side=tk.LEFT, padx=10)

        self.input_window = None
        self.revise_window = None
        self.config_window = None

        self.master.mainloop()

    def show_input_window(self):
        self.master.withdraw()
        if self.input_window:
            self.input_window.top.deiconify()
        else:
            self.input_window = iw.InputWindow(self.master)

    def show_revise_window(self):
        self.master.withdraw()
        if self.revise_window:
            self.revise_window.top.deiconify()
        else:
            self.revise_window = rw.ReviseWindow(self.master)

    def show_config_window(self):
        self.master.withdraw()
        if self.config_window:
            self.config_window.top.deiconify()
        else:
            self.config_window = ConfigWindow(self.master)


class ConfigWindow:
    def __init__(self, master: tk.Tk):
        self.master = master
        self.master.withdraw()
        self.top = tk.Toplevel(self.master)
        self.top.title("Config")
        self.top.bind("<Return>", self.execute_command)  # 绑定回车键
        self.top.protocol("WM_DELETE_WINDOW", lambda: self.master.quit())
        self.entry = tk.Entry(self.top)
        self.back = tk.Button(self.top, text="Back", command=self.back)
        self.output_text = tk.Text(self.top, height=20, state="disabled")
        self.entry.pack(side="top", fill="x")
        self.output_text.pack(side="top", fill="both", expand=True)
        self.back.pack(side="bottom", pady=10)

    def execute_command(self, event=None):
        # 提取entry中输入的指令，
        command = self.entry.get()
        # 清空entry，
        self.entry.delete(0, "end")
        # 通过sh.cursor来执行指令，
        try:
            results = sh.fetchall(command)
            # 把返回的结果全部都输出到显示框，并且self.output_text.see(tk.END)
            self.output_text.config(state="normal")
            self.output_text.insert("end", f"\n{results}")
            self.output_text.config(state="disabled")
            self.output_text.see("end")
        # 如果出错，也把出错信息输出到显示框，其实就是做一个简易的sql控制台
        except Exception as e:
            self.output_text.config(state="normal")
            self.output_text.insert("end", f"\nError: {e}")
            self.output_text.config(state="disabled")
            self.output_text.see("end")

    def back(self):
        self.top.withdraw()
        self.master.deiconify()


if __name__ == "__main__":
    MainWindow()
