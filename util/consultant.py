from pyquery import PyQuery as pq
import requests
from requests.exceptions import SSLError
from typing import Callable
from nltk.corpus import wordnet as wn

options_name = ["pass", "review", "respell", "both"]
url_bing = 'https://cn.bing.com/dict/search?q='
skip_words = ["现在分词", "过去分词", "同“", "的变体"]
pos_dict = {'O': 0, 'n': 1, 'v': 2, 'adj': 3, 'adv': 4, 'prep': 5, 'phr': 6, 'syn': 7, 'intj': 8, 'conj': 9}


def primary_test(vocab, output: Callable[[str], None]):
    url = url_bing + vocab + '&intlFt=1'
    try:
        response = requests.get(url)
        doc = pq(response.text)
        translation = doc('.qdef ul li').text().replace(' 网络', ' O. ')  # 获取翻译
        return translation
    except SSLError:
        output("\n查询失败:网络异常")
        return None
    except Exception:
        return None


def rigid_bing_consult(vocab: str) -> (str, dict[str, [str]], [str]):
    url = url_bing + vocab.replace(' ', '_') + '&intlFt=1'
    response = requests.get(url)
    doc = pq(response.text)
    # 获取音标
    if ' ' not in vocab:
        phonetic = doc('.hd_p1_1').text().replace('\n', '')
    else:
        phonetic = None
    # 获取中文释义
    rigid_translations = dict()
    for li in doc('.qdef ul').children('li').items():
        text = li.text().replace('网络', 'O.')
        pos_and_meaning = text.split('.', 1)
        if len(pos_and_meaning) != 2:
            pos_and_meaning.append(pos_and_meaning[0])
            pos_and_meaning[0] = 'O'
        pos = pos_and_meaning[0]
        meanings = pos_and_meaning[1].split('；')
        for meaning in meanings:
            if any(skip_word in meaning for skip_word in skip_words):
                continue
            if pos in rigid_translations:
                rigid_translations[pos].append(meaning)
            else:
                rigid_translations[pos] = [meaning]
    # 获取例句
    if ' ' in vocab:
        examples = [pq(example).text() for example in doc('.se_li .sen_en')]
    else:
        examples = None
    return phonetic, rigid_translations, examples


def consult_word(word, output: Callable[[str], None], output_mode=1):
    if output_mode == 1:
        output(f"\n查询{word}")
    phonetic, rigid_translations, _ = rigid_bing_consult(word)
    translation_count = 0
    for trans in rigid_translations.values():
        translation_count += len(trans)
    synsets = wn.synsets(word)
    if len(synsets) > 0 and translation_count > 0:
        if output_mode == 1:
            output(f"\n中:{translation_count}条")
            output(f"\t英:{len(synsets)}条")
        else:
            output(f"\n查询{word}√")
        return phonetic, rigid_translations, synsets
    else:
        output(f"\n查询{word}×")
        return None, None, None
