import ttkbootstrap as tk
from ttkbootstrap.constants import *
from tkinter.filedialog import askopenfilename
from ttkbootstrap.dialogs import Querybox
from util import sqlhelper as sh
from util import consultant as ct
import threading

options_name = ["pass", "review", "respell", "both"]


class DictationWindow:
    def __init__(self, master):
        self.master = master
        self.top = tk.Toplevel(self.master, alpha=0.85, background='grey')
        self.top.title("Input Window")
        self.top.resizable(True, True)
        self.top.place_window_center()

        # 输入框及选项
        self.main_label = tk.Label(self.top, justify=tk.CENTER, text="Please type a word:", anchor="center")
        self.main_label.grid(row=0, column=0, columnspan=4, padx=40, pady=5, sticky=tk.W + tk.E)
        self.main_entry = tk.Entry(self.top, justify=tk.CENTER, width=20)
        self.main_entry.grid(row=1, column=1, columnspan=2, padx=5, pady=5, sticky=tk.W + tk.E)

        # 绑定事件
        self.top.bind("<Return>", self.submit_handler)
        self.top.bind("<Tab>", self.tab_handler)
        self.main_entry.bind("<Up>", self.up_handler)
        self.main_entry.bind("<Down>", func=lambda _event: self.main_entry.delete(0, tk.END))
        self.top.protocol("WM_DELETE_WINDOW", lambda: self.master.quit())
        # 选项
        self.option_var = tk.IntVar()
        self.option_var.set(0)  # 默认选中第一个选项
        self.option_button = []
        for i in range(4):
            self.option_button.append(tk.Radiobutton(self.top, text=options_name[i], variable=self.option_var, value=i))
            self.option_button[i].grid(row=2, column=i, padx=5, pady=5, sticky=tk.W + tk.E)
            if i % 2:  # review , both
                self.option_button[i].config(command=self.show_note_entry)
            else:
                self.option_button[i].config(command=self.invisible_note_entry)

        # 按钮
        self.back_button = tk.Button(self.top, text="<", command=self.back)
        self.back_button.grid(row=7, column=0, padx=3, pady=1, sticky=tk.W)
        self.undo_button = tk.Button(self.top, text="undo", command=self.undo)
        self.undo_button.grid(row=7, column=1, padx=5, pady=5, sticky=tk.W)
        self.confirm_button = tk.Button(self.top, text="commit", command=lambda: sh.exec_i("commit;"))
        self.confirm_button.grid(row=1, column=3, padx=5, pady=5, sticky=tk.W)

        # 消息输出框
        self.output_text = tk.Text(self.top, height=10, state=tk.DISABLED)
        self.output_text.grid(row=3, column=0, columnspan=4, rowspan=4, sticky=tk.NSEW)
        self.output("This is an output window.")
        # 设置列宽行高
        for i in range(4):
            self.top.grid_columnconfigure(i, minsize=5, weight=1)
        for i in range(7):
            self.top.grid_rowconfigure(i, minsize=5, weight=2)
        self.top.grid_rowconfigure(7, minsize=3, weight=1)

        # note输入框
        self.note_label = tk.Label(self.top, state=tk.DISABLED, text="Note:")
        self.note_entry = tk.Entry(self.top)

        # 上一次提交的内容
        self.last_submit = ""

    def back(self):
        self.top.withdraw()
        self.master.deiconify()

    def undo(self):
        self.output(f"\nundo affects {sh.exec_i('rollback;')}row(s)")

    def up_handler(self, event=None):
        self.main_entry.delete(0, tk.END)
        self.main_entry.insert(0, self.last_submit)

    def output(self, msg: str):
        self.output_text.config(state=tk.NORMAL)
        self.output_text.insert(tk.END, msg)
        self.output_text.see(tk.END)
        self.output_text.config(state=tk.DISABLED)

    def tab_handler(self, event=None):
        self.option_var.set((self.option_var.get() + 1) % 4)
        if self.option_var.get() % 2:
            self.show_note_entry()
        else:
            self.invisible_note_entry()
        self.master.after(2, lambda: self.main_entry.focus())

    def show_note_entry(self, event=None):
        self.note_label.grid(row=7, column=1, padx=5, pady=3, sticky=tk.E)
        self.note_entry.grid(row=7, column=2, columnspan=2, sticky=tk.EW)

    def invisible_note_entry(self, event=None):
        self.note_label.grid_forget()
        self.note_entry.grid_forget()

    def submit_handler(self, event=None):
        text = self.main_entry.get().strip().lower()
        option_num = self.option_var.get()
        self.main_entry.delete(0, tk.END)  # 清空输入框
        # 合法性检测
        if text == '':
            return
        elif all(char.isalpha() and
                 not char > u'\u3000' or char in [' ', '-', '|']
                 for char in text) and \
                len(text) < 40:
            self.output(f"\n{options_name[option_num]}:{text}")  # todo: another panel output
        else:
            self.output(f'\nInvalid Input.{text}')
            self.main_label.config(text="Please try again")
            return
        if '|' in text:
            fragment = text.split('|')
            if len(fragment) != 2:
                self.output(f'\nInvalid Input.{text}')
                self.main_label.config(text="Please try again")
                return
            text = fragment[0]
            alias = fragment[1]
        else:
            alias = None
        self.last_submit = text
        # 合法性检测结束，查看是否在库中
        primary_query_result = sh.fetchall(f"select `translation` from `translations` where `origin`='{text}';")
        if primary_query_result:
            prompt = ''
            for trans in primary_query_result:
                prompt += trans[0] + '|'
            self.main_label.config(text=prompt)
        else:
            translation = ct.primary_test(text, self.output)
            if translation:
                self.main_label.config(text=translation)
            else:
                self.main_label.config(text="未查到结果")
                return
        if option_num == 0:
            return
        # 词组加入， 仅加入refresh plan
        if ' ' in text:
            note_text = self.note_entry.get()
            self.note_entry.delete(0, tk.END)
            if note_text:
                self.output(f"\tNote:{note_text}")
                # 已在库中，更新计划，返回消息
            if primary_query_result:
                row_count = sh.exec_i(
                    f"update `revise_items` set `mastery_level` = 1 where `revise_id` in (\
                    select `refresh_id` from `phrases` where `phrase` = '{text}');")
                if row_count != 0:
                    self.output("\t已存在库中，计划已更新;")
                else:
                    self.output("\t已存在库中，但貌似没更新？")
            # 不在库中，先弹窗问词组复习形式，再查询结果，结果入库
            else:
                related_word = Querybox.get_string(
                    prompt="related word:\n(or blank indicate independent)",
                    title="Phrase Option",
                    parent=self.top
                )
                if related_word == '':  # 选择独立
                    self.output('\t|independent')
                    sh.phrase_process(text, self.output, note_text)
                else:
                    self.output('\t|related to:' + related_word)
                    sh.phrase_process(text, self.output, note_text, related_word)
        # 单词加入，提取note，再看是否已经有计划
        else:
            note_text = None
            if option_num != 2:
                note_text = self.note_entry.get()
                if note_text:
                    self.note_entry.delete(0, tk.END)
                    self.output(f"\tNote:{note_text}")
            sh.commit_and_start()
            self.output("\ncommit and start")
            threading.Thread(target=lambda:
            sh.word_process(word=text, op=option_num, output=self.output, note=note_text, alias=alias)).start()


if __name__ == "__main__":
    root = tk.Window()
    root.withdraw()
    DictationWindow(root)
    root.mainloop()


class ImportFileWindow:
    def __init__(self, master):
        self.master = master
        self.top = tk.Toplevel(master, alpha=0.9)
        self.top.title("选择单词文件导入数据库，文件内一行一个单词，不支持词组")
        self.file_select_btn = tk.Button(self.top, text="选择文件", command=self.open_file)
        self.file_select_btn.grid(row=0, column=0, padx=10, pady=10)
        self.top.protocol("WM_DELETE_WINDOW", lambda: self.close())
        self.date_entry = tk.DateEntry(self.top, bootstyle="success", dateformat=r"%Y-%m-%d")
        self.date_entry.grid(row=0, column=1, padx=5, pady=10)

        tk.Button(self.top, text="submit", bootstyle=(PRIMARY, "outline-toolbutton"), command=self.submit) \
            .grid(row=0, column=2, padx=10, pady=10)
        self.commit_btn = tk.Button(self.top, text="commit", state=DISABLED, command=sh.db.commit)
        self.commit_btn.grid(row=0, column=3, padx=10, pady=10)

        self.output_text = tk.Text(self.top, height=40, width=100)
        self.output_text.grid(row=1, column=0, columnspan=4, padx=120, pady=30)
        self.output("This is output panel")

    def open_file(self):
        self.path = askopenfilename()
        self.file_select_btn.config(text=self.path)
        self.output(f"\n选择文件路径为：{self.path}")

    def submit(self):
        if self.path is None or self.path == '':
            self.output("\n文件不能为空")
            return
        mastery = Querybox.get_integer(parent=self.top, title="掌握程度",minvalue=0, maxvalue=4)
        date = self.date_entry.entry.get()
        self.output(f"\npath:{self.path},date:{date},mastery:{mastery}")
        sh.commit_and_start()
        self.output("\ncommit and start")
        threading.Thread(target=lambda :
        sh.import_from_file(self.path, self.output, date, str(mastery))).start()
        self.commit_btn.config(state=ACTIVE)

    def close(self):
        self.top.withdraw()
        self.master.deiconify()


    def output(self, msg: str):
        self.output_text.config(state=tk.NORMAL)
        self.output_text.insert(tk.END, msg)
        self.output_text.see(tk.END)
        self.output_text.config(state=tk.DISABLED)
