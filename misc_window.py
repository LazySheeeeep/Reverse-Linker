from util import sqlhelper as sh
import ttkbootstrap as tk
from ttkbootstrap.constants import *


def load_data_for_tree(tree_widget, table_name):
    if not tree_widget.get_children():
        query = f"SELECT * FROM `{table_name}`;"
        data = sh.fetchall(query)
        if len(data) > 0:
            for row in data:
                tree_widget.insert("", tk.END, values=row)
        else:
            tree_widget.insert("", tk.END, values=("null",))


def tree_specify(tree_widget: tk.Treeview, table_name,headings):
    for i, name in enumerate(headings):
        tree_widget.heading(i, text=headings[i])
        tree_widget.column(i, anchor="center")
    tree_widget.column(0, width=10)
    tree_widget.pack(side="top", fill="both", expand=True)
    tree_widget.bind("<Visibility>", lambda event: load_data_for_tree(tree_widget, table_name))


panel_info_list = [
    ("今日复习总览", "revise_list_today", ["ID", "Vocab", "Mastery", "Next Date", "Type"]),
    ("今日重现单词", "refresh_words_today", ["ID", "Word", "Phonetic", "Mastery"]),
    ("今日重现短语", "refresh_phrases_today", ["ID", "Phrase", "Relate to", "Mastery"]),
    ("今日重拼单词", "respell_words_today", ["ID", "Word", "Phonetic", "Alias", "Mastery"]),
    ("全部重现单词", "refresh_words_all", ["ID", "Word", "Phonetic", "Mastery", "Next Date"]),
    ("全部重现短语", "refresh_phrases_all", ["ID", "Phrase", "Relate to", "Mastery", "Next Date"]),
    ("全部重拼单词", "respell_words_all", ["ID", "Word", "Phonetic", "Alias", "Mastery", "Next Date"]),
    ("总复习计划", "revise_list_all", ["ID", "Vocab", "Mastery", "Next Date", "Type"])
]


class MiscWindow:
    def __init__(self, master):
        self.master = master
        self.master.withdraw()
        self.top = tk.Toplevel(self.master)
        self.top.title("Miscellaneous")
        self.top.protocol("WM_DELETE_WINDOW", lambda: self.back())
        # 总的看来是一个看板
        self.notebook = tk.Notebook(self.top)
        self.notebook.pack(fill="both", expand=True)
        # command面板
        self.command_panel = tk.Frame(self.notebook)
        self.entry = tk.Entry(self.command_panel)
        self.entry.bind("<Return>", self.execute_command)
        self.output_text = tk.Text(self.command_panel, height=20, state="disabled")
        self.entry.pack(side="top", fill="x")
        self.output_text.pack(side="top", fill="both", expand=True)

        for panel_info in panel_info_list:
            panel_name, data_key, column_names = panel_info
            # Create a new frame to hold the treeview widget
            panel_frame = tk.Frame(self.notebook)
            # Add the new frame to the notebook
            self.notebook.add(panel_frame, text=panel_name)
            # Create the treeview widget with the specified columns
            treeview = tk.Treeview(panel_frame, columns=list(range(len(column_names))), show=HEADINGS)
            tree_specify(treeview, data_key, column_names)
        # command panel at last, and select it by default
        self.notebook.add(self.command_panel, text="Command")
        self.notebook.select(self.command_panel)
        self.output_text.config(state="normal")
        self.output_text.insert("1.0", "This is command panel. Youcan choose another panel on your will.")
        self.output_text.config(state="disabled")

    def execute_command(self, event=None):
        # 提取entry中输入的指令，
        command = self.entry.get()
        # 清空entry，
        self.entry.delete(0, "end")
        # 通过sh.cursor来执行指令，
        try:
            self.output_text.config(state="normal")
            self.output_text.insert("end", f"\ncommand: {command}")
            results = sh.fetchall(command)
            for result in results:
                self.output_text.insert("end", f"\n{result}")
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
    master = tk.Window()
    MiscWindow(master)
    master.mainloop()
