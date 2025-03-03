def _print_vector(name, vector):
    n = len(vector)
    print("{}:".format(name))
    if n > 20: print(vector[:10], '...', vector[-10:])
    else: print(vector)

def print_vectors(**kwargs):
    for k, v in kwargs.items(): _print_vector(k, v)