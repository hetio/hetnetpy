import pandas
import matplotlib.backends.backend_pdf
import seaborn

def get_degrees_for_metanode(graph, metanode):
    """
    Return a dataframe that reports the degree of each metaedge for
    each node of kind metanode.
    """
    metanode_to_nodes = graph.get_metanode_to_nodes()
    nodes = metanode_to_nodes[metanode]
    rows = list()
    for node in nodes:
        for metaedge, edges in node.edges.items():
            rows.append((node, metaedge, len(edges)))
    df = pandas.DataFrame(rows, columns=['node', 'metaedge', 'degree'])
    return df

def plot_degrees_for_metanode(graph, metanode, col_wrap=2):
    """
    Plots histograms of the degree distribution of each metaedge
    incident to the metanode. Each metaedge receives a facet in
    a seaborn.FacetGrid.
    """
    degree_df = get_degrees_for_metanode(graph, metanode)
    grid = seaborn.FacetGrid(degree_df, col='metaedge', sharex=False, sharey=False, col_wrap=col_wrap)
    grid.map(seaborn.distplot, 'degree', kde=False)
    grid.set_titles('{col_name}')
    return grid

def plot_degrees(graph, path):
    """
    Creates a multipage pdf with a page for each metanode showing degree
    distributions.
    """
    pdf_pages = matplotlib.backends.backend_pdf.PdfPages(path)
    for metanode in graph.metagraph.get_nodes():
        grid = plot_degrees_for_metanode(graph, metanode)
        grid.savefig(pdf_pages, format='pdf')
    pdf_pages.close()
