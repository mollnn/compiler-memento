import json
from os import stat
import networkx as nx
import matplotlib.pyplot as plt
from networkx.algorithms.shortest_paths import weighted
import copy


def isOperator(c):
    if c == '\x03' or c == '\x02' or c == '\x01':
        return True
    return False


def getPrio(c):
    if c == '\x04':
        return 1
    if c == '\x02':
        return 2
    if c == '\x01':
        return 3
    if c == '\x03':
        return 4
    return 0


def toSuffix(expr):
    op = []
    suffix = ""
    for c in expr:
        if isOperator(c):
            # if c == '*':
            #     suffix += c
            #     continue
            while len(op) > 0:
                t = op[-1]
                if getPrio(c) <= getPrio(t):
                    op = op[:-1]
                    suffix += t
                else:
                    break
            op.append(c)
        else:
            if c == '\x04':
                op.append(c)
            elif c == '\x05':
                while op[-1] != '\x04':
                    suffix += op[-1]
                    op = op[:-1]
                op = op[:-1]
            else:
                suffix += c
    while len(op) > 0:
        suffix += op[-1]
        op = op[:-1]
    return suffix


def merge_nfa(nfas):
    n = len(nfas)
    pin = 1

    lens = [0 for i in range(n)]
    for i in range(n):
        lens[i] = len(nfas[i]["e"])
    sumlen = sum(lens)+1

    ans = {
        "s": 0,
        "t": [],
        "e": [[] for i in range(sumlen)],
        "tt": [[] for i in range(sumlen)]
    }

    for i in range(n):
        leni = lens[i]
        mp_idi_id = [pin+i for i in range(leni)]
        nfa_i = nfas[i]
        ans["e"][0].append(["$", mp_idi_id[nfa_i["s"]]])
        for p in range(leni):
            for [w, q] in nfa_i["e"][p]:
                ans["e"][mp_idi_id[p]].append([w, mp_idi_id[q]])
        for tar in nfa_i["t"]:
            ans["tt"][tar+pin].append(i)
            if tar+pin not in ans["t"]:
                ans["t"].append(tar+pin)
        pin += leni

    return ans


def printf(dic):
    dic2 = copy.deepcopy(dic)
    for i in range(len(dic2["e"])):
        dic2["e"][i] = str(dic2["e"][i])
    js = json.dumps(dic2, sort_keys=True, indent=4, separators=(',', ':'))
    print(js)


def nfa_atom(a):
    ans = {"s": 0, "t": 1, "e": [[[a, 1]], []]}
    return ans


def nfa_concat(nfa_1, nfa_2):
    len_1 = len(nfa_1["e"])
    len_2 = len(nfa_2["e"])
    mp_id1_id = [i for i in range(len_1)]
    mp_id2_id = [i+len_1 for i in range(len_2)]
    ans = {
        "s": mp_id1_id[nfa_1["s"]],
        "t": mp_id2_id[nfa_2["t"]],
        "e": [[] for i in range(len_1 + len_2)]
    }
    # 附加边
    ans["e"][mp_id1_id[nfa_1["t"]]].append(["$", mp_id2_id[nfa_2["s"]]])
    # 转换 nfa_1 的边
    for p in range(len_1):
        for [w, q] in nfa_1["e"][p]:
            ans["e"][mp_id1_id[p]].append([w, mp_id1_id[q]])
    # 转换 nfa_2 的边
    for p in range(len_2):
        for [w, q] in nfa_2["e"][p]:
            ans["e"][mp_id2_id[p]].append([w, mp_id2_id[q]])
    return ans


def nfa_union(nfa_1, nfa_2):
    len_1 = len(nfa_1["e"])
    len_2 = len(nfa_2["e"])
    mp_id1_id = [2+i for i in range(len_1)]
    mp_id2_id = [2+i+len_1 for i in range(len_2)]
    ans = {
        "s": 0,
        "t": 1,
        "e": [[] for i in range(2 + len_1 + len_2)]
    }
    # 附加边
    ans["e"][0].append(["$", mp_id1_id[nfa_1["s"]]])
    ans["e"][0].append(["$", mp_id2_id[nfa_2["s"]]])
    ans["e"][mp_id1_id[nfa_1["t"]]].append(["$", 1])
    ans["e"][mp_id2_id[nfa_2["t"]]].append(["$", 1])
    # 转换 nfa_1 的边
    for p in range(len_1):
        for [w, q] in nfa_1["e"][p]:
            ans["e"][mp_id1_id[p]].append([w, mp_id1_id[q]])
    # 转换 nfa_2 的边
    for p in range(len_2):
        for [w, q] in nfa_2["e"][p]:
            ans["e"][mp_id2_id[p]].append([w, mp_id2_id[q]])
    return ans


def nfa_star(nfa_1):
    len_1 = len(nfa_1["e"])
    mp_id1_id = [2+i for i in range(len_1)]
    ans = {
        "s": 0,
        "t": 1,
        "e": [[] for i in range(2 + len_1)]
    }
    # 附加边
    ans["e"][0].append(["$", mp_id1_id[nfa_1["s"]]])
    ans["e"][mp_id1_id[nfa_1["t"]]].append(["$", 1])
    ans["e"][mp_id1_id[nfa_1["t"]]].append(["$", mp_id1_id[nfa_1["s"]]])
    ans["e"][0].append(["$", 1])
    # 转换 nfa_1 的边
    for p in range(len_1):
        for [w, q] in nfa_1["e"][p]:
            ans["e"][mp_id1_id[p]].append([w, mp_id1_id[q]])
    return ans


def re2nfa(sre):
    stack = []

    for x in sre:
        if x not in "\x01\x02\x03":
            stack.append(nfa_atom(x))
        elif x == "\x01":
            p = stack[-2]
            q = stack[-1]
            stack = stack[:-2]
            stack.append(nfa_concat(p, q))
        elif x == "\x02":
            p = stack[-2]
            q = stack[-1]
            stack = stack[:-2]
            stack.append(nfa_union(p, q))
        elif x == "\x03":
            p = stack[-1]
            stack = stack[:-1]
            stack.append(nfa_star(p))

    ans = stack[0]
    ans["t"] = [ans["t"]]

    return ans


def printf0(dic):
    js = json.dumps(dic, sort_keys=True, indent=4, separators=(',', ':'))
    print(js)


epsc_buffer = {}


def eps_closure(nfa, states):
    global epsc_buffer
    if str(set(states)) in epsc_buffer:
        return epsc_buffer[str(set(states))]
    s = states.copy()
    s = list(set(s))
    while True:
        s1 = s[:]
        for p in s:
            for [w, q] in nfa["e"][p]:
                if w == '$' and q not in s:
                    s.append(q)
        s.sort()
        if s == s1:
            break
    epsc_buffer[str(set(states))] = s
    return s


def move(nfa, states, a):
    s = []
    for p in states:
        for [w, q] in nfa["e"][p]:
            if w == a and q not in s:
                s.append(q)
    s = list(set(s))
    return s


def nfa2dfa(nfa):
    d = [eps_closure(nfa, [0])]
    e = []
    chars = []
    for i in nfa["e"]:
        for [w, q] in i:
            if w not in chars:
                chars.append(w)
    chars = list(set(chars))
    # print(chars)
    i = 0
    while i < len(d):
        states = d[i]
        e.append([])
        for a in chars:
            if a == "$":
                continue
            u = move(nfa, states, a)
            u = eps_closure(nfa, u)
            if len(u) == 0:
                continue
            if u not in d and len(u) > 0:
                d.append(u)
            e[i].append([a, d.index(u)])
        i += 1
    # print(d)
    ts = []
    tt = []
    for i in range(len(d)):
        flag = 0
        srcs = []
        for j in nfa["t"]:
            if j in d[i]:
                flag = 1
                srcs.append(j)
        pats = []
        for j in srcs:
            pats += nfa["tt"][j]
        pats = list(set(pats))
        if flag:
            ts.append(i)
        pats = min(pats) if len(pats)>0 else -1
        tt.append(pats)
    return {'s': 0, 't': ts, 'e': e, 'tt': tt}


def getdiv(dfa):
    n = len(dfa["e"])
    # set_1 = dfa["t"]
    # set_0 = [i for i in range(n) if i not in set_1]
    # P = [set_0, set_1]

    P = []

    patset = list(set(dfa["tt"]))
    pdic = {}
    for i in patset:
        pdic[i] = []
    for i in range(len(dfa["tt"])):
        pdic[dfa["tt"][i]].append(i)
    for i, j in pdic.items():
        P.append(j)

    chars = []
    for i in dfa["e"]:
        for [w, q] in i:
            if w not in chars:
                chars.append(w)
    chars = list(set(chars))

    while True:
        P0 = P[:]
        B = [0 for i in range(n)]
        for i in range(len(P)):
            p = P[i]
            for q in p:
                B[q] = i
        flag = 0
        for p in P:
            for c in chars:
                def trans(dfa, p, a):
                    for [w, q] in dfa["e"][p]:
                        if w == a:
                            return q
                    return -1
                tos = [B[trans(dfa, i, c)] if trans(
                    dfa, i, c) >= 0 else -1 for i in p]
                stos = list(set(tos))
                if len(stos) <= 1:
                    continue
                Pa = []
                for itos in stos:
                    s = [p[i] for i in range(len(p)) if tos[i] == itos]
                    Pa.append(s)
                P.remove(p)
                P += Pa
                flag = 1
                break
            if flag == 1:
                break
        if flag == 0:
            break
    # 为符合习惯，交换，让 0 号状态为开始状态
    id0 = -1
    for i in range(len(P)):
        if 0 in P[i]:
            id0 = i
            break

    P[0], P[id0] = P[id0], P[0]
    return P


def dfamin(dfa):
    n = len(dfa["e"])
    div = getdiv(dfa)
    for i in range(len(div)):
        div[i] = list(set(div[i]))
    mp = [0 for i in range(n)]  # 属于哪一个集合
    for i in range(len(div)):
        p = div[i]
        for q in div[i]:
            mp[q] = i
    ans = {'s': 0, 't': [], 'e': [[] for i in range(len(div))], 'tt': []}
    # 决定哪些状态是接受状态
    for i in range(len(div)):
        flag = 1
        bel = 99999
        for j in div[i]:
            if j not in dfa["t"]:
                flag = 0
            else:
                bel = min(bel, dfa["tt"][j])
        if flag:
            ans["t"].append(i)
            ans["tt"].append(bel)
        else:
            ans["tt"].append(-1)
    # 转换所有边
    e = []
    for i in range(n):
        for [w, q] in dfa["e"][i]:
            pp = mp[i]
            qq = mp[q]
            e.append((pp, w, qq))
    # print(e)
    e = list(set(e))
    for [p, w, q] in e:
        ans['e'][p].append([w, q])
    return ans


def draw_fa(nfa):
    G = nx.DiGraph()
    G.clear()
    len_nfa = len(nfa["e"])
    G.add_nodes_from([i for i in range(len_nfa)])  # 添加多个节点
    for i in range(len_nfa):
        if len(nfa["e"][i]) == 0:
            continue
        for [w, q] in nfa["e"][i]:
            G.add_edge(i, q, weight=1 if w == '$' else 2 if w ==
                       'a' else 3 if w == 'b' else 4)  # 添加一条
            if i == q:
                print("自环", i, w)

    # nx.draw(G, node_size=500, with_labels=True, node_color='red')
    elarge1 = [(u, v) for (u, v, d) in G.edges(data=True) if d['weight'] == 2]
    elarge2 = [(u, v) for (u, v, d) in G.edges(data=True) if d['weight'] == 3]
    elarge3 = [(u, v) for (u, v, d) in G.edges(data=True) if d['weight'] == 4]
    esmall = [(u, v) for (u, v, d) in G.edges(data=True) if d['weight'] == 1]
    n0 = [x for x, y in G.nodes(data=True) if x !=
          nfa["s"] and x not in nfa["t"]]
    n1 = [x for x, y in G.nodes(data=True) if x == nfa["s"]]
    n2 = [x for x, y in G.nodes(data=True) if x in nfa["t"]]

    pos = nx.spring_layout(G)  # positions for all nodes

    nx.draw_networkx_nodes(G, pos, nodelist=n0,
                           node_size=500, node_color='gray')
    nx.draw_networkx_nodes(G, pos, nodelist=n1,
                           node_size=500, node_color='pink')
    nx.draw_networkx_nodes(G, pos, nodelist=n2,
                           node_size=500, node_color='brown')

    nx.draw_networkx_edges(G, pos, edgelist=elarge1, width=3, edge_color='red')
    nx.draw_networkx_edges(G, pos, edgelist=elarge2,
                           width=3, edge_color='green')
    nx.draw_networkx_edges(G, pos, edgelist=elarge3,
                           width=3, edge_color='blue')
    nx.draw_networkx_edges(G, pos, edgelist=esmall, width=2,
                           alpha=1, edge_color='gray', style='dotted')
    nx.draw_networkx_labels(G, pos, font_size=14,
                            font_family='sans-serif', font_color='w')
    plt.axis('off')
    plt.show()


def run(dfa, str):
    p = dfa["s"]
    for c in str:
        x = -1
        for [w, q] in dfa["e"][p]:
            if w == c:
                x = q
        if x == -1:
            return -1
        else:
            p = x
    return dfa["tt"][p]


def runx(dfa, src):
    ptr = 0
    results = []
    while ptr < len(src):
        p = dfa["s"]

        MAXPREREAD = 256  # 最多预读 MAXPREREAD 个字符
        str = src[ptr:ptr+MAXPREREAD]
        last_match_pos = -1
        last_match_ans = -1
        for step, c in enumerate(str):
            x = -1
            for [w, q] in dfa["e"][p]:
                if w == c:
                    x = q
            if x == -1:
                break
            else:
                p = x
            if dfa["tt"][p] != -1:
                last_match_pos = step+1
                last_match_ans = dfa["tt"][p]
        if last_match_pos == -1:
            # 错误，跳过该行
            print("\033[31merror near:", src[ptr:ptr+32], "\033[0m")
            while ptr < len(src) and src[ptr] != '\n':
                ptr += 1
            ptr += 1
        else:
            # print("\033[32mmatch re#%d" % last_match_ans, str[:last_match_pos],"\033[0m")
            result_re_id = last_match_ans
            result_str = str[:last_match_pos]
            if result_str not in " \n\r\t":
                results.append((result_re_id, result_str))
            ptr += last_match_pos
    return results


def re_preprocess(re):
    re = copy.deepcopy(re)
    re = re.replace("[A~Za~z]", "([A~Z]|[a~z])")
    re = re.replace("[A~Za~z0~9]", "([A~Z]|[a~z]|[0~9])")
    re = re.replace("[0~9]", "(0|1|2|3|4|5|6|7|8|9)")
    re = re.replace("[1~9]", "(1|2|3|4|5|6|7|8|9)")
    re = re.replace(
        "[A~Z]", "(A|B|C|D|E|F|G|H|I|J|K|L|M|N|O|P|Q|R|S|T|U|V|W|X|Y|Z)")
    re = re.replace(
        "[a~z]", "(a|b|c|d|e|f|g|h|i|j|k|l|m|n|o|p|q|r|s|t|u|v|w|x|y|z)")

    re = re.replace("\\n", "\n")
    re = re.replace("\\r", "\r")
    re = re.replace("\\t", "\t")

    re = re.replace("\\&", "\x06")
    re = re.replace("&", "\x01")
    re = re.replace("\x06", "&")

    re = re.replace("\\|", "\x06")
    re = re.replace("|", "\x02")
    re = re.replace("\x06", "|")

    re = re.replace("\\*", "\x06")
    re = re.replace("*", "\x03")
    re = re.replace("\x06", "*")

    re = re.replace("\\(", "\x06")
    re = re.replace("(", "\x04")
    re = re.replace("\x06", "(")

    re = re.replace("\\)", "\x06")
    re = re.replace(")", "\x05")
    re = re.replace("\x06", ")")

    i = 0
    while i+1 < len(re):
        a = 'a' if re[i] not in "\x02\x01\x03\x04\x05" else re[i]
        b = 'a' if re[i+1] not in "\x02\x01\x03\x04\x05" else re[i+1]
        c = [
            'a\x04', 'aa', '\x05a', '\x03a', '\x03\x04', '\x05\x04'
        ]
        if a+b in c:
            re = re[:i+1]+'\x01'+re[i+1:]
        i += 1
    return re


re_file = open("re.txt", "r")
re_list = re_file.readlines()
re_list = [i[:-1] for i in re_list]

sres = copy.deepcopy(re_list)
re_list = [re_preprocess(i) for i in re_list]
nfas = [re2nfa(toSuffix(i)) for i in re_list]
nfa = merge_nfa(nfas)
dfa = nfa2dfa(nfa)
dfa = dfamin(dfa)

# printf(dfa)
# print(ans)

src_file = open("src.txt", "r")
src = src_file.read()

results = runx(dfa, src)

# map.txt 对每个 re 给定一个名称，用于语法分析
map_file = open("map.txt", "r")
token_map = map_file.readlines()
token_map = [i[:-1] for i in token_map]

tokens_file = open("tokens.txt", "w")
for x, y in results:
    print(x,  token_map[x], y, file=tokens_file)

# s = ["a", "b", "ab", "aa", "abc", "1", "0", "123", "1.23", "a11"]
# ans = [run(dfa, i) for i in s]
# for i, a in enumerate(ans):
#     print(i, s[i], a, -1 if a == -1 else sres[a])

# draw_fa(dfa)
