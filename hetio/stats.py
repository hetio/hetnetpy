import pandas
import matplotlib
import matplotlib.backends.backend_pdf
import seaborn

def get_degrees_for_metanode(graph, metanode):
    """
    Return a dataframe that reports the degree of each metaedge for
    each node of kind metanode.
    """
    metanode_to_nodes = graph.get_metanode_to_nodes()
    nodes = metanode_to_nodes.get(metanode, [])
    rows = list()
    for node in nodes:
        for metaedge, edges in node.edges.items():
            rows.append((node, metaedge, len(edges)))
    df = pandas.DataFrame(rows, columns=['node', 'metaedge', 'degree'])
    return df.sort(['node', 'metaedge'])

def plot_degrees_for_metanode(graph, metanode, col_wrap=2, facet_height=4):
    """
    Plots histograms of the degree distribution of each metaedge
    incident to the metanode. Each metaedge receives a facet in
    a seaborn.FacetGrid.
    """
    degree_df = get_degrees_for_metanode(graph, metanode)
    grid = seaborn.FacetGrid(degree_df, col='metaedge', sharex=False, sharey=False, col_wrap=col_wrap, size=facet_height)
    grid.map(seaborn.distplot, 'degree', kde=False)
    grid.set_titles('{col_name}')
    return grid

def plot_degrees(graph, path):
    """
    Creates a multipage pdf with a page for each metanode showing degree
    distributions.
    """
    # Temporarily disable `figure.max_open_warning`
    max_open = matplotlib.rcParams['figure.max_open_warning']
    matplotlib.rcParams['figure.max_open_warning'] = 0
    pdf_pages = matplotlib.backends.backend_pdf.PdfPages(path)
    for metanode in graph.metagraph.get_nodes():
        grid = plot_degrees_for_metanode(graph, metanode)
        grid.savefig(pdf_pages, format='pdf')
    pdf_pages.close()
    matplotlib.rcParams['figure.max_open_warning'] = max_open

def get_metanode_df(graph):
    rows = list()
    for metanode, nodes in graph.get_metanode_to_nodes().items():
        series = pandas.Series()
        series['metanode'] = metanode
        series['abbreviation'] = metanode.abbrev
        metaedges = set()
        for metaedge in metanode.edges:
            metaedges |= {metaedge, metaedge.inverse}
        series['metaedges'] = sum([not metaedge.inverted for metaedge in metaedges])
        series['nodes'] = len(nodes)
        series['unconnected_nodes'] = sum(not any(node.edges.values()) for node in nodes)
        rows.append(series)
    return pandas.DataFrame(rows).sort('metanode')

def get_metaedge_df(graph):
    rows = list()
    for metaedge, edges in graph.get_metaedge_to_edges().items():
        series = pandas.Series()
        series['metaedge'] = metaedge
        series['abbreviation'] = metaedge.get_abbrev()
        series['inverted'] = int(metaedge.inverted)
        series['edges'] = len(edges)
        series['source_nodes'] = len(set(edge.source for edge in edges))
        series['target_nodes'] = len(set(edge.target for edge in edges))
        rows.append(series)
    return pandas.DataFrame(rows).sort('metaedge')
