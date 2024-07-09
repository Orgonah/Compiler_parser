from graphviz import Digraph

def print_grammar(grammar):
    for non_terminal, productions in grammar.items():
        print(f"{non_terminal} -> ", end="")
        production_str = " | ".join(["".join(prod) for prod in productions])
        print(production_str)

def eliminate_left_recursion(grammar):
    new_grammar = {}
    for non_terminal in grammar:
        productions = grammar[non_terminal][0]
        left_recursive = []
        non_left_recursive = []
        for production in productions:
            if production.startswith(non_terminal):
                left_recursive.append(production[len(non_terminal):])
            else:
                non_left_recursive.append(production)
        
        if left_recursive:
            new_non_terminal = non_terminal + "`"
            while new_non_terminal in grammar or new_non_terminal in new_grammar:
                new_non_terminal += "`"
            new_grammar[non_terminal] = [[prod + new_non_terminal for prod in non_left_recursive]]
            new_grammar[new_non_terminal] = [[prod + new_non_terminal for prod in left_recursive] + ['ε']]
        else:
            new_grammar[non_terminal] = [non_left_recursive]

    return new_grammar

def left_factoring(grammar):
    new_grammar = {}
    for non_terminal in grammar:
        productions = grammar[non_terminal][0]
        factored = {}
        for production in productions:
            prefix = production[0] if production else ''
            if prefix not in factored:
                factored[prefix] = []
            factored[prefix].append(production)
        
        if len(factored) == 1:
            new_grammar[non_terminal] = [productions]
        else:
            new_non_terminal = non_terminal + "`"
            while new_non_terminal in grammar or new_non_terminal in new_grammar:
                new_non_terminal += "`"
            new_grammar[non_terminal] = []
            for prefix in factored:
                if len(factored[prefix]) == 1:
                    new_grammar[non_terminal].append(factored[prefix][0])
                else:
                    new_grammar[non_terminal].append(prefix + new_non_terminal)
                    new_grammar[new_non_terminal] = [prod[1:] if len(prod) > 1 else 'ε' for prod in factored[prefix]]

    for key, value in new_grammar.items():
        if isinstance(value[0], list):
            new_grammar[key] = value[0]
        else:
            new_grammar[key] = value

    return new_grammar

def transform_grammar(input_grammar):
    grammar_no_left_recursion = eliminate_left_recursion(input_grammar)
    grammar_no_left_recursion_factored = left_factoring(grammar_no_left_recursion)
    return grammar_no_left_recursion_factored

# Example usage
input_grammar = {
    'E': [['E+T', 'T']],
    'T': [['T*F', 'F']],
    'F': [['(E)', 'id']]
}

grammar = transform_grammar(input_grammar)
print("\nThe Grammar: (you could change the input_grammar variable in the code)\n")
# print(output_grammar)
print_grammar(grammar)
print("\n")

# Create table
def compute_first_sets(grammar):
    first = {non_terminal: set() for non_terminal in grammar}
    
    def first_of(symbol):
        if symbol not in grammar:
            return {symbol}
        if not first[symbol]:
            for production in grammar[symbol]:
                for char in production:
                    first[symbol] |= first_of(char)
                    if 'ε' not in first_of(char):
                        break
                    first[symbol].discard('ε')
                else:
                    first[symbol].add('ε')
        return first[symbol]
    
    for non_terminal in grammar:
        first_of(non_terminal)
    
    return first

def compute_follow_sets(grammar, first):
    follow = {non_terminal: set() for non_terminal in grammar}
    start_symbol = next(iter(grammar))
    follow[start_symbol].add('$')
    
    def follow_of(non_terminal):
        for nt, productions in grammar.items():
            for production in productions:
                 for i in range(len(production)):
                    symbol = production[i]
                    if i+1 < len(production) and production[i+1] == '`':
                        symbol += '`'
                    if symbol == non_terminal:
                        follow_idx = i + len(non_terminal)
                        while follow_idx < len(production):
                            next_symbol = production[follow_idx]
                            if follow_idx+1 < len(production) and production[follow_idx+1] == '`':
                                next_symbol += '`'
                            if next_symbol in first:
                                follow[non_terminal] |= first[next_symbol] - {'ε'}
                            else:
                                follow[non_terminal].add(next_symbol)
                            if next_symbol not in first or 'ε' not in first[next_symbol]:
                                break
                            follow_idx += len(next_symbol)
                        if follow_idx == len(production):
                            follow[non_terminal] |= follow[nt]
    
    for _ in grammar:
        for non_terminal in grammar:
            follow_of(non_terminal)
    
    return follow

def create_ll1_table(grammar, first, follow):
    non_terminals = list(grammar.keys())
    terminals = set()
    for productions in grammar.values():
        for production in productions:
            for char in production:
                if char not in grammar and char != 'ε':
                    terminals.add(char)
    terminals = list(terminals) + ['$']
    
    table = {nt: {t: None for t in terminals} for nt in non_terminals}
    
    for nt, productions in grammar.items():
        for production in productions:
            first_set = set()
            for char in production:
                if char in first:
                    first_set |= first[char]
                else:
                    first_set.add(char)
                    break
                if 'ε' not in first[char]:
                    break
                first_set.discard('ε')
            if 'ε' in first_set:
                first_set |= follow[nt]
            for terminal in first_set:
                table[nt][terminal] = production
            if 'ε' in first_set:
                for terminal in follow[nt]:
                    table[nt][terminal] = production
    
    for nt in table:
        if 'd' in table[nt]:
            del table[nt]['d']
        if '`' in table[nt]:
            del table[nt]['`']
        if 'i' in table[nt]:
            table[nt]['id'] = table[nt].pop('i')
    
    return table

def print_ll1_table(table):
    non_terminals = list(table.keys())
    terminals = sorted(list(next(iter(table.values())).keys()))
    
    header = [""] + terminals
    rows = []
    for nt in non_terminals:
        row = [nt]
        for t in terminals:
            prod = table[nt][t]
            row.append("".join(prod) if prod else "")
        rows.append(row)
    
    col_widths = [max(len(row[i]) for row in [header] + rows) for i in range(len(header))]
    
    def print_row(row):
        print(" | ".join(f"{cell:{col_widths[i]}}" for i, cell in enumerate(row)))
    
    print_row(header)
    print("-" * (sum(col_widths) + 3 * len(col_widths) - 1))
    for row in rows:
        print_row(row)

first = compute_first_sets(grammar)
follow = compute_follow_sets(grammar, first)
table = create_ll1_table(grammar, first, follow)
print("LL1 table for the grammar:")
print_ll1_table(table)
print("\n")

###############################################################
# Create parse tree in dictionary form

def parse_string(input_string, table, start_symbol):
    input_string += '$'
    stack = [start_symbol]
    cursor = 0
    parse_tree = []

    while stack:
        top = stack.pop()        
        if top == '$' and cursor == len(input_string):
            break
        
        if cursor >= len(input_string):
            raise ValueError(f"Unexpected end of input")
        
        current_symbol = input_string[cursor]
        if(current_symbol=='i' and input_string[cursor+1]=='d'):
            current_symbol='id'

        if top in table:
            production = table[top].get(current_symbol)
            if not production:
                raise ValueError(f"Unexpected symbol {current_symbol} at position {cursor}")
            if production != 'ε':
                extended_production = []
                i = 0
                while i < len(production):
                    if i + 1 < len(production) and production[i + 1] == '`':
                        extended_production.append(production[i:i+2])
                        i += 2
                    elif i + 1 < len(production) and production[i] == 'i' and production[i + 1] == 'd':
                        extended_production.append(production[i:i+2])
                        i += 2    
                    else:
                        extended_production.append(production[i])
                        i += 1
                stack.extend(reversed(extended_production))
            parse_tree.append((top, production))
        elif top == current_symbol:
            cursor += len(current_symbol)
        elif top == 'ε':
            continue
        else:
            raise ValueError(f"Unexpected symbol {top} at position {cursor}")

    return parse_tree

input_string = input("Write the input to make the parser tree (Example: id+id*id) :\n")
parse_tree = parse_string(input_string, table, 'E')

###############################################################

# Create parse tree using TreeNode class and visualize it

class TreeNode:
    def __init__(self, value):
        self.value = value
        self.children = []

    def add_child(self, child_node):
        self.children.append(child_node)

def build_parse_tree(parse_tree_rules):
    root = TreeNode('E')
    stack = [(root, 'E')]
    rule_index = 0
    
    while stack:
        current_node, current_symbol = stack.pop()
        
        if rule_index < len(parse_tree_rules) and parse_tree_rules[rule_index][0] == current_symbol:
            parent, expansion = parse_tree_rules[rule_index]
            rule_index += 1
            flagPrime=0
            flagid=0
            if expansion == 'ε':
                new_node = TreeNode('')
                current_node.add_child(new_node)
            
            else:
                for symbol in reversed(expansion):
                    if symbol == '`':
                        flagPrime=1
                        continue
                    if flagPrime==1:
                        symbol+= '`'
                        flagPrime=0

                    if symbol == 'd':
                        flagid=1
                        continue
                    if flagid==1:
                        symbol+= 'd'
                        flagid=0

                    if symbol != 'ε':
                        new_node = TreeNode(symbol)
                        current_node.add_child(new_node)
                        stack.append((new_node, symbol))
    
    return root

def print_tree(node, prefix="", is_last=True):
    print(prefix, "`- " if is_last else "|- ", node.value if node.value else "''", sep="")
    prefix += "   " if is_last else "|  "    
    child_count = len(node.children)
    for i, child in enumerate(node.children):
        is_last_child = (i == (child_count - 1))
        print_tree(child, prefix, is_last_child)

def visualize_tree(node):
    dot = Digraph()
    
    def add_nodes_edges(node, dot, parent=None):
        node_id = str(id(node))
        dot.node(node_id, label=node.value if node.value else "''")
        if parent:
            dot.edge(parent, node_id)
        for child in node.children:
            add_nodes_edges(child, dot, node_id)
    
    add_nodes_edges(node, dot)
    return dot


parse_tree_root = build_parse_tree(parse_tree)
print_tree(parse_tree_root)

# Save and show the parse tree
dot = visualize_tree(parse_tree_root)
output_path = dot.render('parse_tree', format='jpeg')
dot.view(output_path)