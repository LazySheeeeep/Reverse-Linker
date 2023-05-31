import ttkbootstrap as tk
from ttkbootstrap.constants import *
from tkinter import messagebox
from util import sqlhelper as sh


# todo: implement
def generate_translation_for_word(word, level):
    translations = sh.fetchall(f"select `abbreviation`, `translation`\
                                 from `translations`\
                                 join `part_of_speeches` using (`pos_id`)\
                                 where `origin` = '{word}'")
    d = {}
    for (pos, translation) in translations:
        if pos in d:
            d[pos].append(translation)
        else:
            d[pos] = [translation]
    prompt_text = f"\n\n\nmastery_level:{level}"
    for key in d.keys():
        prompt_text += f"\n{key}:\n"
        prompt_text += '；'.join(d[key])
    return prompt_text


def collate(str1: str, str2: str) -> int:
    idx = 0
    min_len = min(len(str1), len(str2))
    while min_len > idx:
        if str1[idx] != str2[idx]:
            return idx
        idx += 1
    return min_len


class RespellWindow:
    def __init__(self, master):
        self.master = master
        self.top = tk.Toplevel(master)
        self.top.title("Respell Window")
        self.top.protocol("WM_DELETE_WINDOW", self.close_window)
        self.top.protocol("WM_DEICONIFY", self.start)
        self.top.geometry("870x620")
        self.top.update()

        self.wrong_list_frame = tk.LabelFrame(text="错误的", master=self.top, style=DANGER, width=200, height=600)
        self.wrong_list_frame.place(x=670, y=10)
        self.correct_list_frame = tk.LabelFrame(text="正确的", master=self.top, style=PRIMARY, width=200, height=600)
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

        tk.Button(self.center_frame, text="Recall", width=10, bootstyle="danger", command=self.recall_word) \
            .grid(row=2, column=0, padx=10, pady=5)

        self.correct_text = tk.Text(self.correct_list_frame, width=12, height=15, state=tk.DISABLED)
        self.correct_text.pack(padx=5, pady=30)
        self.wrong_text = tk.Text(self.wrong_list_frame, width=12, height=15, state=tk.DISABLED)
        self.wrong_text.pack(padx=5, pady=30)

        self.all_tuples = sh.fetchall("select * from `respell_words_today`;")
        self.total_amount = len(self.all_tuples)
        self.wrong_list = []
        self.correct_list = []
        self.current_index = -1  # 指向第几个单词
        self.state = "IDLE"  # on_submit函数根据当前状态来决定prompt，IDLE表示什么都不做

        self.correct_update_count = 0
        self.wrong_update_count = 0
        self.delete_count = 0
        self.start()

    def prompt(self, msg: str):
        self.prompt_text.config(state=tk.NORMAL)
        self.prompt_text.insert(tk.END, msg)
        self.prompt_text.see(tk.END)
        self.prompt_text.config(state=tk.DISABLED)

    def add_wrong(self, word):
        self.wrong_list.append(word)
        self.wrong_text.config(state=tk.NORMAL)
        self.wrong_text.insert(tk.E, word + '\n')
        self.wrong_text.see(tk.END)
        self.wrong_text.config(state=tk.DISABLED)

    def add_correct(self, word):
        self.update_mastery_level(word)
        self.correct_list.append(word)
        self.correct_text.config(state=tk.NORMAL)
        self.correct_text.insert(tk.E, word + '\n')
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
            self.move_on()
        else:
            self.prompt("\n取消操作")

    def on_submit(self, event):
        ans = self.entry.get().strip()
        self.entry.delete(0, tk.END)
        if self.state == "THINKING":
            _id, word, phonetic, alias, level = self.all_tuples[self.current_index]
            if ans == '':
                self.prompt(f"\n{phonetic}")
                self.state = "MUST_SUBMIT"
            else:
                _id, word, phonetic, alias, level = self.all_tuples[self.current_index]
                self.check(ans, word, alias)  # 判断是否正确
                self.move_on()
        elif self.state == "MUST_SUBMIT":
            _id, word, phonetic, alias, level = self.all_tuples[self.current_index]
            if ans == '':  # 一看就会，懒得写直接跳过
                self.add_correct(word)
                self.move_on()
            else:
                self.check(ans, word, alias)  # 判断是否正确
                self.move_on()
        else:
            self.prompt(f"\ncurrent state {self.state} has no operation.")

    def move_on(self):
        self.current_index += 1
        if self.current_index >= self.total_amount:
            self.state = "END"
            self.end()
        else:
            self.state = "THINKING"
            _, new_word, _, _, level = self.all_tuples[self.current_index]
            prompt_content = generate_translation_for_word(word=new_word, level=level)
            self.prompt(prompt_content)

    def check(self, ans, word, alias):
        if ans == word or alias and ans == alias:
            self.prompt("√")
            self.add_correct(word)
        else:
            self.prompt(f"\n{ans}×")
            self.prompt(f"\n{word}\n")
            idx = collate(ans, word)
            self.prompt(' ' * idx)
            self.prompt('^')
            self.add_wrong(word)

    def recall_word(self):
        if self.wrong_list:
            self.wrong_text.config(state=tk.NORMAL)
            self.wrong_text.delete("end-2l", "end-1c")  # 删除最后一行的文本
            self.wrong_text.config(state=tk.DISABLED)
            self.add_correct(self.wrong_list.pop(-1))
        else:
            self.prompt("\nnothing to recall")

    def update_mastery_level(self, word):
        cnt = sh.exec_i(f"update revise_items set mastery_level = mastery_level + 1 where revise_id in\
            (select respell_id from words where spelling = '{word}');")
        cnt2 = sh.exec_i("delete from `revise_items` where `mastery_level` is null;")
        self.correct_update_count += cnt
        self.prompt(f"\n{word}√:{cnt}")
        if cnt2 == 1:
            self.prompt(f"\n单词{word}重拼计划已完成{cnt}")

    def end(self):
        self.prompt(f"\n拼对{len(self.correct_list)}\t更新{self.correct_update_count}\t消除{self.delete_count}")
        cnt = 0
        for word in self.wrong_list:
            alias = sh.fetchone(f"select `alias` from `words` where `spelling` = '{word}'")
            cnt += sh.word_renew_plan(word, 2, self.prompt, alias=alias, output_mode=0)
        self.prompt(f"\n拼错{len(self.wrong_list)}\t重新加入{cnt}")
        sh.db.commit()
        self.prompt(f"\ncommitted")

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
