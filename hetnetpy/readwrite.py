import collections
import csv
import importlib
import io
import json
import mimetypes
import operator
import pickle
import random
import re
from urllib.request import urlopen

# Import fspath function to convert path-like objects to string paths
try:
    from os import fspath
except ImportError:
    fspath = str

from hetnetpy.hetnet import Graph, MetaGraph


def read_graph(path, formatting=None):
    """Read a graph from a path"""
    writable = extract_writable(path, formatting)
    graph = graph_from_writable(writable)
    return graph


def read_metagraph(path, formatting=None):
    """Read a metagraph from a path"""
    writable = extract_writable(path, formatting)
    metagraph = metagraph_from_writable(writable)
    return metagraph


def write_graph(graph, path, formatting=None, masked=True):
    """Write a graph to the specified path."""
    writable = writable_from_graph(graph, masked=masked)
    dump(writable, path, formatting)


def write_metagraph(metagraph, path, formatting=None):
    """Write a graph to the specified path."""
    writable = writable_from_metagraph(metagraph)
    dump(writable, path, formatting)


def open_read_file(path, text_mode=True):
    """
    Return a file object from the path.
    Automatically detects and supports urls and gzip/bzip2 compression.

    text_mode : bool
        whether to return a text mode or byte mode file
    """
    path = fspath(path)
    opener = get_opener(path)
    mode = "rt" if text_mode else "rb"
    # Read from URL
    if re.match("^(http|ftp)s?://", path):

        with urlopen(path) as response:
            content = response.read()

        if text_mode and opener == io.open:
            encoding = response.headers.get_content_charset()
            text = content.decode(encoding)
            return io.StringIO(text)

        else:
            b = io.BytesIO(content)
            return opener(b, mode)

    # Read from file
    return opener(path, mode)


def open_write_file(path, mode="wt"):
    """
    Return a write-text mode file object from the path.
    Automatically detects and supports gzip/bzip2 compression.
    """
    path = fspath(path)
    opener = get_opener(path)
    return opener(path, mode)


def load(read_file, formatting):
    """
    Return a writable from read_file. Support json, and pkl formats.
    """

    # JSON formatted
    if formatting == "json":
        return json.load(read_file)

    # pickle formatted
    if formatting == "pkl":
        return pickle.load(read_file)

    # Unsupported format
    raise ValueError("Unsupported format: {}".format(formatting))


def extract_writable(path, formatting=None):
    """Extract a writable from the file specified by path"""
    if formatting is None:
        formatting = detect_formatting(path)
    format_to_text_mode = {"json": True, "pkl": False}
    read_file = open_read_file(path, text_mode=format_to_text_mode[formatting])
    writable = load(read_file, formatting)
    read_file.close()
    return writable


def dump(writable, path, formatting=None):
    """Dump a writable to a path. Support json, and pkl formats."""
    if formatting is None:
        formatting = detect_formatting(path)

    # JSON formatted
    if formatting == "json":
        write_file = open_write_file(path)
        json.dump(writable, write_file, indent=2, cls=Encoder)
        write_file.close()

    # pickle formatted
    elif formatting == "pkl":
        write_file = open_write_file(path, "wb")
        pickle.dump(writable, write_file)
        write_file.close()

    # Unsupported format
    else:
        raise ValueError("Unsupported format: {}".format(formatting))


def detect_formatting(path):
    """Detect the formatting using filename extension"""
    path = fspath(path)
    if ".json" in path:
        return "json"
    if ".pkl" in path:
        return "pkl"
    raise ValueError("Cannot detect the format of {}".format(path))


encoding_to_module = {"gzip": "gzip", "bzip2": "bz2", "xz": "lzma"}


def get_opener(filename):
    """
    Automatically detect compression and return the file opening function.
    """
    type_, encoding = mimetypes.guess_type(filename)
    if encoding is None:
        opener = io.open
    else:
        module = encoding_to_module[encoding]
        opener = importlib.import_module(module).open
    return opener


def metagraph_from_writable(writable):
    """Create a metagraph from a writable"""
    metaedge_tuples = [tuple(x) for x in writable["metaedge_tuples"]]
    kind_to_abbrev = writable.get("kind_to_abbrev")
    metagraph = MetaGraph.from_edge_tuples(metaedge_tuples, kind_to_abbrev)
    return metagraph


def graph_from_writable(writable):
    """Create a graph from a writable"""
    metagraph = metagraph_from_writable(writable)
    graph = Graph(metagraph)

    nodes = writable["nodes"]
    for node in nodes:
        graph.add_node(**node)

    edges = writable["edges"]
    for edge in edges:
        for key in "source_id", "target_id":
            edge[key] = tuple(edge[key])
        graph.add_edge(**edge)

    return graph


def writable_from_metagraph(metagraph):
    """Create a writable from a metagraph"""
    metanode_kinds = [metanode.get_id() for metanode in metagraph.get_nodes()]
    metaedge_tuples = [
        edge.get_id() for edge in metagraph.get_edges(exclude_inverts=True)
    ]
    writable = collections.OrderedDict()
    writable["metanode_kinds"] = sorted(metanode_kinds)
    writable["metaedge_tuples"] = sorted(metaedge_tuples)
    writable["kind_to_abbrev"] = metagraph.kind_to_abbrev
    return writable


def writable_from_graph(graph, int_id=False, masked=True):
    """Create a writable from a graph"""

    writable = writable_from_metagraph(graph.metagraph)

    nodes = list()
    for i, node in enumerate(graph.node_dict.values()):
        if not masked and node.is_masked():
            continue
        node_as_dict = collections.OrderedDict()
        node_as_dict["kind"] = node.metanode.identifier
        node_as_dict["identifier"] = node.identifier
        node_as_dict["name"] = node.name
        node_as_dict["data"] = node.data
        if int_id:
            node_as_dict["int_id"] = i
            node.int_id = i
        nodes.append(node_as_dict)
    writable["nodes"] = nodes

    edges = list()
    for edge in graph.get_edges(exclude_inverts=True):
        if not masked and edge.is_masked():
            continue
        edge_id_keys = ("source_id", "target_id", "kind", "direction")
        edge_id = edge.get_id()
        edge_items = list(zip(edge_id_keys, edge_id))
        edge_as_dict = collections.OrderedDict(edge_items)
        edge_as_dict["data"] = edge.data
        if int_id:
            edge_as_dict["source_int"] = edge.source.int_id
            edge_as_dict["target_int"] = edge.target.int_id
        edges.append(edge_as_dict)
    writable["edges"] = edges

    return writable


class Encoder(json.JSONEncoder):
    """
    A JSONEncoder that supports numpy types by converting them
    to standard python types.
    """

    def default(self, o):
        if type(o).__module__ == "numpy":
            return o.item()
        return json.JSONEncoder.default(self, o)


def write_nodetable(graph, path):
    """Write a tabular encoding of the graph nodes."""
    rows = list()
    for node in graph.node_dict.values():
        row = collections.OrderedDict()
        row["kind"] = node.metanode.identifier
        row["id"] = str(node)
        row["name"] = node.name
        rows.append(row)
    rows.sort(key=operator.itemgetter("kind", "id"))
    fieldnames = ["id", "name", "kind"]
    write_file = open_write_file(path)
    writer = csv.DictWriter(write_file, fieldnames=fieldnames, delimiter="\t")
    writer.writeheader()
    writer.writerows(rows)
    write_file.close()


def write_sif(graph, path, max_edges=None, seed=0):
    """Write a sif encoding of the graph edges."""
    if max_edges is not None:
        assert isinstance(max_edges, int)
    sif_file = open_write_file(path)
    writer = csv.writer(sif_file, delimiter="\t")
    writer.writerow(["source", "metaedge", "target"])
    metaedge_to_edges = graph.get_metaedge_to_edges(exclude_inverts=True)
    random.seed(seed)
    for metaedge, edges in metaedge_to_edges.items():
        if max_edges is not None and len(edges) > max_edges:
            edges = random.sample(edges, k=max_edges)
        for edge in edges:
            row = edge.source, edge.metaedge.abbrev, edge.target
            writer.writerow(row)
    sif_file.close()
