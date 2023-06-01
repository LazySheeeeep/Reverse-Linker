import ttkbootstrap as tk
import input_window as iw  # input_window.py中含有听写与文件导入两个类的实现
import revise_window as rw  # revise_window.py含有refresh window和respell window两个类的实现
import misc_window as mw

# 子窗口登记处
subwin = [("Dictation", iw.DictationWindow),
          ("Import File", iw.ImportFileWindow),
          ("Refresh", rw.RefreshWindow),
          ("Respell", rw.RespellWindow),
          ("Misc", mw.MiscWindow)]


class MainWindow:
    def __init__(self, alpha):
        self.alpha = alpha  # 设置透明度
        self.master = tk.Window(alpha=alpha)  # 新建window作为主窗口
        self.master.title("反向连接建立器")
        # 对所有的子窗口，创建一个按钮，绑定对应的唤醒子窗口的功能，并且打包到主界面显示出来
        for i, (win_name, _) in enumerate(subwin):
            tk.Button(self.master, text=win_name, width=10,
                      command=lambda i=i: self.show_subwindow(i)).pack(side=tk.LEFT, padx=10, pady=25)
        # 子窗口列表初始化
        self.subwindow_list = [None] * len(subwin)
        # 开始主窗口执行
        self.master.mainloop()

    def show_subwindow(self, num: int):
        self.master.withdraw()  # 主窗口收起
        # 看是否有对应的子窗口已被创建，如果有就展开，没有就新建一个
        if self.subwindow_list[num]:
            self.subwindow_list[num].top.deiconify()
        else:
            self.subwindow_list[num] = subwin[num][1](self.master, self.alpha)


if __name__ == "__main__":
    MainWindow(0.85)
