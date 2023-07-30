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
    prompt_text = f"mastery level:{level}"
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
        self.top.geometry("930x590")
        self.top.update()

        self.wrong_list_frame = tk.LabelFrame(text="错误的", master=self.top, style=DANGER, width=200, height=600)
        self.wrong_list_frame.place(x=730, y=10)
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

        self.all_tuples = sh.fetchall("select * from `respell_words_today` limit 30;")
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
        if self.state == "RECALL":
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
            self.state = "RECALL"
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
        if (self.state == "RECALL" or self.state == "MUST_SUBMIT") and self.wrong_list:
            self.wrong_text.config(state=tk.NORMAL)
            self.wrong_text.delete("end-2l", "end-1c")  # 删除最后一行的文本
            self.wrong_text.config(state=tk.DISABLED)
            self.add_correct(self.wrong_list.pop(-1))
        else:
            self.prompt("\nnothing to recall")

    def update_mastery_level(self, word):
        cnt = sh.exec_i(f"update revise_items set mastery_level = mastery_level + 1 where revise_id in\
            (select respell_id from words where spelling = '{word}');")
        if cnt:
            self.correct_update_count += 1
            self.prompt(f"\n{word}√")
            cnt2 = sh.exec_i("delete from `revise_items` where `mastery_level` is null;")
            if cnt2 >= 1:
                self.prompt(f"\n单词{word}重拼计划已完成")
                self.delete_count += 1
                if cnt2 > 1:
                    self.prompt(f"\n有其他{cnt2-1}个单词被删去")
        else:
            self.prompt(f"\n单词{word}更新失败")

    def end(self):
        self.prompt(f"\n拼对{len(self.correct_list)}\t更新{self.correct_update_count}\t消除{self.delete_count}")
        cnt = 0
        for word in self.wrong_list:
            alias = sh.fetchone(f"select `alias` from `words` where `spelling` = '{word}'")
            if alias == (None,):
                alias = None
            cnt += sh.word_renew_plan(word, 2, self.prompt, alias=alias, output_mode=0)
        self.prompt(f"\n拼错{len(self.wrong_list)}\t重新加入{cnt}")
        sh.db.commit()
        self.prompt(f"\ncommitted")

    def close_window(self):
        self.top.withdraw()
        self.master.deiconify()


class RefreshWindow:
    def __init__(self, master, alpha):
        self.master = master
        self.top = tk.Toplevel(master, alpha=alpha)
        self.top.title("Refresh Window")
        self.top.protocol("WM_DELETE_WINDOW", self.close_window)
        self.top.protocol("WM_DEICONIFY", self.start)
        self.top.geometry("1330x1045")
        self.top.update()
        self.top.bind("<KeyPress-space>", lambda _=None: self.on_confirm())
        self.top.bind("<Tab>", lambda _=None: self.on_tab())
        self.top.bind("<KeyPress-q>", lambda _=None: self.switch_to_misc())
        self.top.bind("<KeyPress-x>", lambda _=None: self.on_no())
        self.top.bind("<KeyPress-r>", lambda _=None: self.recall())

        self.correct_list_frame = tk.LabelFrame(text="pass", master=self.top, style=PRIMARY, width=200, height=900)
        self.correct_list_frame.place(x=10, y=10)
        self.center_frame = tk.Labelframe(text="refresh", master=self.top, style=PRIMARY, width=890, height=900)
        self.center_frame.place(x=210, y=10)
        self.wrong_list_frame = tk.LabelFrame(text="stall", master=self.top, style=DANGER, width=200, height=900)
        self.wrong_list_frame.place(x=1130, y=10)

        # center frame
        nb_w, nb_h = 890, 650
        self.nb = tk.Notebook(master=self.center_frame, width=nb_w, height=nb_h)
        self.nb.grid(row=0, column=0, columnspan=3, padx=10, pady=30)
        self.meaning_text = tk.Text(master=self.nb, width=nb_w, height=nb_h, state=tk.NORMAL)
        self.nb.add(self.meaning_text, text="en", sticky=tk.W)
        self.translation_text = tk.Text(master=self.nb, width=nb_w, height=nb_h, state=tk.NORMAL)
        self.nb.add(self.translation_text, text="cn", sticky=tk.W)
        self.misc_text = tk.Text(master=self.nb, width=nb_w, height=nb_h, state=tk.NORMAL)
        self.nb.add(self.misc_text, text="misc", sticky=tk.W)
        self.nb_state = "en"

        self.outcome_text = tk.Text(self.center_frame, width=60, height=5, state=tk.DISABLED)
        self.outcome_text.grid(row=1, column=0, columnspan=3, padx=10, pady=10)

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
        self.all_vocab_tuples = []
        self.all_words_count = lambda: int(sh.fetchone("select count(*) from `refresh_words_today`;")[0])
        self.all_phrases_count = lambda: int(sh.fetchone("select count(*) from `refresh_phrases_today`;")[0])
        self.wrong_list = []
        self.correct_list = []
        self.word_dict = {}
        self.current_index = -1  # 指向第几个单词
        self.state = "IDLE"  # on_submit函数根据当前状态来决定prompt，IDLE表示什么都不做
        self.can_recall = False
        self.correct_update_count = 0
        self.delete_count = 0
        self.start()

    def fetch_vocab(self):
        # 30 words and 5 phrases once at most
        word_tuples = sh.fetchall("select * from `refresh_words_today` limit 30;")
        phrase_tuples = sh.fetchall("select * from `refresh_phrases_today` limit 5;")
        for word_tuple in word_tuples:
            self.all_vocab_tuples.append((True, word_tuple))
        for phrase_tuple in phrase_tuples:
            self.all_vocab_tuples.append((False, phrase_tuple))

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
        if cnt:
            self.correct_update_count += 1
            self.prompt(f"\n{word}√")
            cnt2 = sh.exec_i("delete from `revise_items` where `mastery_level` is null;")
            if cnt2 >= 1:
                self.prompt(f"\n单词{word}refresh计划已完成")
                self.delete_count += 1
                if cnt2 > 1:
                    self.prompt(f"\n有其他{cnt2 - 1}个单词被删去")
        else:
            self.prompt(f"\n单词{word}更新失败")

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
        results = sh.fetchall(f"select `abbreviation`, `meaning`, `meaning_id`\
                                 from `meanings`\
                                 join `part_of_speeches` using (`pos_id`)\
                                 where `meaning_id` in\
                                 (select meaning_id from word_ids where spelling = '{word}');")
        self.word_dict.clear()
        for (pos, meaning, meaning_id) in results:
            if pos in self.word_dict:
                self.word_dict[pos].append((meaning_id, meaning))
            else:
                self.word_dict[pos] = [(meaning_id, meaning)]
        self.meaning_text.config(state=tk.NORMAL)
        self.meaning_text.delete("1.0", tk.END)
        self.meaning_text.insert(tk.END, f"mastery level:{level}")
        for pos in self.word_dict.keys():
            self.meaning_text.insert(tk.END, f"\n{pos}")
            for (_, meaning) in self.word_dict[pos]:
                self.meaning_text.insert(tk.END, '\n  ' + meaning)
            self.misc_text.insert(tk.END, '\n')
        self.meaning_text.config(state=tk.DISABLED)

    def prompt_note(self, _id, vocab):
        note = sh.fetchone(f"select `content` from `notes` where `revise_id` = {_id};")
        if note:
            Messagebox.show_info(message=f"{vocab}:\n\t{note[0]}", parent=self.top, title="Note")

    def prompt_example_sentences_for_phrase(self, phrase):
        self.misc_text.config(state=tk.NORMAL)
        self.misc_text.delete("1.0", tk.END)
        self.misc_text.insert(tk.END, f"{phrase}'s example sentences:")
        sentences = sh.fetchall(f"select `sentence` from `example_sentences` where `phrase` = '{phrase}';")
        if sentences:
            for sentence in sentences:
                self.misc_text.insert(tk.END, f'\n--{sentence[0]}')
        else:
            self.misc_text.insert(tk.END, f"\n{phrase} has no example sentences:(")
        self.misc_text.config(state=tk.DISABLED)

    # example sentences and antonyms&synonyms prompting
    def prompt_example_sentences_for_word(self, word):
        self.misc_text.config(state=tk.NORMAL)
        self.misc_text.delete("1.0", tk.END)
        self.misc_text.insert(tk.END, f"{word}'s dictionary:")
        for pos in self.word_dict.keys():
            self.misc_text.insert(tk.END, f"\n{pos}")
            for (meaning_id, meaning) in self.word_dict[pos]:
                self.misc_text.insert(tk.END, f'\n>>{meaning}')
                sentences = sh.fetchall(
                    f"select `sentence` from `example_sentences` where `meaning_id` = {meaning_id};")
                an_synonyms = sh.fetchall(
                    f"select `word`, `is_synonym` from `an_synonyms` where `meaning_id` = {meaning_id};")
                if an_synonyms and len(an_synonyms) > 1 or an_synonyms[0][0] != word:
                    self.misc_text.insert(tk.END, f'\n ')
                    for (an_synonym, is_syn) in an_synonyms:
                        if an_synonym != word:
                            if is_syn:
                                self.misc_text.insert(tk.END, " " + an_synonym)
                            else:  # is antonym
                                self.misc_text.insert(tk.END, " *" + an_synonym)
                if sentences:
                    for sentence in sentences:
                        self.misc_text.insert(tk.END, f'\n--{sentence[0]}')  # sentence is a tuple of one item
        self.misc_text.config(state=tk.DISABLED)

    def start(self):
        self.current_index = -1
        if self.all_words_count() == 0 and self.all_phrases_count() == 0:
            Messagebox.show_info(message="Nothing more to refresh today.", parent=self.top)
            self.close_window()
            return
        result = Messagebox.show_question(message=f"Today's task:\ntotal words：{self.all_words_count()}\n\
total phrases:{self.all_phrases_count()}\nReady to start?\n(no more than 30 words & 5 phrases once)",
                                          parent=self.top)
        if result == "确认":
            self.prompt("Start：")
            self.fetch_vocab()
            if self.can_move_on():
                self.move_on()
        else:
            self.prompt("\n取消操作")

    def get_vocab(self):
        return self.all_vocab_tuples[self.current_index]

    def on_confirm(self):
        if self.state == "RECALL":  # 给出答案
            self.state = "CHECK/STRENGTHEN"
            self.switch_to_misc()  # show the misc window when checking
            is_word, vocab_tuple = self.get_vocab()
            if is_word:
                _id, word, phonetic, _ = vocab_tuple
                self.prompt(f"\n{word}\t{phonetic}")
                # 给出例句和同近义词
                self.prompt_example_sentences_for_word(word)
                self.prompt_note(_id, word)
            else:
                _id, phrase, _, _ = vocab_tuple
                self.prompt(f"\n{phrase}")
                self.prompt_example_sentences_for_phrase(phrase)
                self.prompt_note(_id, phrase)
        elif self.state == "CHECK/STRENGTHEN":
            is_word, vocab_tuple = self.get_vocab()
            _id = vocab_tuple[0]
            vocab = vocab_tuple[1]
            self.add_correct(_id, vocab)
            self.can_recall = True
            if self.can_move_on():
                self.move_on()
        else:
            self.prompt(f"\ncurrent state {self.state} has no operation.")

    def on_no(self):
        if self.state == "RECALL" or self.state == "CHECK/STRENGTHEN":
            is_word0, tuple0 = self.get_vocab()
            _id = tuple0[0]
            vocab = tuple0[1]
            self.add_wrong(_id, vocab)
            if self.can_move_on():
                self.move_on()
            self.prompt(f"{vocab} x")
        else:
            self.prompt(f"\ncurrent state {self.state} has no operation.")

    def can_move_on(self):
        self.current_index += 1
        if self.current_index >= len(self.all_vocab_tuples):
            self.group_settlement()
            if self.all_words_count() == 0 and self.all_phrases_count() == 0:
                Messagebox.show_info(message="Nothing more to refresh today.", parent=self.top)
                self.close_window()
                return False
            else:
                result = Messagebox.show_question(message=f"Still have {self.all_words_count()} words\
and {self.all_phrases_count()} phrases to refresh.\nReady to move on?", parent=self.top)
                if result == "确认":
                    self.fetch_vocab()
                    self.current_index = 0
                    return True
                else:
                    self.state = "END"
                    self.can_recall = False
                    return False
        else:
            return True

    def move_on(self):
        self.state = "RECALL"
        is_word, tuple1 = self.get_vocab()
        if is_word:
            _, word, _, level = tuple1
            self.prompt_translations(word, level)
            self.prompt_meanings(word, level)
            self.switch_to_en()
        else:
            _, phrase, relate_word, level = tuple1
            self.meaning_text.config(state=tk.NORMAL)
            self.meaning_text.delete("1.0", tk.END)
            self.meaning_text.insert(tk.END, "phrase: no data.")
            self.meaning_text.config(state=tk.DISABLED)
            if relate_word:
                self.prompt_translations(phrase, level)
                Messagebox.show_info(parent=self.top, message=relate_word)
            else:
                self.prompt_translations(phrase, level)
            self.switch_to_cn()

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

    def group_settlement(self):
        self.prompt(f"\n熟悉{len(self.correct_list)}\t更新{self.correct_update_count}\t消除{self.delete_count}")
        cnt = 0
        for _id, word in self.wrong_list:
            note = sh.fetchone(f"select `content` from `notes` where `revise_id` = '{_id}'")
            cnt += sh.word_renew_plan(word, 1, self.prompt, note=note, output_mode=0)
        self.prompt(f"\n不熟{len(self.wrong_list)}\t重开{cnt}")
        self.wrong_list.clear()
        self.correct_list.clear()
        self.all_vocab_tuples.clear()
        sh.db.commit()
        self.prompt(f"\ncommitted")

    def on_tab(self):
        if self.nb_state == "en":
            self.switch_to_cn()
        else:
            self.switch_to_en()

    def switch_to_en(self):
        self.nb_state = "en"
        self.nb.select(self.meaning_text)

    def switch_to_cn(self):
        self.nb_state = "cn"
        self.nb.select(self.translation_text)

    def switch_to_misc(self):
        self.nb_state = 'misc'
        self.nb.select(self.misc_text)


if __name__ == "__main__":
    master = tk.Window()
    RespellWindow(master, 0.85)
    master.mainloop()
