import pymysql
import nltk
from nltk.corpus import wordnet as wn
from typing import Callable
from util import consultant as ct


nltk_pos_dict = {
    'a': 3,  # 形容词
    's': 3,  # 形容词
    'r': 4,  # 副词
    'n': 1,  # 名词
    'v': 2,  # 动词
    'g': 6,
    'x': 8,  # 感叹词
    'c': 9,  # 连词
    'p': 5,
}
pos_dict = {'O': 0, 'n': 1, 'v': 2, 'adj': 3, 'adv': 4, 'prep': 5, 'phr': 6, 'syn': 7, 'intj': 8, 'conj': 9}

db = pymysql.connect(
        host="localhost",
        user='root',
        password='1q2w3e4r',
        database='glossary'
    )
cursor = db.cursor()


def commit_and_start():
    cursor.execute('commit;')
    cursor.execute("start transaction;")


def exec_i(command: str) -> int:
    cursor.execute(command)
    return cursor.rowcount


def fetchall(command: str):
    cursor.execute(command)
    return cursor.fetchall()


def fetchone(command: str):
    cursor.execute(command)
    return cursor.fetchone()


def insert_synsets(spelling: str, synsets: [nltk.corpus.reader.wordnet.Synset],
                   output: Callable[[str], None]):
    insert_word_ids_command = "insert into `word_ids` values "
    insert_meanings_command = "insert into `meanings`(`meaning_id`,`pos_id`,`meaning`) values "
    insert_an_synonyms_command = "insert into `an_synonyms` values "
    insert_example_sentences_command = "insert into `example_sentences` (`meaning_id`, `sentence`) values "
    for synset in synsets:
        pos = nltk_pos_dict.get(synset.pos(), 0)
        meaning_id = synset.offset()
        insert_word_ids_command += f"('{spelling}', {meaning_id}),"
        insert_meanings_command += f"""({meaning_id}, {pos}, "{synset.definition().replace('"', "'")}"),"""
        for lemma in synset.lemmas():
            syn = lemma.name()
            if lemma.antonyms():
                ant = lemma.antonyms()[0].name()
                insert_an_synonyms_command += f"({meaning_id}, '{ant}', false),"
            insert_an_synonyms_command += f"({meaning_id}, '{syn}', true),"
        for example in synset.examples():
            ex = example.replace('"', "'")
            insert_example_sentences_command += f"""({meaning_id}, "{ex}"),"""
    cnt = exec_i(insert_meanings_command[:-1] + ';')
    output(f"\nmeanings：{cnt}")
    cnt = exec_i(insert_word_ids_command[:-1] + ';')
    output(f"\tword_ids：{cnt}")
    cnt = exec_i(insert_an_synonyms_command[:-1] + ';')
    output(f"\tan_synonyms：{cnt}")
    cnt = exec_i(insert_example_sentences_command[:-1] + ';')
    output(f"\texample_sentences：{cnt}√")


def insert_translations(origin, rigid_translations, output: Callable[[str], None]):
    command = "insert into `translations` values "
    for pos, trans in rigid_translations.items():
        pos_id = pos_dict.get(pos, 0)
        for tran in trans:
            command += f"('{origin}', '{pos_id}', '{tran}'),"
    output(f"\ntranslations：{exec_i(command[:-1] + ';')}")


def phrase_process(phrase: str, output: Callable[[str], None], note: str = None, related_word: str = None):
    output(f"\ncommit and start transaction\n查询{phrase}的中文释义...")
    commit_and_start()  # undo结点
    _, rigid_translations, examples = ct.rigid_bing_consult(phrase)
    output(f'√\ntranslations:{str(rigid_translations)}\n例句数：{len(examples)}')
    # 插入到数据库中
    cnt = exec_i(f"insert into `revise_items` values();")
    output(f"\nrevise_items：{cnt}")
    revise_id = cursor.lastrowid
    if related_word is None:
        cnt = exec_i(f"insert into `phrases` values('{phrase}', null, '{revise_id}');")
    else:
        cnt = exec_i(f"insert into `phrases` values('{phrase}', '{related_word}', );")
    output(f"\tphrases：{cnt}")
    insert_translations(phrase, rigid_translations, output)
    if note:
        output(f"""\tnotes：{exec_i(f"insert into `notes` values('{revise_id}', '{note}');")}""")
    if len(examples) > 0:
        command = "insert into `example_sentences` values"
        for i, example in enumerate(examples):
            if i > 9:  # 最多10句
                break
            command += f"""("{phrase}", null, "{example.replace('"',"'")}"),"""
        cnt = exec_i(command[:-1] + ';')
        output(f"\texample_sentences改变行数：{cnt}√")
    else:
        output("\n无例句被插入")


def word_renew(word: str, op: int, note: str = None, alias: str = None):
    cnt = 0
    if op == 1 or op == 3:
        if note:
            cnt += fetchone(f"call `renew_refresh_plan_for_word`('{word}', '{note}');")
        else:
            cnt += fetchone(f"call `renew_refresh_plan_for_word`('{word}', null);")
    if op == 2 or op == 3:
        if alias:
            cnt += fetchone(f"call `renew_respell_plan_for_word`('{word}', '{alias}');")
        else:
            cnt += fetchone(f"call `renew_respell_plan_for_word`('{word}', null);")
    return cnt


def word_process(word:str, op: int, output: Callable[[str], None], note=None, alias: str = None):
    output(f"\ncommit and start transaction\n查询{word}的中英释义...")
    commit_and_start()  # undo结点
    phonetic, rigid_translations, _ = ct.rigid_bing_consult(word)
    output(f"\n中√{str(rigid_translations)}")
    synsets = wn.synsets(word)
    if len(synsets) > 0:
        output(f"\n英√查到{len(synsets)}条")
    else:
        output("\n未查询到英文释义，加入复习计划失败")
        return
    cnt = 0  # 计数
    # 新增复习计划
    if op == 3:
        cnt = exec_i(f"insert into `revise_items` values(),();")
    else:
        cnt = exec_i(f"insert into `revise_items` values();")
    output(f"\nrevise_items改变行数：{cnt}")
    # 插入words
    if op == 3:
        cnt = exec_i(f"""insert into `words`(\
        `spelling`,`phonetic`,`refresh_id`,`respell_id`) values(\
        '{word}',"{phonetic}",last_insert_id(),last_insert_id()+1);""")  # 经测试，插入多个时返回第一个插入的id
    elif op == 1:
        cnt = exec_i(f"""insert into `words`(\
                    `spelling`,`phonetic`,`refresh_id`) values(\
                    '{word}',"{phonetic}",last_insert_id());""")
    elif op == 2:
        cnt = exec_i(f"""insert into `words`(\
                    `spelling`,`phonetic`,`respell_id`) values(\
                    '{word}',"{phonetic}",last_insert_id());""")
    if alias:
        exec_i(f'update `words` set `alias` = "{alias}" where `spelling` = "{word}";')
    output(f"\twords改变行数：{cnt}")
    # 插入notes
    if note:
        cnt = exec_i(f"insert into `notes` values (last_insert_id(),'{note}')")
        output(f"\tnotes改变行数：{cnt}")
    # 插入meanings, an_syn, examples, word_ids
    insert_synsets(word, synsets, output)
    # 插入translations
    insert_translations(word, rigid_translations, output)
