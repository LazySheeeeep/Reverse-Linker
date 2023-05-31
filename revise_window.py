import ttkbootstrap as tk
from ttkbootstrap.constants import *
from tkinter import messagebox
from util import sqlhelper as sh


# todo: implement
class RespellWindow:
    def __init__(self, master):
        self.master = master
        self.top = tk.Toplevel(master)
        self.top.title("Respell Window")
        self.top.protocol("WM_DELETE_WINDOW", self.close_window)
        self.top.protocol("WM_DEICONIFY", self.start)
        self.top.geometry("870x620")
        self.top.update()

        self.wrong_list_frame = tk.LabelFrame(text="错误的", master=self.top, style=DANGER, width=190, height=600)
        self.wrong_list_frame.place(x=670, y=10)
        self.correct_list_frame = tk.LabelFrame(text="正确的", master=self.top, style=PRIMARY, width=190, height=600)
        self.correct_list_frame.place(x=10, y=10)
        self.center_frame = tk.Labelframe(text="respell", master=self.top, style=PRIMARY, width=390, height=600)
        self.center_frame.place(x=210, y=10)

        # 将三个部件添加到新的Frame中
        self.prompt_text = tk.Text(self.center_frame, width=30, height=12, state=tk.DISABLED)
        self.prompt_text.grid(row=0, column=0, padx=10, pady=30)

        self.entry = tk.Entry(self.center_frame, width=30)
        self.entry.grid(row=1, column=0, padx=10, pady=5)
        self.entry.bind("<Return>", self.on_submit)
        self.entry.focus_set()

        tk.Button(self.center_frame, text="Recall", width=10, bootstyle="danger", command=self.recall_word)\
            .grid(row=2, column=0, padx=10, pady=5)

        self.correct_text = tk.Text(self.correct_list_frame, width=10, height=15, state=tk.DISABLED)
        self.wrong_text = tk.Text(self.wrong_list_frame, width=10, height=15, state=tk.DISABLED)

        self.word_list = sh.fetchall("select `vocab` from `revise_list_today` \
                                        where  `type` = 'respell' collate utf8mb4_unicode_ci;")
        self.total_amount = len(self.word_list)
        self.wrong_list = []
        self.correct_list = []
        self.start()
        self.current_index = 0  # 指向第几个单词
        self.state = 0  # on_submit函数根据当前状态来决定prompt，0表示什么都不做

        # 上一次提交的内容
        self.last_submit = ""

    def prompt(self, msg: str):
        self.prompt_text.config(state=tk.NORMAL)
        self.prompt_text.insert(tk.END, msg)
        self.prompt_text.see(tk.END)
        self.prompt_text.config(state=tk.DISABLED)

    def add_wrong(self, word):
        self.wrong_list.append(word)
        self.wrong_text.config(state=tk.NORMAL)
        self.wrong_text.insert(tk.E, '\n' + word)
        self.wrong_text.see(tk.END)
        self.wrong_text.config(state=tk.DISABLED)

    def add_correct(self, word):
        self.correct_list.append(word)
        self.correct_text.config(state=tk.NORMAL)
        self.correct_text.insert(tk.E, '\n' + word)
        self.correct_text.see(tk.END)
        self.correct_text.config(state=tk.DISABLED)

    def start(self):
        if self.total_amount == 0:
            messagebox.showinfo("今日计划已经完成")
            self.close_window()
            return
        result = messagebox.askquestion("提示", f"\n今日需重拼：{self.total_amount}词，是否开始？")
        if result == "yes":
            self.prompt("Start：")
            for word in self.word_list:
                self.prompt(f"\n{word}")
        else:
            self.prompt("\n取消操作")

    def show_next_word(self):
        if self.current_index < len(self.word_list):
            word = self.word_list[self.current_index]
            self.prompt_label.configure(text=word["prompt"])
            self.translation_label.configure(text="")
            self.entry.delete(0, tk.END)
        else:
            messagebox.showinfo("Finished", "You have finished respelling all the words.")

    def on_submit(self, event):
        return
        answer = self.entry.get().strip()
        word = self.word_list[self.current_index]
        correct_spelling = word["spelling"]
        alias = word["alias"]
        if answer.lower() == correct_spelling.lower():
            self.current_index += 1
            self.update_mastery_level(word["respell_id"])
            self.show_next_word()
        elif alias and answer.lower() == alias.lower():
            self.current_index += 1
            self.update_mastery_level(word["respell_id"])
            self.show_next_word()
        else:
            self.wrong_list.append(word)
            self.show_wrong_list()
            messagebox.showinfo("Incorrect", f"The correct spelling is: {correct_spelling}")

    def recall_word(self):
        if self.wrong_list:
            self.wrong_text.config(state=tk.NORMAL)
            self.wrong_text.delete(self.prompt_text.index("end-2c linestart"), "end")
            self.wrong_text.config(state=tk.DISABLED)
            self.add_correct(self.wrong_list.pop(-1))

    def update_mastery_level(self):
        cnt = 0
        for word in self.correct_list:
            cnt += sh.exec_i(f"update revise_items set mastery_level = mastery_level + 1 where revise_id in \
                            (select `respell_id` from `words` where `spelling` = '{word}');")
        self.prompt(f"\n正确单词{len(self.correct_list)}个，共{cnt}个单词重拼计划已更新")
        cnt = sh.exec_i("delete from `revise_items` where `mastery_level` is null;")
        self.prompt(f"\n其中共有{cnt}个单词已经完全消除")
        cnt = 0
        for word in self.wrong_list:
            alias = sh.fetchone(f"select `alias` from `words` where `spelling` = '{word}'")
            cnt += sh.word_renew_plan(word, 2, self.prompt, alias=alias, output_mode=0)
        self.prompt(f"\n另有拼错的单词{len(self.word_list)}个\n{cnt}个重新加入重拼计划")

    def close_window(self):
        self.top.withdraw()
        self.master.deiconify()


class RefreshWindow:
    def __init__(self, master):
        self.master = master
        self.top = tk.Toplevel(master)
        self.top.title("Refresh Window")
        self.top.protocol("WM_DELETE_WINDOW", self.close_window)
        self.button = tk.Button(self.top, text="hi", command=self.close_window, padx=3, pady=3)
        self.button.pack()

        # Implement the functionality for the Refresh Window here

    def close_window(self):
        self.top.withdraw()
        self.master.deiconify()


class ConfigWindow:
    def __init__(self, master):
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
            self.output_text.config(state="normal")
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
    RespellWindow(master)
    master.mainloop()