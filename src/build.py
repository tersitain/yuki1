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

G3 = ('悪安暗医委意育員院飲運泳駅央横屋温化荷界開階寒感漢館岸起期客究急級宮球去橋業曲局銀区苦具君係軽血決研県庫湖向幸港号根祭皿'
      '仕死使始指歯詩次事持式実写者主守取酒受州拾終習集住重宿所暑助昭消商章勝乗植申身神真深進世整昔全相送想息速族他打対待代第題'
      '炭短談着注柱丁帳調追定庭笛鉄転都度投豆島湯登等動童農波配倍箱畑発反坂板皮悲美鼻筆氷表秒病品負部服福物平返勉放味命面問役薬'
      '由油有遊予羊洋葉陽様落流旅両緑礼列練路和')
assert len(G3) == 200 and len(set(G3)) == 200 and not set(G3) & set(G1 + G2), len(G3)

# グループ: k=2年生の漢字(1字1語) / j=2年生の字の熟語 / c=3年生の漢字
OWN = {'k': G2, 'j': G2, 'c': G3}                 # 1列目に書ける字
OK = {'k': G1 + G2, 'j': G1 + G2, 'c': G1 + G2 + G3}   # 語に使える字
is_kanji = lambda c: '一' <= c <= '鿿'
is_hira = lambda c: 'ぁ' <= c <= 'ゖ' or c == 'ー'
errs = []
units = []
seen = {'k': [], 'j': [], 'c': []}
words = {'k': [], 'j': [], 'c': []}
g = 'k'
for ln in (SRC / 'kanji.txt').read_text(encoding='utf-8').splitlines():
    if not ln.strip():
        continue
    if ln.startswith('@'):
        g = ln[1:].strip(); continue
    if ln.startswith('#'):
        t, e = ln[1:].strip().split('|')
        units.append({'g': g, 't': t, 'e': e, 'k': []})
        continue
    k, s = ln.split('\t')
    m = re.fullmatch(r'([^{}]*)\{([^|{}]+)\|([^|{}]+)\}([^{}]*)', s)
    if not m:
        errs.append(f'形式: {ln}'); continue
    pre, word, read, post = m.groups()
    if k not in OWN[g]: errs.append(f'{g}: この学年の字ではない: {k}')
    if g != 'j' and k in seen[g]: errs.append(f'{g}: 重複: {k}')
    seen[g].append(k)
    if word in words[g] or (g == 'j' and word in words['k']): errs.append(f'{g}: 語の重複: {word}')
    words[g].append(word)
    if k not in word: errs.append(f'語に字がない: {k} {word}')
    for c in word:
        if is_kanji(c) and c not in OK[g]: errs.append(f'{g}: 未習の字: {word} の {c}')
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

for gg in ('k', 'c'):
    missing = set(OWN[gg]) - set(seen[gg])
    if missing: errs.append(f'{gg}: 不足: ' + ''.join(sorted(missing)))
if errs:
    print('\n'.join(errs)); sys.exit(1)

for gg in 'kjc':
    us = [u for u in units if u['g'] == gg]; n = sum(len(u['k']) for u in us)
    print(gg, '単元', len(us), '語', n, '問題', n * 2, '|', ' '.join(f"{u['t']}{len(u['k'])}" for u in us))
print('じゅくごで出ていない2年生の字:', ''.join(c for c in G2 if c not in ''.join(words['j'])))

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
