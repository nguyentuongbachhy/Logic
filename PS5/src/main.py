import itertools, os
from logic import Atom, Not, And, Or, convert_to_clauses, check_complementary, clauses_to_expr, simplify, to_cnf

INPUT = "./PS5/input"
OUTPUT = "./PS5/output"


def resolve(clause_i, clause_j, clauses):
    ci = convert_to_clauses(clause_i)
    cj = convert_to_clauses(clause_j)
    resolved_clause = []

    for literal in ci:
        negated_literal = Not(literal)
        if negated_literal in cj:
            temp_ci = ci.copy()
            temp_cj = cj.copy()
            temp_ci.remove(literal)
            temp_cj.remove(negated_literal)
            if not temp_ci and not temp_cj:
                resolved_clause.append(Atom("{}"))
            else:
                clause = temp_ci + temp_cj
                clause.sort(key=lambda x : hash(x) if isinstance(x, Atom) else hash(Not(x)))
                if not check_complementary(clause) and clause not in clauses:
                    resolved_clause.append(clause)

    if len(resolved_clause) == 0:
        return Atom("False")

    return clauses_to_expr(resolved_clause)


def pl_resolution(query, clauses):
    negated_query = Not(query)
    clauses.append(negated_query)

    result = []


    while True:

        pairs = list(itertools.combinations(range(len(clauses)), 2))

        new_clauses = []

        for pair in pairs:
            new_clause = simplify(to_cnf(resolve(clauses[pair[0]], clauses[pair[1]], clauses)))
            if new_clause != Atom("False") and new_clause not in new_clauses and new_clause not in clauses:
                new_clauses.append(new_clause)

        result.append(new_clauses)

        if not new_clauses:
            return result, False
        else:
            if Atom("{}") in new_clauses:
                return result, True
            else:
                for expr in new_clauses:
                    if expr not in clauses and simplify(expr) not in [Atom("True"), Atom("False")]:
                        clauses.append(expr)

def parse_clause(line: str):
    tokens = line.replace('(', ' ( ').replace(')', ' ) ').split()
    stack = []
    operators = []

    def apply_operator():
        operator = operators.pop()
        if operator == "OR":
            right = stack.pop()
            left = stack.pop()
            stack.append(Or(left, right))

        elif operator == "AND":
            right = stack.pop()
            left = stack.pop()
            stack.append(And(left, right))

    for token in tokens:
        if token == '(':
            operators.append(token)
        elif token == ')':
            while operators and operators[-1] != '(':
                apply_operator()
            operators.pop()
        elif token in {"OR", "AND"}:
            while operators and operators[-1] in {"OR", "AND"}:
                apply_operator()
            operators.append(token)
        elif token.startswith("-"):
            stack.append(Not(Atom(token[1:])))
        else:
            stack.append(Atom(token))

    while operators:
        apply_operator()

    return stack[0] if stack else None


def readKB(filepath):
    with open(filepath, 'r') as f:
        lines = f.readlines()

    query = to_cnf(parse_clause(lines[0]))


    clauses = []

    num_clauses = int(lines[1])

    for i in range(2, num_clauses + 2):
        cnf_clauses = to_cnf(parse_clause(lines[i]))
        clauses.append(cnf_clauses)

    return query, clauses

def write_output(result, check, filepath):
    filepath = filepath.replace("in", "out")
    with open(filepath, 'w') as f:
        for exprs in result:
            f.write(str(len(exprs)) + '\n')
            for expr in exprs:
                f.write(str(expr) + '\n')
        if check:
            f.write('YES')
        else:
            f.write('NO')


def main():
    for filename in os.listdir(INPUT):
        filepath = os.path.join(INPUT, filename)
        query, clauses = readKB(filepath)

        result, check = pl_resolution(query, clauses)

        write_output(result, check, filepath)


if __name__ == "__main__":
    main()
    