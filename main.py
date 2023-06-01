import ttkbootstrap as tk
import input_window as iw
import revise_window as rw
import misc_window as mw


subwin = [("Dictation", iw.DictationWindow),
          ("Import File", iw.ImportFileWindow),
          ("Refresh", rw.RefreshWindow),
          ("Respell", rw.RespellWindow),
          ("Misc", mw.MiscWindow)]


class MainWindow:
    def __init__(self, alpha):
        self.alpha = alpha
        self.master = tk.Window(alpha=alpha)
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
            self.subwindow_list[num] = subwin[num][1](self.master, self.alpha)


if __name__ == "__main__":
    MainWindow(0.85)
