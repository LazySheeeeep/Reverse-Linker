from nltk.corpus import wordnet as wn
#import nltk
#nltk.download('wordnet')

# 输入要查询的单词
word = "incredulously"

# 查找该单词的所有 Synset
synsets = wn.synsets(word)
print(type(synsets[0]))
# 输出每个 Synset 的所有信息
if len(synsets) > 0:
    for synset in synsets:
        print("词义编号：", synset.offset())
        print("词义类别：", synset.pos())
        print("定义：", synset.definition())
        print("例句：", synset.examples())
        print("同义词：", [lemma.name() for lemma in synset.lemmas()])
        print("反义词：", [lemma.antonyms()[0].name() for lemma in synset.lemmas() if lemma.antonyms()])
        print("------------------------------")
else:
    print("未找到该单词的 Synset。")

# import ttkbootstrap as ttk
# from ttkbootstrap.constants import *
# from tkinter.filedialog import askopenfilename
# from ttkbootstrap.dialogs import Querybox
#
# def open_file():
#     path = askopenfilename()
#     file_select_btn.config(text=path)
#
# root = ttk.Window()
# file_select_btn = ttk.Button(root, text="选择文件", command=open_file)
# file_select_btn.grid(row=0, column=0, sticky=ttk.W, padx=10, pady=10)
#
#
# de2 = ttk.DateEntry(bootstyle="success", dateformat=r"%Y-%m-%d")  # r"%Y"
# de2.grid(row=0, column=1, sticky=ttk.W, padx=10, pady=10)
#
#
# def get_dataentry():
#     print(de2.entry.get())
#
#
# ttk.Button(root, text="submit", bootstyle=(PRIMARY, "outline-toolbutton"), command=get_dataentry) \
#     .grid(row=0, column=2, sticky=ttk.W, padx=10, pady=10)
# root.mainloop()
