import collections
import pickle
import gzip
import json
import os
import io
import re
import operator
import csv
import random
import requests

from hetio.hetnet import Graph, MetaGraph

class Encoder(json.JSONEncoder):

    def default(self, o):
        if type(o).__module__ == 'numpy':
            return o.item()
        return json.JSONEncoder.default(self, o)

def open_path(path):
    """
    Return a text mode file object from the path.
    Automatically detects and supports urls and gzip compression.
    """
    is_gzipped = path.endswith('.gz')

    # url
    if re.match('^https?://', path):
        response = requests.get(path)
        if is_gzipped:
            b = io.BytesIO(response.content)
            return gzip.open(b, 'rt')
        return io.StringIO(response.text)

    # not url
    if is_gzipped:
        return gzip.open(path, 'rt')
    return open(path, 'r')

def open_ext(path, *args, **kwargs):
    """
    Return a file object. Automically detects gzip extension.
    """
    open_fxn = gzip.open if path.endswith('.gz') else open
    return open_fxn(path, *args, **kwargs)

def load(read_file, formatting):
    """Return a writable from a read_file"""

    # JSON formatted
    if formatting == 'json':
        return json.load(read_file)

    # YAML formatted
    if formatting == 'yaml':
        import yaml
        try:
            loader = yaml.CSafeLoader
        except AttributeError:
            loader = yaml.SafeLoader
        return yaml.load(read_file, Loader=loader)

    # pickle formatted
    if formatting == 'pkl':
        return pickle.load(read_file)

    # Unsupported format
    raise ValueError('Unsupported format: {}'.format(formatting))

def detect_formatting(path):
    """Detect the formatting using filename extension"""
    if '.json' in path:
        return 'json'
    if '.yaml' in path:
        return 'yaml'
    if '.pkl' in path:
        return 'pkl'
    raise ValueError('Cannot detect the format of {}'.format(path))

def extract_writable(path, formatting=None):
    """Extract a writable from the file specified by path"""
    if formatting is None:
        formatting = detect_formatting(path)
    read_file = open_path(path)
    writable = load(read_file, formatting)
    read_file.close()
    return writable

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
    writable = writable_from_graph(graph, ordered=True, masked=masked)
    dump(writable, path, formatting)

def write_metagraph(metagraph, path, formatting=None):
    """Write a graph to the specified path."""
    writable = writable_from_metagraph(metagraph, ordered=True)
    dump(writable, path, formatting)

def dump(writable, path, formatting=None):
    """Dump a writable to a path"""
    if formatting is None:
        formatting = detect_formatting(path)

    # JSON formatted
    if formatting == 'json':
        write_file = open_ext(path, 'wt')
        json.dump(writable, write_file, indent=2, cls=Encoder)
        write_file.close()

    # YAML formatted
    if formatting == 'yaml':
        import yaml
        try:
            dumper = yaml.CSafeDumper
        except AttributeError:
            dumper = yaml.SafeDumper
        write_file = open_ext(path, 'wt')
        yaml.dump(writable, write_file, Dumper=dumper)
        write_file.close()

    # pickle formatted
    if formatting == 'pkl':
        write_file = open_ext(path, 'wb')
        pickle.dump(writable, write_file)
        write_file.close()

    # Unsupported format
    raise ValueError('Unsupported format: {}'.format(formatting))

def metagraph_from_writable(writable):
    """Create a metagraph from a writable"""
    metaedge_tuples = [tuple(x) for x in writable['metaedge_tuples']]
    kind_to_abbrev = writable.get('kind_to_abbrev')
    metagraph = MetaGraph.from_edge_tuples(metaedge_tuples, kind_to_abbrev)
    return metagraph

def graph_from_writable(writable):
    """Create a graph from a writable"""
    metagraph = metagraph_from_writable(writable)
    graph = Graph(metagraph)

    nodes = writable['nodes']
    for node in nodes:
        graph.add_node(**node)

    edges = writable['edges']
    for edge in edges:
        for key in 'source_id', 'target_id':
            edge[key] = tuple(edge[key])
        graph.add_edge(**edge)

    return graph

def write_gml(graph, path):
    """ """
    writable = writable_from_graph(graph, int_id=True)

    re_pattern = re.compile(r"[^0-9a-zA-Z ]+")
    gml_nodes = list()
    for node in writable['nodes']:
        gml_node = collections.OrderedDict()
        gml_node['id'] = node['int_id']
        gml_node['label'] = node['id_']
        gml_node['kind'] = node['kind']
        name = node['data'].get('name', '')
        name = re.sub(re_pattern, '_', name)
        gml_node['name'] = name
        gml_nodes.append(gml_node)

    gml_edges = list()
    for edge in writable['edges']:
        gml_edge = collections.OrderedDict()
        gml_edge['source'] = edge['source_int']
        gml_edge['target'] = edge['target_int']
        gml_edge['kind'] = edge['kind']
        gml_edge['direction'] = edge['direction']
        gml_edges.append(gml_edge)

    with open(path, 'w') as write_file:
        gml_writer = GMLWriter(write_file)
        gml_writer.write_graph(gml_nodes, gml_edges)

def write_sif(graph, path, max_edges=None, seed=0):
    if max_edges is not None:
        assert isinstance(max_edges, int)
    sif_file = gzip.open(path, 'wt') if path.endswith('.gz') else open(path, 'w')
    writer = csv.writer(sif_file, delimiter='\t')
    writer.writerow(['source', 'metaedge', 'target'])
    metaedge_to_edges = graph.get_metaedge_to_edges(exclude_inverts=True)
    random.seed(seed)
    for metaedge, edges in metaedge_to_edges.items():
        if max_edges is not None and len(edges) > max_edges:
            edges = random.sample(edges, k=max_edges)
        for edge in edges:
            row = edge.source, edge.metaedge.get_abbrev(), edge.target
            writer.writerow(row)
    sif_file.close()

def write_nodetable(graph, path):
    rows = list()
    for node in graph.node_dict.values():
        row = collections.OrderedDict()
        row['kind'] = node.metanode.identifier
        row['id'] = str(node)
        row['name'] = node.name
        rows.append(row)
    rows.sort(key=operator.itemgetter('kind', 'id'))
    fieldnames = ['id', 'name', 'kind']
    write_file = open(path, 'w')
    writer = csv.DictWriter(write_file, fieldnames=fieldnames, delimiter='\t')
    writer.writeheader()
    writer.writerows(rows)
    write_file.close()

def writable_from_metagraph(metagraph, ordered=True):
    """Create a writable from a metagraph"""
    metanode_kinds = [metanode.get_id() for metanode in metagraph.get_nodes()]
    metaedge_tuples = [edge.get_id() for edge in
                       metagraph.get_edges(exclude_inverts=True)]
    writable = collections.OrderedDict() if ordered else dict()
    writable['metanode_kinds'] = metanode_kinds
    writable['metaedge_tuples'] = metaedge_tuples
    writable['kind_to_abbrev'] = metagraph.kind_to_abbrev
    return writable

def writable_from_graph(graph, ordered=True, int_id=False, masked=True):
    """Create a writable from a graph"""

    writable = writable_from_metagraph(graph.metagraph, ordered)

    nodes = list()
    for i, node in enumerate(graph.node_dict.values()):
        if not masked and node.is_masked():
            continue
        node_as_dict = collections.OrderedDict() if ordered else dict()
        node_as_dict['kind'] = node.metanode.identifier
        node_as_dict['identifier'] = node.identifier
        node_as_dict['name'] = node.name
        node_as_dict['data'] = node.data
        if int_id:
            node_as_dict['int_id'] = i
            node.int_id = i
        nodes.append(node_as_dict)
    writable['nodes'] = nodes

    edges = list()
    for edge in graph.get_edges(exclude_inverts=True):
        if not masked and edge.is_masked():
            continue
        edge_id_keys = ('source_id', 'target_id', 'kind', 'direction')
        edge_id = edge.get_id()
        edge_items = list(zip(edge_id_keys, edge_id))
        edge_as_dict = collections.OrderedDict(edge_items) if ordered else dict(edge_items)
        edge_as_dict['data'] = edge.data
        if int_id:
            edge_as_dict['source_int'] = edge.source.int_id
            edge_as_dict['target_int'] = edge.target.int_id
        edges.append(edge_as_dict)
    writable['edges'] = edges

    return writable


class GMLWriter(object):
    """
    http://www.fim.uni-passau.de/fileadmin/files/lehrstuhl/brandenburg/projekte/gml/gml-technical-report.pdf
    """

    def __init__(self, write_file):
        """GML writing and reading class"""
        self.gml_file = write_file  # file to write GML to
        self.write_indent = '\t'
        self.write_level = 0  # indentation level while writing

    def write_graph(self, nodes, edges):
        """nodes and edges are lists of dictionaries."""

        with GMLBlock(self, 'graph'):

            for node in nodes:
                with GMLBlock(self, 'node'):
                    self.write_properties(node)

            for edge in edges:
                with GMLBlock(self, 'edge'):
                    self.write_properties(edge)


    def write(self, s):
        """Write string s to self.gml_file prepending the proper indentation."""
        indent = self.write_indent * self.write_level
        self.gml_file.write(indent + s)

    def write_properties(self, dictionary):
        for key, value in list(dictionary.items()):
            self.write_property(key, value)

    def write_property(self, key, value, printing=False):
        """ """
        if not re.match(r'[A-Za-z]\w*\Z', key):
            if printing: print('Invalid Key:', key)
            return
        if isinstance(value, (int, float)):
            value = str(value)

        elif isinstance(value, str):
            #value = value.replace('"', "'")
            #value = value.replace('&', "AMPERSAND")
            if re.search(r'[&"\\]', value):
                if printing: print('Invalid Value:', value)
                return
            value = '"{}"'.format(value)

        elif isinstance(value, (list, tuple, set)):
            with GMLBlock(self, key):
                for elem in value:
                    self.write_property('list', elem)
            return

        elif isinstance(value, dict):
            with GMLBlock(self, key):
                self.write_properties(value)
            return

        else:
            print('GML formating not specified for', type(value))
            return
        line = '{} {}\n'.format(key, value)
        if len(line) > 254:
            if printing: print('Line too long:', line)
            return
        self.write(line)

class GMLBlock(object):

    def __init__(self, gml, key):
        self.gml = gml
        self.key = key

    def __enter__(self):
        self.gml.write('%s [\n' % self.key)
        self.gml.write_level += 1

    def __exit__(self, *args, **kwargs):
        self.gml.write_level -= 1
        self.gml.write(']\n')
