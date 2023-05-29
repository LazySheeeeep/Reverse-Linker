import tkinter as tk
from util import sqlhelper as sh
from util import consultant as ct

options_name = ["pass", "review", "respell", "both"]


class PhraseOptionWindow:
    def __init__(self, master: tk.Tk, first_op_name, second_op_name):
        self.master = master
        self.top = tk.Toplevel(self.master)
        window_width = 200
        window_height = 150
        screen_width = self.top.winfo_screenwidth()
        screen_height = self.top.winfo_screenheight()
        x = int((screen_width - window_width) / 2)
        y = int((screen_height - window_height) / 2)
        self.top.geometry(f"{window_width}x{window_height}+{x}+{y}")
        title_label = tk.Label(self.top, text='Please choose an option', justify=tk.CENTER)
        title_label.grid(row=0, column=0, pady=5)
        self.option_var = tk.IntVar()
        self.option_var.set(0)  # 默认选中第一个选项
        self.button1 = tk.Radiobutton(self.top, text=first_op_name, variable=self.option_var, value=0,
                                      command=self.on_first_handler)
        self.button1.grid(row=1, column=0, padx=5, pady=5, sticky=tk.W + tk.E)
        self.button2 = tk.Radiobutton(self.top, text=second_op_name, variable=self.option_var, value=1,
                                      command=self.on_second_handler)
        self.button2.grid(row=2, column=0, padx=5, pady=5, sticky=tk.W + tk.E)
        self.entry = tk.Entry(self.top, justify=tk.CENTER, width=20)
        self.top.bind("<Tab>", self.change_option)  # 绑定Tab键
        self.top.bind("<Return>", self.close_window)  # 绑定Enter键

        self.button1.focus_set()  # 将焦点设置在第一个选项上
        self.button1.select()  # 默认选中第一个选项

        self.associate_word = ''

    def change_option(self, event=None):
        # 按一次就换一个选项；
        if self.option_var.get() == 0:
            self.on_second_handler()
        else:
            self.on_first_handler()

    def on_first_handler(self):
        self.option_var.set(0)
        self.entry.grid_forget()

    def on_second_handler(self, event=None):
        self.option_var.set(1)
        self.entry.grid(row=3, column=0, padx=5, pady=5, sticky=tk.W + tk.E)
        self.entry.focus_set()

    def close_window(self, event=None):
        if self.option_var.get() == 1:
            self.associate_word = self.entry.get()
            self.entry.delete(0, tk.END)
        self.top.destroy()

    def outcome(self):
        self.top.wait_window()
        return self.associate_word


class InputWindow:
    def __init__(self, master: tk.Tk):
        self.master = master
        self.top = tk.Toplevel(self.master)
        self.top.title("Input Window")
        self.top.resizable(True, True)
        self.height = 200
        self.width = 440
        x = (self.top.winfo_screenwidth() - self.width) // 2
        y = (self.top.winfo_screenheight() - self.height) // 2
        self.top.geometry(f"{self.width}x{self.height}+{x}+{y}")

        # 输入框及选项
        self.main_label = tk.Label(self.top, text="Please type a word:")
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
        self.back_button.grid(row=6, column=0, padx=3, pady=1, sticky=tk.W)
        self.undo_button = tk.Button(self.top, text="undo", command=self.undo)
        self.undo_button.grid(row=6, column=1, padx=5, pady=5, sticky=tk.W)
        self.confirm_button = tk.Button(self.top, text="commit", command=lambda: sh.exec_i("commit;"))
        self.confirm_button.grid(row=1, column=3, padx=5, pady=5, sticky=tk.W)

        # 消息输出框
        self.output_text = tk.Text(self.top, height=5, state=tk.DISABLED)
        self.output_text.grid(row=3, column=0, columnspan=4, rowspan=3, sticky=tk.NSEW)
        self.output("This is an output window.")
        # 设置列宽行高
        for i in range(4):
            self.top.grid_columnconfigure(i, minsize=5, weight=1)
        for i in range(6):
            self.top.grid_rowconfigure(i, minsize=5, weight=2)
        self.top.grid_rowconfigure(6, minsize=3, weight=1)

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
        self.note_label.grid(row=6, column=1, padx=5, pady=3, sticky=tk.E)
        self.note_entry.grid(row=6, column=2, columnspan=2, sticky=tk.EW)

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
            self.output(f"\n{options_name[option_num]}:{text}")
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
        primary_query_result = sh.fetchone(f"select `translation` from `translations` where `origin`='{text}';")
        if primary_query_result:
            self.main_label.config(text=str(primary_query_result))
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
                    phrase_option_window = PhraseOptionWindow(self.master, "Independent", "Related to")
                    related_word = phrase_option_window.outcome()
                    if related_word == '':  # 选择独立
                        sh.phrase_process(text, self.output, note_text)
                    else:
                        self.output('\tassociate with:' + related_word)
                        sh.phrase_process(text, self.output, note_text, related_word)
        # 单词加入，提取note，再看是否已经有计划
        else:
            note_text = None
            if option_num != 2:
                self.note_entry.get()
                self.note_entry.delete(0, tk.END)
            if note_text:
                self.output(f"\tNote:{note_text}")
            # 检测是否已有refresh计划
            exist_result = sh.fetchone(f"select * from words where spelling = '{text}';")
            # 已有，更新计划，输出消息
            if exist_result:
                cnt = sh.word_renew(text, option_num, note_text, alias)
                self.output('\n计划更新√' + cnt)
            # 查询结果，结果入库
            else:
                sh.word_process(text, option_num, self.output, note_text, alias)
                self.output('\n计划加入√')


if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    InputWindow(root)
    root.mainloop()
