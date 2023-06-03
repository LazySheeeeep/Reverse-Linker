import ttkbootstrap as tk
from ttkbootstrap.constants import *
from ttkbootstrap.dialogs import Messagebox
from util import sqlhelper as sh


def generate_translation(word, level):
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
    prompt_text = f"mastery_level:{level}"
    for key in d.keys():
        prompt_text += f"\n{key}\n  "
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
    def __init__(self, master, alpha):
        self.master = master
        self.top = tk.Toplevel(master, alpha=alpha)
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
        self.prompt_text = tk.Text(self.center_frame, width=30, height=12, state=tk.DISABLED, font=("Courier", 10))
        self.prompt_text.grid(row=0, column=0, padx=10, pady=30)

        self.entry = tk.Entry(self.center_frame, width=30)
        self.entry.grid(row=1, column=0, padx=10, pady=5)
        self.entry.bind("<Return>", self.on_submit)
        self.entry.focus_set()

        tk.Button(self.center_frame, text="Recall", width=10, style="danger", command=self.recall_word) \
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
        self.wrong_text.insert(tk.END, word + '\n')
        self.wrong_text.see(tk.END)
        self.wrong_text.config(state=tk.DISABLED)

    def add_correct(self, word):
        self.update_mastery_level(word)
        self.correct_list.append(word)
        self.correct_text.config(state=tk.NORMAL)
        self.correct_text.insert(tk.END, word + '\n')
        self.correct_text.see(tk.END)
        self.correct_text.config(state=tk.DISABLED)

    def start(self):
        self.current_index = -1
        if self.total_amount == 0:
            Messagebox.show_info(message="今日计划已经完成", parent=self.top)
            self.close_window()
            return
        result = Messagebox.show_question(message=f"\n今日需重拼：{self.total_amount}词，是否开始？", parent=self.top)
        if result == "确认":
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
            prompt_content = generate_translation(word=new_word, level=level)
            self.prompt(f"\n\n{prompt_content}")

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
        if (self.state == "THINKING" or self.state == "MUST_SUBMIT") and self.wrong_list:
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


# todo: implement 跳过部分
class RefreshWindow:
    def __init__(self, master, alpha):
        self.master = master
        self.top = tk.Toplevel(master, alpha=alpha)
        self.top.title("Refresh Window")
        self.top.protocol("WM_DELETE_WINDOW", self.close_window)
        self.top.protocol("WM_DEICONIFY", self.start)
        self.top.geometry("1330x1045")
        self.top.update()
        self.top.bind("<Return>", lambda _=None: self.on_confirm())
        self.top.bind("<Tab>", lambda _=None: self.on_tab())

        self.correct_list_frame = tk.LabelFrame(text="pass", master=self.top, style=PRIMARY, width=200, height=900)
        self.correct_list_frame.place(x=10, y=10)
        self.center_frame = tk.Labelframe(text="refresh", master=self.top, style=PRIMARY, width=890, height=900)
        self.center_frame.place(x=210, y=10)
        self.wrong_list_frame = tk.LabelFrame(text="stall", master=self.top, style=DANGER, width=200, height=900)
        self.wrong_list_frame.place(x=1130, y=10)

        # 中央Frame
        self.nb = tk.Notebook(master=self.center_frame, width=890, height=300)
        self.nb.grid(row=0, column=0, columnspan=3, padx=10, pady=30)
        self.meaning_text = tk.Text(master=self.nb, width=890, height=300, state=tk.NORMAL)
        self.nb.add(self.meaning_text, text="en", sticky=tk.W)
        self.translation_text = tk.Text(master=self.nb, width=890, height=300, state=tk.NORMAL)
        self.nb.add(self.translation_text, text="cn", sticky=tk.W)
        self.nb_state = "en"

        self.outcome_text = tk.Text(self.center_frame, width=60, height=15, state=tk.DISABLED)
        self.outcome_text.grid(row=1, column=0, columnspan=3, padx=10, pady=30)

        tk.Button(self.center_frame, text="Recall", width=10, style="danger", command=self.recall)\
            .grid(row=2, column=0, padx=10, pady=5)
        tk.Button(self.center_frame, text="√", width=10, style=PRIMARY, command=self.on_confirm)\
            .grid(row=2, column=1, padx=10, pady=5)
        tk.Button(self.center_frame, text="×", width=10, style="danger", command=self.on_no)\
            .grid(row=2, column=2, padx=10, pady=5)

        self.correct_text = tk.Text(self.correct_list_frame, width=12, height=30, state=tk.DISABLED)
        self.correct_text.pack(padx=5, pady=60, side=tk.TOP)
        self.wrong_text = tk.Text(self.wrong_list_frame, width=12, height=30, state=tk.DISABLED)
        self.wrong_text.pack(padx=5, pady=60, side=tk.TOP)
        # 一次最多100个单词
        self.all_word_tuples = sh.fetchall("select * from `refresh_words_today` limit 100;")
        self.all_phrase_tuples = sh.fetchall("select * from `refresh_phrases_today`;")
        self.all_vocab_tuples = []
        for word_tuple in self.all_word_tuples:
            self.all_vocab_tuples.append((True, word_tuple))
        for phrase_tuple in self.all_phrase_tuples:
            self.all_vocab_tuples.append((False, phrase_tuple))
        self.total_amount = len(self.all_vocab_tuples)
        self.wrong_list = []
        self.correct_list = []
        self.current_index = -1  # 指向第几个单词
        self.state = "IDLE"  # on_submit函数根据当前状态来决定prompt，IDLE表示什么都不做
        self.can_recall = False
        self.correct_update_count = 0
        self.wrong_update_count = 0
        self.delete_count = 0
        self.start()

    def prompt(self, msg: str):
        self.outcome_text.config(state=tk.NORMAL)
        self.outcome_text.insert(tk.END, msg)
        self.outcome_text.see(tk.END)
        self.outcome_text.config(state=tk.DISABLED)

    def close_window(self):
        self.top.withdraw()
        self.master.deiconify()

    def update_mastery_level(self, _id, word):
        cnt = sh.exec_i(f"update revise_items set mastery_level = mastery_level + 1 where revise_id = {_id};")
        cnt2 = sh.exec_i("delete from `revise_items` where `mastery_level` is null;")
        self.correct_update_count += cnt
        self.prompt(f"\n{word}√:{cnt}")
        if cnt2 == 1:
            self.prompt(f"\n{word}重现计划已完成{cnt}")

    def add_wrong(self, _id, word):
        self.wrong_list.append((_id, word))
        self.wrong_text.config(state=tk.NORMAL)
        self.wrong_text.insert(tk.END, word + '\n')
        self.wrong_text.see(tk.END)
        self.wrong_text.config(state=tk.DISABLED)

    def add_correct(self, _id, word):
        sh.commit_and_start()
        self.update_mastery_level(_id, word)
        self.correct_list.append((_id, word))
        self.correct_text.config(state=tk.NORMAL)
        self.correct_text.insert(tk.END, word + '\n')
        self.correct_text.see(tk.END)
        self.correct_text.config(state=tk.DISABLED)

    def prompt_translations(self, word, level):
        content = generate_translation(word, level)
        self.translation_text.config(state=tk.NORMAL)
        self.translation_text.delete("1.0", tk.END)
        self.translation_text.insert(tk.END, content)
        self.translation_text.config(state=tk.DISABLED)

    def prompt_meanings(self, word, level):
        results = sh.fetchall(f"select `abbreviation`, `meaning`\
                                         from `meanings`\
                                         join `part_of_speeches` using (`pos_id`)\
                                         where `meaning_id` in\
                                         (select meaning_id from word_ids where spelling = '{word}');")
        d = {}
        for (pos, meaning) in results:
            if pos in d:
                d[pos].append(meaning)
            else:
                d[pos] = [meaning]
        self.meaning_text.config(state=tk.NORMAL)
        self.meaning_text.delete("1.0", tk.END)
        self.meaning_text.insert(tk.END, f"mastery level:{level}\n")
        for key in d.keys():
            self.meaning_text.insert(tk.END, f"{key}\n  ")
            self.meaning_text.insert(tk.END, '\n  '.join(d[key]))
            self.meaning_text.insert(tk.END, '\n')
        self.meaning_text.config(state=tk.DISABLED)

    def start(self):
        self.current_index = -1
        if self.total_amount == 0:
            Messagebox.show_info(message="今日计划已经完成", parent=self.top)
            self.close_window()
            return
        result = Messagebox.show_question(message=f"\n今日计划共：{self.total_amount}词，是否开始？", parent=self.top)
        if result == "确认":
            self.prompt("Start：")
            if self.can_move_on():
                self.move_on()
        else:
            self.prompt("\n取消操作")

    def get_vocab(self):
        return self.all_vocab_tuples[self.current_index]

    def on_confirm(self):
        if self.state == "THINKING":  # 给出答案
            self.state = "REMIND"
            is_word0, tuple0 = self.get_vocab()
            if is_word0:
                _id0, word0, phonetic0, level0 = tuple0
                self.prompt(f"\n{word0}\t{phonetic0}")
                # todo: 给出例句和同近义词以及笔记，先跳过
            else:
                _id0, phrase0, relate_word, level0 = tuple0
                self.prompt(f"\n{phrase0}")
                # todo: 给出例句，先跳过
        elif self.state == "REMIND":
            is_word0, tuple0 = self.get_vocab()
            _id0 = tuple0[0]
            vocab0 = tuple0[1]
            self.add_correct(_id0, vocab0)
            self.can_recall = True
            if self.can_move_on():
                self.move_on()
        else:
            self.prompt(f"\ncurrent state {self.state} has no operation.")

    def on_no(self):
        is_word0, tuple0 = self.get_vocab()
        _id = tuple0[0]
        vocab = tuple0[1]
        self.add_wrong(_id, vocab)
        if self.can_move_on():
            self.move_on()

    def can_move_on(self):
        self.current_index += 1
        if self.current_index >= self.total_amount:
            self.state = "END"
            self.current_index = self.total_amount
            self.end()
            return False
        else:
            return True

    def move_on(self):
        is_word, tuple1 = self.get_vocab()
        if is_word:
            _, word, _, level = tuple1
            self.prompt_translations(word, level)
            self.prompt_meanings(word, level)
        else:
            _, phrase, relate_word, level = tuple1
            if relate_word:
                self.prompt_translations(phrase, level)
                Messagebox.show_info(parent=self.top, message=relate_word)
            else:
                self.prompt_translations(phrase, level)
        self.state = "THINKING"

    def recall(self):
        if self.can_recall:
            self.correct_text.config(state=tk.NORMAL)
            self.correct_text.delete("end-2l", "end-1c")  # 删除最后一行的文本
            self.correct_text.config(state=tk.DISABLED)
            _id, word = self.correct_list.pop(-1)
            self.add_wrong(_id, word)
            sh.exec_i("rollback;")
            self.prompt(f"\nrecall {word} to stall")
            self.can_recall = False
        else:
            self.prompt("\nnothing to recall")

    def end(self):
        self.prompt(f"\n熟悉{len(self.correct_list)}\t更新{self.correct_update_count}\t消除{self.delete_count}")
        cnt = 0
        for _id, word in self.wrong_list:
            note = sh.fetchone(f"select `content` from `notes` where `revise_id` = '{_id}'")
            cnt += sh.word_renew_plan(word, 1, self.prompt, note=note, output_mode=0)
        self.prompt(f"\n不熟{len(self.wrong_list)}\t重新加入{cnt}")
        self.wrong_list.clear()
        sh.db.commit()
        self.prompt(f"\ncommitted")

    def on_tab(self):
        if self.nb_state == "en":
            self.nb_state = "cn"
            self.nb.select(self.translation_text)
        else:
            self.nb_state = "en"
            self.nb.select(self.meaning_text)


if __name__ == "__main__":
    master = tk.Window()
    RespellWindow(master, 0.85)
    master.mainloop()
