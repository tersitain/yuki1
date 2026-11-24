"""漢字データを検証し、テンプレートに埋めこんで app/ に出力する。"""
import json, re, hashlib, sys, pathlib

SRC = pathlib.Path(__file__).parent
APP = SRC.parent / 'app'
if not APP.exists():
    APP = SRC.parent   # リポジトリでは、公開ファイルを直下に置く

G1 = '一右雨円王音下火花貝学気九休玉金空月犬見五口校左三山子四糸字耳七車手十出女小上森人水正生青夕石赤千川先早草足村大男竹中虫町天田土二日入年白八百文木本名目立力林六'
G2 = ('引羽雲園遠何科夏家歌画回会海絵外角楽活間丸岩顔汽記帰弓牛魚京強教近兄形計元言原戸古午後語工公広交光考'
      '行高黄合谷国黒今才細作算止市矢姉思紙寺自時室社弱首秋週春書少場色食心新親図数西声星晴切雪船線前組走多'
      '太体台地池知茶昼長鳥朝直通弟店点電刀冬当東答頭同道読内南肉馬売買麦半番父風分聞米歩母方北毎妹万明鳴毛'
      '門夜野友用曜来里理話')
assert len(G1) == 80 and len(set(G1)) == 80, len(G1)
assert len(G2) == 160 and len(set(G2)) == 160, len(G2)

is_kanji = lambda c: '一' <= c <= '鿿'
is_hira = lambda c: 'ぁ' <= c <= 'ゖ' or c == 'ー'
errs = []
units = []
seen = []
for ln in (SRC / 'kanji.txt').read_text(encoding='utf-8').splitlines():
    if not ln.strip():
        continue
    if ln.startswith('#'):
        t, e = ln[1:].strip().split('|')
        units.append({'t': t, 'e': e, 'k': []})
        continue
    k, s = ln.split('\t')
    m = re.fullmatch(r'([^{}]*)\{([^|{}]+)\|([^|{}]+)\}([^{}]*)', s)
    if not m:
        errs.append(f'形式: {ln}'); continue
    pre, word, read, post = m.groups()
    if k not in G2: errs.append(f'2年の字ではない: {k}')
    if k in seen: errs.append(f'重複: {k}')
    seen.append(k)
    if k not in word: errs.append(f'語に字がない: {k} {word}')
    for c in word:
        if is_kanji(c) and c not in G1 + G2: errs.append(f'未習の字: {word} の {c}')
    for c in pre + post:
        if is_kanji(c): errs.append(f'文に漢字: {s}')
    if not all(is_hira(c) for c in read): errs.append(f'よみがひらがなでない: {read}')
    # 送りがなを切り分ける（語とよみの共通の末尾）
    n = 0
    while n < min(len(word), len(read)) - 1 and word[-1 - n] == read[-1 - n] and not is_kanji(word[-1 - n]):
        n += 1
    stem, sread, oku = word[:len(word) - n], read[:len(read) - n], word[len(word) - n:]
    if not stem or not all(is_kanji(c) for c in stem): errs.append(f'語幹が漢字だけでない: {word} -> {stem}')
    if not sread: errs.append(f'よみの切り分け: {word} {read}')
    units[-1]['k'].append([k, pre, stem, sread, oku, post])

missing = set(G2) - set(seen)
if missing: errs.append('不足: ' + ''.join(sorted(missing)))
if errs:
    print('\n'.join(errs)); sys.exit(1)

total = sum(len(u['k']) for u in units)
print('単元', len(units), '漢字', total, '問題', total * 2)
for u in units:
    print(' ', u['t'], len(u['k']), ''.join(x[0] for x in u['k']))
# 参考：語幹のよみが重なる組（かき問題の選択肢から自動で外す）
from collections import defaultdict
d = defaultdict(list)
for u in units:
    for x in u['k']: d[x[3]].append(x[2])
print('同じよみ:', {k: v for k, v in d.items() if len(v) > 1})
d = defaultdict(list)
for u in units:
    for x in u['k']: d[x[4]].append(x[2] + x[4])
print('送りがな別:', {k: len(v) for k, v in d.items()})

tpl = (SRC / 'template.html')
if tpl.exists():
    APP.mkdir(exist_ok=True)
    html = tpl.read_text(encoding='utf-8').replace('/*KANJI*/[]', json.dumps(units, ensure_ascii=False, separators=(',', ':')))
    assert '/*KANJI*/' not in html
    (APP / 'index.html').write_text(html, encoding='utf-8')
    h = hashlib.sha1(html.encode()).hexdigest()[:8]
    sw = (SRC / 'sw.js').read_text(encoding='utf-8').replace('__HASH__', h)
    (APP / 'sw.js').write_text(sw, encoding='utf-8')
    print('index.html', len(html.encode()), 'bytes  cache', h)
