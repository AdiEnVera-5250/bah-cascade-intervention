import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
import pandas as pd

def add_homophilic_node(G, id, n_edges, p, h, labels, rng):
    G.add_node(id)

    labels.append(rng.choice([0, 1], p=[p, 1 - p]))
    G.nodes[id]['label'] = labels[id]

    if id == 0:
        return

    existing_nodes = np.array([n for n in G.nodes() if n != id])

    probabilities = calculate_probabilities(G, existing_nodes, labels, id, h)

    target = prepare_edges(n_edges, existing_nodes, probabilities, rng)
    add_edges(G, id, target)

def calculate_probabilities(G, existing_nodes, labels, id, h):
    eps = 1e-6
    same = np.array([labels[n] == labels[id] for n in existing_nodes], dtype=bool)
    h_wgt = np.where(same, h, 1 - h)

    degrees = np.array([G.degree(n) for n in existing_nodes], dtype=float)

    wgts = (degrees + eps) * h_wgt
    if np.sum(wgts) > 0:
        probabilities = wgts / np.sum(wgts)
    else:
        return None

    return probabilities

def prepare_edges(n_edges, existing_nodes, probabilities, rng):
    if probabilities is not None:
        non_zero = probabilities > 0
        options = existing_nodes[non_zero]
        if len(options) == 0:
            return set()

        k = min(n_edges, len(options))
        p = probabilities[non_zero]
        p = p/np.sum(p)

        target = rng.choice(options, size=k, replace=False, p=p)
    else:
        return set()
    
    return set(target.tolist())

def add_edges(G, id, targets):
    for t in targets:
        G.add_edge(id, t)

def generate_bah(n_nodes, n_edges, p, h, seed=None):
    if(p < 0 or p > 1):
        raise ValueError("Fraction must be between 0 and 1.")

    if(h < 0 or h > 1):
        raise ValueError("Homophily must be between 0 and 1.")

    if n_nodes < 1:
        raise ValueError("Number of nodes must be at least 1.")

    if (n_edges < 1 or n_edges >= n_nodes):
        raise ValueError("Number of edges must be at least 1 and less than the number of nodes.")

    rng = np.random.default_rng(seed)
    Graph = nx.Graph()
    labels = []

    for i in range(n_nodes):
        add_homophilic_node(Graph, i, n_edges, p, h, labels, rng)

    return Graph

def generate_bah_int(init_n_nodes, inter_n_nodes, n_edges, init_p, inter_p, init_h, inter_h, seed=None):
    if inter_p is None:
        if init_p < 0 or init_p > 1:
            raise ValueError("Initial proportion must be between 0 and 1.")
        else:
            new_fraction = init_p

    if inter_p < 0 or inter_p > 1:
        raise ValueError("Intervention proportion fraction must be between 0 and 1.")
    
    if inter_h is None:
        if init_h < 0 or init_h > 1:
            raise ValueError("Initial homophily must be between 0 and 1.")
        else:
            inter_h = init_h

    if inter_h < 0 or inter_h > 1:
        raise ValueError("Intervention homophily must be between 0 and 1.")

    if init_n_nodes < 1:
        raise ValueError("Initial number of nodes must be at least 1.")

    if inter_n_nodes <= 0:
        raise ValueError("Intervention number of nodes must be at least 0.")

    if (n_edges < 1 or n_edges >= init_n_nodes):
        raise ValueError("Number of edges must be at least 1 and less than the number of nodes.")

    rng = np.random.default_rng(seed)
    G = generate_bah(init_n_nodes, n_edges, init_p, init_h, seed=seed)
    labels = [G.nodes[n]['label'] for n in G.nodes()]

    rng = np.random.default_rng(seed + 1 if seed is not None else None)

    for i in range(inter_n_nodes):
        add_homophilic_node(G, i + init_n_nodes, n_edges, inter_p, inter_h, labels, rng)

    return G

def simulate_cascade_gw(G, thr, init_set=None, seed=None):
    if G.number_of_nodes() == 0:
        return 0.0

    if thr is None:
        thr = 0
    
    if not (0 <= thr <= 1):
        raise ValueError("Threshold must be between 0 and 1.")

    if init_set is None:
        rng = np.random.default_rng(seed)
        active = {int(rng.choice(list(G.nodes())))}
    else:
        active = set(init_set)

    t = 0
    while True:
        new_active = set()
        for node in G.nodes():
            if node not in active:
                neighbors = set(G.neighbors(node))
                if not neighbors:
                    continue
                frac = len(neighbors & active) / len(neighbors)
                if frac >= thr:
                    new_active.add(node)
        if not new_active:
            break
        active.update(new_active)
        t +=1

    return active,t

def analyze_cascade(G, active_nodes):
    n_actives, t = len(active_nodes)
    n_nodes = G.number_of_nodes()

    comp = 0
    if n_actives != 0:
        for n in active_nodes:
            if G.nodes[n].get('label') == 0:
                comp += 1

    return {
        'Size': n_actives/n_nodes,
        'Composition': comp/n_actives,
        'Time': t
        }
        
def analyze_stats(input = []):
    series = pd.Series(input)

    return {
        'Mean': np.mean(series),
        'Median': np.median(series),
        'Std': np.std(series),
        'Q1': np.quantile(series, 0.25),
        'Q3': np.quantile(series, 0.75)
    }

def analyze_network_cascades(G, thr, p_active, n_cascades, seed=None):
    n_nodes = G.number_of_nodes()
    labels = [G.nodes[n]['label'] for n in G.nodes()]

    init_zeros = [G.nodes[n] for n in labels == 0]
    init_ones = [G.nodes[n] for n in labels == 1]

    init_sets = [init_zeros, init_ones]

    results = {}

    for i in range(len(init_sets)):
        cascade_results = []

        for j in range(n_cascades):
            rng = np.random.default_rng(seed + j)
            init = int(rng.choice(init_sets[i], round(min(n_nodes*p_active, len(init_sets[i])))))

            cascade_results.append(simulate_cascade_gw(G, thr, init, seed+i))

        size = [r['Size'] for r in cascade_results]
        composition_zeros = [r['Composition'] for r in cascade_results]
        composition_ones = 1 - composition_zeros
        time = size = [r['Time'] for r in cascade_results]

        sizes_analisis = analyze_stats(size)
        composition_zeros_analisis = analyze_stats(composition_zeros)
        composition_ones_analisis = analyze_stats(composition_ones)
        time_analisis = analyze_stats(time)

        sizes_analisis = {f'Size {k}': v for k,v in sizes_analisis.items()}
        composition_zeros_analisis = {f'Composition zeros {k}': v for k,v in composition_zeros_analisis.items()}
        composition_ones_analisis = {f'Composition ones {k}': v for k,v in composition_ones_analisis.items()}
        time_analisis = {f'Time {k}': v for k,v in time_analisis.items()}
        
        analisis = sizes_analisis | composition_zeros_analisis | composition_ones_analisis | time_analisis

        if i == 0:
            results = {f'{k} ({i})': v for k,v in analisis.items()}
        else:
            results = results | {f'{k} ({i})': v for k,v in analisis.items()}

    return results

def network_experiment(n_networks, n_cascades, init_n_nodes, inter_n_nodes, n_edges, init_p, inter_p, init_h, inter_h, thr, p_active, seed=None):
    results = {}
    for i in range(n_networks):
        G = generate_bah_int(init_n_nodes, inter_n_nodes, n_edges, init_p, inter_p, init_h, inter_h, seed + i)
        results_aux = analyze_network_cascades(G, thr, p_active, n_cascades, seed+i)

        if i == 0:
            results = {'Seed': [seed]} | {k: [v] for k,v in results_aux.items()}
        else:
            results['Seed'].append(seed+i)
            for k in results_aux.keys():
                results[k].append(results_aux[k])

    return results

G = generate_bah(n_nodes=15, n_edges=1, p=0.2, h=0.8, seed=42)

pos = nx.spring_layout(G)
nx.draw(G, pos, with_labels=True, node_color=[G.nodes[n]['label'] for n in G.nodes()])
plt.show()

'''
edges_number_set = {1, 2}
fractions_set = {0.1, 0.2, 0.3, 0.4, 0.5}
homophily_set = {0.0, 0.2, 0.5, 0.8, 1.0} 
threshold_set = {0.1, 0.2, 0.3}
initial_nodes_fraction = {0.01, 0.05, 0.10, 0.15}
labels_set = {0, 1, None}

metrics = {'Seed','Relative Size', 'Mean', 'Median', 'Deviation', 'Probability > 50%', 'Absolute diference'}
network_seeds_number = 50
cascade_seeds_number = 50
'''