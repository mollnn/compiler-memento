# 项：(prod_id, dot_pos, ahead)
import copy


def closure(prods, ps, first):
    ps = ps[:]
    for (prod_id, dot_pos, ahead) in ps:
        prod = prods[prod_id]
        if dot_pos + 1 < len(prod):
            cur = prod[dot_pos+1]
            # next_symbol = prod[dot_pos+2] if dot_pos+2 < len(prod) else ahead
            nss = []
            tmpseq = prod[dot_pos+2:] + [ahead]
            i = 0
            first['$'] = ['$']
            while i < len(tmpseq):
                for x in first[tmpseq[i]]:
                    if (x != '$' or tmpseq[i] == '$') and x not in nss:
                        nss.append(x)
                if '$' not in first[tmpseq[i]]:
                    break
                i += 1
            for next_symbol in nss:
                for ex_prod_id, ex_prod in enumerate(prods):
                    if ex_prod[0] == cur:
                        new_item = (ex_prod_id, 0, next_symbol)
                        if new_item not in ps:
                            ps.append(new_item)
    return ps


def goto(prods, ps, a, first):
    ans = []
    for (i, j, ah) in ps:
        prod = prods[i]
        if j + 1 < len(prod):
            cur = prod[j + 1]
            if cur == a:
                new_item = (i, j+1, ah)
                if new_item not in ans:
                    ans.append(new_item)
    return closure(prods, ans, first)


def prod2str(prod, dotpos):
    prod = prod[:]
    prod.append("")
    prod[dotpos + 1] = '·' + prod[dotpos + 1]
    return prod[0] + '→' + ''.join(prod[1:])


def make_lr1(prods):

    table = [{}]
    words = list(set(j for i in prods for j in i))
    nonterminals = list(set(i[0] for i in prods))
    terminals = [i for i in words if i not in nonterminals]
    terminals .append('$')
    nonterminals.sort()
    terminals.sort()

    # 预处理 first 集合
    first = {}
    for i in terminals:
        first[i] = [i]
    for i in nonterminals:
        first[i] = []

    while True:
        old_first = copy.deepcopy(first)
        for prod in prods:
            left = prod[0]
            right = prod[1:]
            i = 0
            while i < len(right):
                for x in first[right[i]]:
                    if x != "$" and x not in first[left]:
                        first[left].append(x)
                if "$" not in first[right[i]]:
                    break
                i += 1
            if i == len(right):
                if "$" not in first[left]:
                    first[left].append("$")
        if old_first == first:
            break

    I0 = closure(prods, [(0, 0, '$')], first)
    cc = [I0]
    i = 0

    while i < len(cc):
        ccc = {}
        for j in cc[i]:
            if (j[0], j[1]) not in ccc.keys():
                ccc[(j[0], j[1])] = j[2]
            else:
                ccc[(j[0], j[1])] = j[2]
        ccc = [[i[0], i[1], j] for i, j in ccc.items()]
        print("\033[35m[I%d]:\n  \033[31m" % i, '\n   \033[31m'.join(prod2str(prods[j[0]], j[1])+' \t\033[33m'+j[2]+'\033[30m'
              for j in ccc), end="\n   \033[32m")
        candiwords = []
        for j in cc[i]:
            prod = prods[j[0]]
            dot_pos = j[1]+1
            if dot_pos < len(prod) and prod[dot_pos] not in candiwords:
                candiwords.append(prod[dot_pos])
            if dot_pos == len(prod):
                if prod[0] != "S'":
                    if j[2] not in table[i].keys():
                        table[i][j[2]] = 'r%d' % j[0]
                    else:
                        table[i][j[2]] = 'r%d' % j[0]
                else:
                    if '$' not in table[i].keys():
                        table[i]['$'] = 'acc'
                    else:
                        table[i]['$'] += 'acc'
        for j in candiwords:
            tmp = goto(prods, cc[i], j, first)
            if len(tmp) > 0 and tmp not in cc:
                cc.append(tmp)
                table.append({})
            if len(tmp) > 0:
                print(j, cc.index(tmp), sep=",", end="  ")
                if j in terminals:
                    if j not in table[i].keys():
                        table[i][j] = "s%d" % cc.index(tmp)
                    else:
                        table[i][j] = "s%d" % cc.index(tmp)
                else:
                    table[i][j] = "%d" % cc.index(tmp)
        i += 1
        print("\033[0m")
    head = ['I']
    for j in terminals:
        head.append(j)
    for j in nonterminals:
        if j == "S'":
            continue
        head.append(j)
    print('---'.join(''+'-'*(5) for i in head))
    print(' | '.join(i+' '*(5-len(i)) for i in head))
    print('-+-'.join(''+'-'*(5) for i in head))
    for i, line in enumerate(table):
        lo = [str(i)]
        for j in terminals:
            if j in line.keys():
                lo.append(table[i][j])
            else:
                lo.append("")
        for j in nonterminals:
            if j == "S'":
                continue
            if j in line.keys():
                lo.append(table[i][j])
            else:
                lo.append("")
        print(' | '.join(i+' '*(5-len(i)) for i in lo))
    return table


prod_file = open("prod.txt", "r")
prod_lines = prod_file.readlines()
prod_lines = [i[:-1] for i in prod_lines]
prod_lines = [i[:-1] if i[-1] == ' ' else i for i in prod_lines]

prods = [i.split(" ")[:1] + i.split(" ")[2:] for i in prod_lines]
print(prods)
table = make_lr1(prods)

tokens = []
token_file = open("tokens.txt", "r")
token_lines = token_file.readlines()
token_lines = [i[:-1] for i in token_lines]
token_lines = [i[:-1] if i[-1] == ' ' else i for i in token_lines]
token_lines = [i.split(' ') for i in token_lines]
tokens = [i[1] for i in token_lines]
tokens_str = [i[2] for i in token_lines]
tokens.append("$")
tokens_str.append("")


stack_token = ['#']
stack_state = [0]

input_ptr = 0

while len(stack_token) > 0:
    cur_token = tokens[input_ptr]
    cur_state = stack_state[-1]
    if cur_token not in table[cur_state].keys():
        print("errorA")
        break
    action = table[cur_state][cur_token]
    if action == "acc":
        print("succeed")
        break
    elif action[0] == 's':
        next_state = int(action[1:])
        stack_token.append(cur_token)
        stack_state.append(next_state)
        input_ptr += 1
        print("shift", cur_token)
    else:
        prod_id = int(action[1:])
        prod_len = len(prods[prod_id]) - 1
        print("reduce", prods[prod_id])
        stack_token = stack_token[:-prod_len]
        stack_state = stack_state[:-prod_len]
        cur_state = stack_state[-1]
        goto_nt = prods[prod_id][0]
        if goto_nt not in table[cur_state].keys():
            print("errorB")
            break
        next_state = int(table[cur_state][goto_nt])
        stack_token.append(goto_nt)
        stack_state.append(next_state)
