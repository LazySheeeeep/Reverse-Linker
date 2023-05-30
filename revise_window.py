import tkinter as tk
from tkinter import messagebox
from util import sqlhelper as sh


# todo: implement
class RespellWindow:
    def __init__(self, master):
        self.master = master
        self.top = tk.Toplevel(master)
        self.top.title("Respell Window")
        self.top.geometry("400x300")
        self.top.protocol("WM_DELETE_WINDOW", self.close_window)

        self.word_list = self.get_respell_list()
        self.current_index = 0

        self.prompt_label = tk.Label(self.top, text="")
        self.prompt_label.pack(pady=10)

        self.translation_label = tk.Label(self.top, text="")
        self.translation_label.pack(pady=10)

        self.entry = tk.Entry(self.top, width=30)
        self.entry.pack(pady=10)
        self.entry.bind("<Return>", self.check_answer)
        self.entry.focus_set()

        self.wrong_list = []
        self.wrong_list_panel = tk.Frame(self.top)
        self.wrong_list_panel.pack(pady=10)

        self.recall_button = tk.Button(self.top, text="Recall", width=10, command=self.recall_word)
        self.recall_button.pack(pady=10)

        self.show_next_word()

    def get_respell_list(self):
        respell_list = sh.fetchall("SELECT * FROM revise_list_today WHERE type='respell'")
        return respell_list

    def show_next_word(self):
        if self.current_index < len(self.word_list):
            word = self.word_list[self.current_index]
            self.prompt_label.configure(text=word["prompt"])
            self.translation_label.configure(text="")
            self.entry.delete(0, tk.END)
        else:
            messagebox.showinfo("Finished", "You have finished respelling all the words.")

    def check_answer(self, event):
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

    def show_wrong_list(self):
        for widget in self.wrong_list_panel.winfo_children():
            widget.destroy()

        for i, word in enumerate(self.wrong_list):
            label = tk.Label(self.wrong_list_panel, text=word["prompt"])
            label.pack()

    def recall_word(self):
        if self.wrong_list:
            word = self.wrong_list.pop()
            self.update_mastery_level(word["respell_id"])
            self.show_wrong_list()

    def update_mastery_level(self, respell_id):
        sh.exec_i(f"UPDATE revise_items SET mastery_level = mastery_level + 1 WHERE revise_id = {respell_id}")

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
