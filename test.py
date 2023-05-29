from nltk.corpus import wordnet as wn
# import nltk
# nltk.download('wordnet')

# 输入要查询的单词
word = "incredulously"

# 查找该单词的所有 Synset
synsets = wn.synsets(word)
# print(type(synsets[0]))
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
