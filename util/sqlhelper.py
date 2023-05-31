import threading
from pymysql.err import IntegrityError
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
                   output: Callable[[str], None], output_mode=1):
    insert_word_ids_command = """insert into `word_ids` values """
    insert_an_synonyms_command = """insert into `an_synonyms` values """
    insert_example_sentences_command = """insert into `example_sentences` (`meaning_id`, `sentence`) values """
    an_syn_exist = False
    example_exist = False
    duplicate_meaning = False
    meaning_cnt = 0
    for synset in synsets:
        pos = nltk_pos_dict.get(synset.pos(), 0)
        meaning_id = synset.offset()
        insert_word_ids_command += f"""('{spelling}', {meaning_id}),"""
        insert_meanings_command = f"""insert into `meanings`(`meaning_id`,`pos_id`,`meaning`) values ({meaning_id}, {pos}, "{synset.definition().replace('"', "'")}");"""
        try:
            # 不同的单词可以有重复的意思， 所以需要单独执行
            meaning_cnt += exec_i(insert_meanings_command)
        except IntegrityError:
            output(f"\nword:{spelling} has a duplicate meaning:{synset.name()}")
            duplicate_meaning = True
            continue
        except Exception:
            output(f"\n at:{spelling}\nof command{insert_meanings_command}")
        for lemma in synset.lemmas():
            an_syn_exist = True
            syn = lemma.name()
            if lemma.antonyms():
                ant = lemma.antonyms()[0].name()
                insert_an_synonyms_command += f"""({meaning_id}, "{ant}", false),"""
            insert_an_synonyms_command += f"""({meaning_id}, "{syn}", true),"""
        for example in synset.examples():
            ex = example.replace('"', "'")
            insert_example_sentences_command += f"""({meaning_id}, "{ex}"),"""
            example_exist = True
    if output_mode == 1:
        if duplicate_meaning:
            output(f"\nmeanings:{meaning_cnt}")
        else:
            output(f"\tmeanings:{meaning_cnt}")
    cnt = exec_i(insert_word_ids_command[:-1] + ';')
    if output_mode == 1:
        output(f"\tword_ids:{cnt}")
    if an_syn_exist:
        cnt = exec_i(insert_an_synonyms_command[:-1] + ';')
    else:
        cnt = 0
    if output_mode == 1:
        output(f"\tan_synonyms:{cnt}")
    if example_exist:
        cnt = exec_i(insert_example_sentences_command[:-1] + ';')
    else:
        cnt = 0
    if output_mode == 1:
        output(f"\texample_sentences:{cnt}√")


def insert_translations(origin, rigid_translations, output: Callable[[str], None], output_mode=1):
    command = "insert into `translations` values "
    for pos, trans in rigid_translations.items():
        pos_id = pos_dict.get(pos, 0)
        for tran in trans:
            command += f"('{origin}', '{pos_id}', '{tran}'),"
    cnt = exec_i(command[:-1] + ';')
    if output_mode == 1:
        output(f"\ntranslations：{cnt}")


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
        cnt = exec_i(f"insert into `phrases` values('{phrase}', '{related_word}', '{revise_id}');")
    output(f"\tphrases：{cnt}")
    insert_translations(phrase, rigid_translations, output)
    if note:
        output(f"""\tnotes：{exec_i(f"insert into `notes` values('{revise_id}', '{note}');")}""")
    if len(examples) > 0:
        command = "insert into `example_sentences` values"
        for i, example in enumerate(examples):
            if i > 9:  # 最多10句
                break
            command += f"""("{phrase}", null, "{example.replace('"', "'")}"),"""
        cnt = exec_i(command[:-1] + ';')
        output(f"\texample_sentences改变行数：{cnt}√")
    else:
        output("\n无例句被插入")


def word_renew_plan(word: str, op: int, output: Callable[[str], None], note: str = None, alias: str = None, output_mode=1):
    cnt = 0
    output("\n")
    if op == 1 or op == 3:
        if note:
            cnt += exec_i(f"call `renew_refresh_plan_for_word`('{word}', '{note}');")
        else:
            cnt += exec_i(f"call `renew_refresh_plan_for_word`('{word}', null);")
        if output_mode == 1:
            output("refresh renewed ")
    if op == 2 or op == 3:
        if alias:
            cnt += exec_i(f"call `renew_respell_plan_for_word`('{word}', '{alias}');")
        else:
            cnt += exec_i(f"call `renew_respell_plan_for_word`('{word}', null);")
        if output_mode == 1:
            output("respell renewed ")
    if output_mode == 1:
        output(f"\t{cnt}√")
    else:
        return cnt


def word_join_plan(word: str, op: int, output: Callable[[str], None], phonetic: str,
                   rigid_translations: dict[str, [str]], synsets: [nltk.corpus.reader.wordnet.Synset],
                   note: str = None, alias: str = None, next_revise_date: str = None, mastery: str = None,
                   output_mode=1):
    # 新增复习计划
    if op == 3:
        isrt_rev_cmd = """insert into `revise_items` values (),();"""
    else:
        if next_revise_date and mastery:
            isrt_rev_cmd = f"""insert into `revise_items`(`next_revise_date`, `mastery_level`) values 
            ('{next_revise_date}', '{mastery}');"""
        else:
            isrt_rev_cmd = """insert into `revise_items` values ();"""
    cnt = exec_i(isrt_rev_cmd)
    if output_mode == 1:
        output(f"\nrevise_items:{cnt}")
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
    if output_mode == 1:
        output(f"\twords：{cnt}")
    if alias:
        exec_i(f'update `words` set `alias` = "{alias}" where `spelling` = "{word}";')
    # 插入notes
    if note:
        cnt = exec_i(f"insert into `notes` values (last_insert_id(),'{note}')")
        if output_mode == 1:
            output(f"\tnotes：{cnt}")
    # 插入meanings, an_syn, examples, word_ids
    insert_synsets(word, synsets, output, output_mode)
    # 插入translations
    insert_translations(word, rigid_translations, output, output_mode)
    if output_mode == 1:
        output(f"\n{word} ok√")


def word_process(word: str, op: int, output: Callable[[str], None], note: str = None, alias: str = None):
    # 检测是否已有
    exist_result = fetchone(f"select * from words where spelling = '{word}';")
    # 已有，更新计划，输出消息
    if exist_result:
        word_renew_plan(word, op, output, note, alias)
    # 查询结果，结果入库
    else:
        phonetic, rigid_translations, synsets = ct.consult_word(word, output)
        if synsets:
            word_join_plan(word=word, op=op, output=output, note=note, alias=alias, phonetic=phonetic,
                           rigid_translations=rigid_translations, synsets=synsets)
        else:
            output(f"\n{word}加入计划失败")


def import_from_file(filename, output: Callable[[str], None], date, mastery='1'):
    output("\n开始执行")
    all_content = []
    word_list = []
    thread_list = []
    error_list = []
    error_again_list = []
    # 获取单词列表
    with open(filename, 'r', encoding='utf-8') as f:
        for line in f.readlines():
            if line.startswith("#"):
                continue
            word = line.strip()
            exist_result = fetchone(f"select * from words where spelling = '{word}';")
            # 已有，更新计划，输出消息
            if exist_result:
                output(f"\n{word}已存在")
                continue
            else:
                word_list.append(word)
    import_from_word_list(all_content, error_list, output, thread_list, word_list, date, mastery)
    if len(error_list) == 0:
        output("\n所有单词均加入计划，按commit保存结果到数据库")
        return
    if 0 < len(error_list) < 30:
        output("\n二次查询开始")
        thread_list.clear()
        all_content.clear()
        import_from_word_list(all_content, error_again_list, output, thread_list, error_list, date, mastery)
        if len(error_again_list) == 0:
            output("\n所有单词均加入计划，按commit保存结果到数据库")
            return
        else:
            error_list = error_again_list
    if len(error_list) > 0:
        output("\n以下单词无法加入计划：")
        for word in error_list:
            output(f"\n{word}")
        output("\n按commit保存结果到数据库")


def import_from_word_list(all_content, error_list, output, thread_list, word_list, date, mastery):
    # 启动查询线程
    for word in word_list:
        t = threading.Thread(target=fun, args=(word, all_content, output, error_list))
        t.start()
        thread_list.append(t)
    for t in thread_list:
        t.join()
    for (word, phonetic, rigid_translations, synsets) in all_content:
        word_join_plan(word=word, op=1, output=output, phonetic=phonetic,
                       rigid_translations=rigid_translations, synsets=synsets,
                       next_revise_date=date, mastery=mastery, output_mode=0)
        output(f"\n{word}√")


def fun(word, all_content: list, output: Callable[[str], None], error_list: list):
    try:
        phonetic, rigid_translations, synsets = ct.consult_word(word, output, 0)
        if synsets:
            all_content.append((word, phonetic, rigid_translations, synsets))
        else:
            raise Exception("没查到synsets")
    except Exception as e:
        output(f"\n查询{word}时出现异常：{str(e)}")
        error_list.append(word)
