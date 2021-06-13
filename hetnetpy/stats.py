import matplotlib
import matplotlib.backends.backend_pdf
import pandas
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
            rows.append((node.identifier, node.name, str(metaedge), len(edges)))
    df = pandas.DataFrame(rows, columns=["node_id", "node_name", "metaedge", "degree"])
    return df.sort_values(["node_name", "metaedge"])


def get_metanode_to_degree_df(graph):
    """
    Return a dictionary of metanode to degree_df, where degree_df is a
    wide-format dataframe of node degrees.
    """
    metanode_to_degree_df = dict()
    for metanode in graph.metagraph.get_nodes():
        degree_df = get_degrees_for_metanode(graph, metanode)
        if degree_df.empty:
            continue
        degree_df = pandas.pivot_table(
            degree_df,
            values="degree",
            index=["node_id", "node_name"],
            columns="metaedge",
        ).reset_index()
        metanode_to_degree_df[metanode] = degree_df
    return metanode_to_degree_df


def degrees_to_excel(graph, path):
    """
    Write node degrees to a multisheet excel spreadsheet. Path should end in
    a valid excel extension that `pandas.ExcelWriter` can detect, such as
    `.xlsx`.
    """
    metanode_to_degree_df = get_metanode_to_degree_df(graph)
    writer = pandas.ExcelWriter(path)
    for metanode, degree_df in metanode_to_degree_df.items():
        degree_df.to_excel(writer, sheet_name=str(metanode), index=False)
    if writer.engine == "xlsxwriter":
        for sheet in writer.sheets.values():
            sheet.freeze_panes(1, 0)
    writer.close()


def plot_degrees_for_metanode(graph, metanode, col_wrap=2, facet_height=4):
    """
    Plots histograms of the degree distribution of each metaedge
    incident to the metanode. Each metaedge receives a facet in
    a seaborn.FacetGrid.
    """
    degree_df = get_degrees_for_metanode(graph, metanode)
    grid = seaborn.FacetGrid(
        degree_df,
        col="metaedge",
        sharex=False,
        sharey=False,
        col_wrap=col_wrap,
        size=facet_height,
    )
    grid.map(seaborn.distplot, "degree", kde=False)
    grid.set_titles("{col_name}")
    return grid


def plot_degrees(graph, path):
    """
    Creates a multipage pdf with a page for each metanode showing degree
    distributions.
    """
    # Temporarily disable `figure.max_open_warning`
    max_open = matplotlib.rcParams["figure.max_open_warning"]
    matplotlib.rcParams["figure.max_open_warning"] = 0
    pdf_pages = matplotlib.backends.backend_pdf.PdfPages(path)
    for metanode in graph.metagraph.get_nodes():
        grid = plot_degrees_for_metanode(graph, metanode)
        grid.savefig(pdf_pages, format="pdf")
    pdf_pages.close()
    matplotlib.rcParams["figure.max_open_warning"] = max_open


def get_metanode_df(graph):
    rows = list()
    for metanode, nodes in graph.get_metanode_to_nodes().items():
        series = pandas.Series()
        series["metanode"] = metanode
        series["abbreviation"] = metanode.abbrev
        metaedges = set()
        for metaedge in metanode.edges:
            metaedges |= {metaedge, metaedge.inverse}
        series["metaedges"] = sum([not metaedge.inverted for metaedge in metaedges])
        series["nodes"] = len(nodes)
        series["unconnected_nodes"] = sum(
            not any(node.edges.values()) for node in nodes
        )
        rows.append(series)

    metanode_df = pandas.DataFrame(rows).sort_values("metanode")
    return metanode_df


def get_metaedge_df(graph):
    rows = list()
    for metaedge, edges in graph.get_metaedge_to_edges(exclude_inverts=True).items():
        series = pandas.Series()
        series["metaedge"] = str(metaedge)
        series["abbreviation"] = metaedge.abbrev
        series["edges"] = len(edges)
        series["source_nodes"] = len(set(edge.source for edge in edges))
        series["target_nodes"] = len(set(edge.target for edge in edges))
        rows.append(series)
    metaedge_df = pandas.DataFrame(rows).sort_values("metaedge")
    return metaedge_df


def get_metaedge_style_df(metagraph):
    """
    Get metaedge representations in various styles.
    """
    rows = list()
    for metaedge in metagraph.get_edges(exclude_inverts=False):
        series = pandas.Series()
        series["metaedge"] = str(metaedge)
        series["unicode_metaedge"] = metaedge.get_unicode_str()
        series["standard_metaedge"] = str(
            metaedge.inverse if metaedge.inverted else metaedge
        )
        series["abbreviation"] = metaedge.abbrev
        series["standard_abbreviation"] = metaedge.get_standard_abbrev()
        series["source"] = str(metaedge.source)
        series["target"] = str(metaedge.target)
        series["inverted"] = int(metaedge.inverted)
        rows.append(series)
    metaedge_style_df = pandas.DataFrame(rows).sort_values("metaedge")
    return metaedge_style_df
