class Atom:
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return self.name

    def __eq__(self, other):
        if isinstance(other, Atom):
            return self.name == other.name
        if isinstance(other, Not):
            return other.is_not == False and self == other.operand
        return False
    
    def __hash__(self):
        return ord(self.name)

class Not:
    def __init__(self, operand):
        if isinstance(operand, Not):
            self.is_not = not operand.is_not
            self.operand = operand.operand
            if not self.is_not:
                self.__class__ = operand.operand.__class__
                self.__dict__.update(operand.operand.__dict__)
        else:
            self.is_not = True
            self.operand = operand

    def __repr__(self):
        prefix = "-" if self.is_not else ""
        return f"{prefix}{self.operand}"
    
    def __eq__(self, other):
        if isinstance(other, Not):
            return self.is_not == other.is_not and self.operand == other.operand
        if isinstance(other, Atom):
            return not self.is_not and self.operand == other
        return False

    def __hash__(self):
        return ord(self.operand) if not self.is_not else 45 * 256 + hash(self.operand)

class And:
    def __init__(self, *operands):
        flat_operands = []
        for op in operands:
            if isinstance(op, And):
                flat_operands.extend(op.operands)
            else:
                flat_operands.append(op)
        self.operands = list(set(flat_operands))

    def __repr__(self):
        if len(self.operands) == 1:
            return str(self.operands[0])
        return " AND ".join(
            f"({op})" if isinstance(op, Or) else str(op) for op in self.operands
        )
    
    def __eq__(self, other):
        if isinstance(other, And):
            return set(self.operands) == set(other.operands)
        return False

    def __hash__(self):
        return hash(("Or", tuple(sorted(hash(op) for op in self.operands))))

    def simplify(self):
        simplified_operands = [simplify(op) for op in self.operands]

        if check_complementary(simplified_operands):
            return Atom("False")

        new_operands = []
        for op in simplified_operands:
            if isinstance(op, Or):
                for inner_op in op.operands:
                    distributed = And(inner_op, *[x for x in simplified_operands if x != op]).simplify()
                    new_operands.append(distributed)
            else:
                new_operands.append(op)

        new_operands = [op for op in new_operands if not (isinstance(op, Atom) and op.name == "True")]

        if not new_operands:
            return Atom("True")
        if len(new_operands) == 1:
            return new_operands[0]

        new_operands.sort(key=lambda x: hash(x) if isinstance(x, Atom) else hash(Not(x)))

        return And(*new_operands)

class Or:
    def __init__(self, *operands):
        flat_operands = []
        for op in operands:
            if isinstance(op, Or):
                flat_operands.extend(op.operands)
            else:
                flat_operands.append(op)
        self.operands = list(set(flat_operands))

    def __repr__(self):
        if len(self.operands) == 1:
            return str(self.operands[0])
        return " OR ".join(
            f"({op})" if isinstance(op, And) else str(op) for op in self.operands
        )
    
    def __eq__(self, other):
        if isinstance(other, Or):
            return set(self.operands) == set(other.operands)
        return False

    def __hash__(self):
        return hash(("Or", tuple(sorted(hash(op) for op in self.operands))))

    def simplify(self):
        simplified_operands = [simplify(op) for op in self.operands]

        if check_complementary(simplified_operands):
            return Atom("True")

        new_operands = [op for op in simplified_operands if not (isinstance(op, Atom) and op.name == "False")]

        if not simplified_operands:
            return Atom("False")
        if len(simplified_operands) == 1:
            return simplified_operands[0]
        
        new_operands.sort(key=lambda x: hash(x) if isinstance(x, Atom) else hash(Not(x)))

        return Or(*new_operands)

def simplify(expr):
    if isinstance(expr, Atom):
        return expr
    if isinstance(expr, Not):
        return Not(simplify(expr.operand))
    if isinstance(expr, And):
        return expr.simplify()
    if isinstance(expr, Or):
        return expr.simplify()
    return expr

def to_cnf(expr):
    if isinstance(expr, Atom):
        return expr
    if isinstance(expr, Not):
        if isinstance(expr.operand, Not):
            return to_cnf(expr.operand.operand)
        if isinstance(expr.operand, And):
            return to_cnf(Or(*(Not(op) for op in expr.operand.operands)))
        if isinstance(expr.operand, Or):
            return to_cnf(And(*(Not(op) for op in expr.operand.operands)))
        return expr

    if isinstance(expr, And):
        return And(*(to_cnf(op) for op in expr.operands))

    if isinstance(expr, Or):
        operands = [to_cnf(op) for op in expr.operands]

        result = operands[0]
        for operand in operands[1:]:
            if isinstance(result, And):
                result = And(*(to_cnf(Or(op, operand)) for op in result.operands))
            elif isinstance(operand, And):
                result = And(*(to_cnf(Or(result, op)) for op in operand.operands))
            else:
                result = Or(result, operand)

        return result

    return expr

def convert_to_clauses(cnf):
    if isinstance(cnf, Atom):
        return [cnf]
    if isinstance(cnf, Not):
        return [Not(cnf.operand)]
    if isinstance(cnf, And):
        clauses = []
        for operand in cnf.operands:
            converted_clause = [convert_to_clauses(operand)]
            clauses.extend(converted_clause)
        return clauses
    if isinstance(cnf, Or):
        operands = []
        for operand in cnf.operands:
            if isinstance(operand, Or):
                operands.extend(operand.operands)
            else:
                operands.append(operand)
        return operands
    return []

def clauses_to_expr(clauses):
    if not clauses:
        return None
    
    expr = []
    for clause in clauses:
        if isinstance(clause, (Atom, Not)):
            expr.append(clause)
        elif len(clause) == 1:
            expr.append(next(iter(clause)))
        else:
            expr.append(Or(*clause))
    
    if len(expr) == 1:
        return expr[0]
    else:
        return And(*expr)


def propagate(clauses, literal):
    simplified = []
    for clause in clauses:
        if literal in clause:
            continue
        if Not(literal) in clause:
            new_clause = clause - {Not(literal)}
            simplified.append(new_clause)
        else:
            simplified.append(clause)
    return simplified


def dpll(clauses, assignment={}):
    if not clauses:
        return True
    if any(not clause for clause in clauses):
        return False

    for clause in clauses:
        if len(clause) == 1:
            literal = next(iter(clause))
            return dpll(propagate(clauses, literal), {**assignment, literal: True})

    literal = next(iter(next(iter(clauses))))

    return (
        dpll(propagate(clauses, literal), {**assignment, literal: True}) or
        dpll(propagate(clauses, Not(literal)), {**assignment, literal: False})
    )


def satisfiable(expr):
    cnf = to_cnf(expr)
    clauses = convert_to_clauses(cnf)
    return dpll(clauses)


def check_complementary(clause):
    for atom in clause:
        neg_atom = Not(atom) if not isinstance(atom, Not) else atom.operand
        if neg_atom in clause:
            return True
    return False
