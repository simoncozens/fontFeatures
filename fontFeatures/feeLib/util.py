import functools

def compare(l, token, r):
    if not r: return bool(l)
    comparator_tokens = [">=", "<=", "==", "<", ">"]
    comparator_attrs = ["__ge__", "__le__", "__eq__", "__lt__", "__gt__"]
    comparators = dict(zip(comparator_tokens, comparator_attrs))
    return (getattr(l, comparators[token])(r))

def extend_args_until(args, n, obj=list):
    while len(args) < n:
        args.append(obj())
    return args
