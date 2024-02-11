import gurobipy as gp
from gurobipy import GRB
from itertools import combinations, permutations, product
import numpy as np
import os.path

try:

    # Needs to be >= 2.
    number_of_colors = 6

    # Create good tuples with convention (color(xy), color(xz), color(yz)) for x < y < z.
    good_tuples = []

    # First type of good tuples.
    for (i,j) in combinations(range(number_of_colors), 2):
        good_tuples.append((i, j, i))
        good_tuples.append((j, i, j))

    # Second type of good tuples. 
    good_tuples += list(permutations(range(number_of_colors), r = 3))

    # Make immutable for efficiency.
    good_tuples = tuple(good_tuples)

    """
        Matrix and vector for ILP are now constructed. 
    """ 

    good_tuples_set = set(good_tuples)

    # Generate edges of 5-clique. 
    edges = tuple(combinations(range(5), 2))

    # Palette can at most have size 6.
    bad_palettes = [set() for _ in range(6)]

    # Generate the triangles per position of apex vertex.
    triangles_per_apex = []
    for it in range(5):
        triangles = []
        for (j, k) in combinations([j for j in range(5) if j != it], 2):
            triangles.append(tuple(sorted((it, j, k))))
        triangles_per_apex.append(tuple(triangles))

    # Iterate over all colorings to get palettes. 
    for coloring in product(range(number_of_colors), repeat=10):

        # Generate triangle of 5-clique. 
        for it in range(5):
            
            palette = tuple(sorted({(coloring[edges.index((a, b))], coloring[edges.index((a, c))], coloring[edges.index((b, c))]) for (a, b, c) in triangles_per_apex[it]}))

            if good_tuples_set.issuperset(palette):
                bad_palettes[len(palette) - 1].add(palette)

    # Remove non-minimal bad palettes.
    checked = set() 
    minimal = set()

    def extract_minimal(input: tuple):
        checked.add(input)

        if len(input) == 6: 
            return 

        for tup in good_tuples_set.difference(input):
            s = set(input)
            s.add(tup)
            new_tup = tuple(sorted(s))

            if checked.__contains__(new_tup):
                continue
            
            if bad_palettes[len(new_tup) - 1].__contains__(new_tup):
                extract_minimal(new_tup)
        return 

    for palettes in bad_palettes:
        for palette in palettes:
            if not checked.__contains__(palette):
                minimal.add(palette)
                extract_minimal(palette)

    bad_palettes = tuple(minimal)

    A = np.zeros((len(bad_palettes), len(good_tuples)), dtype=np.bool_) 

    for (it, palette) in enumerate(bad_palettes):
        for tup in palette:
            A[it, good_tuples.index(tup)] = 1

    b = np.empty(len(bad_palettes), dtype=np.ubyte)

    for (it, palette) in enumerate(bad_palettes):
        b[it] = len(palette) - 1

    """
        Gurobi code
    """

    # Setup the Gurobi environment with the WLS license
    e = gp.Env(empty=True)

    wlsaccessID = os.getenv('GRB_WLSACCESSID','undefined')
    e.setParam('WLSACCESSID', wlsaccessID)

    licenseID = os.getenv('GRB_LICENSEID', '0')
    e.setParam('LICENSEID', int(licenseID))

    wlsSecrets = os.getenv('GRB_WLSSECRET','undefined')
    e.setParam('WLSSECRET', wlsSecrets)

    e.setParam('CSCLIENTLOG', int(3))

    e.start()

    # Create the model within the Gurobi environment
    m = gp.Model(env=e, name="ILP")

    # Create variables
    x = m.addMVar(len(good_tuples), vtype = GRB.BINARY, name = "assign")

    # Set objective 
    m.setObjective(x.sum(), GRB.MAXIMIZE)

    # Add constraints
    m.addConstr(A @ x <= b)
    m.addConstr(9 * x.sum() <= 4 * (number_of_colors ** 3))

    # Optimize model
    m.optimize()

    for it, v in enumerate(m.getVars()):
        print('%s %g' % (good_tuples[it], v.X))
    
    # Close everything
    m.dispose()
    e.close()

except gp.GurobiError as e:
    print('Error code ' + str(e.errno) + ": " + str(e))

except AttributeError:
    print('Encountered an attribute error')