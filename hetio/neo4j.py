import textwrap
import re

import py2neo
import py2neo.packages.httpstream
import pandas

import hetio.hetnet

# Avoid SocketError
py2neo.packages.httpstream.http.socket_timeout = 1e8

def export_neo4j(graph, uri, node_queue=100, edge_queue=100):
    """Export hetnet to neo4j"""
    db_graph = py2neo.Graph(uri)

    # Delete all existing nodes
    db_graph.delete_all()

    # Create uniqueness constrains and indexes
    for metanode in graph.metagraph.get_nodes():
        label = as_label(metanode)
        if 'identifier' not in db_graph.schema.get_uniqueness_constraints(label):
            db_graph.schema.create_uniqueness_constraint(label, 'identifier')
        if 'name' not in db_graph.schema.get_indexes(label):
            db_graph.schema.create_index(label, 'name')

    # Create nodes
    creator = Creator(db_graph, node_queue)
    for node in graph.get_nodes():
        label = as_label(node.metanode)
        data = sanitize_data(node.data)
        neo_node = py2neo.Node(label, identifier=node.identifier, name=node.name, **data)
        creator.append(neo_node)
    creator.create()

    # Create edges
    creator = Creator(db_graph, edge_queue)
    for edge in graph.get_edges(exclude_inverts=True):
        metaedge = edge.metaedge
        rel_type = as_type(metaedge)
        source_label = as_label(metaedge.source)
        target_label = as_label(metaedge.target)
        source = db_graph.find_one(source_label, 'identifier', edge.source.identifier)
        target = db_graph.find_one(target_label, 'identifier', edge.target.identifier)
        data = sanitize_data(edge.data)
        neo_rel = py2neo.Relationship(source, rel_type, target, **data)
        creator.append(neo_rel)
    creator.create()

    return db_graph


class Creator(list):
    """Batch creation of py2neo objects"""

    def __init__(self, db_graph, max_queue_size=25):
        super().__init__()
        self.db_graph = db_graph
        self.max_queue_size = max_queue_size
        self.n_created = 0

    def append(self, x):
        super().append(x)
        if len(self) >= self.max_queue_size:
            self.create()

    def create(self):
        if not self:
            return
        self.db_graph.create(*self)
        self.n_created += len(self)
        #print('{} nodes created\r'.format(self.n_created), end='')
        del self[:]


def as_label(metanode):
    """Convert metanode to a label-formatted str"""
    label = str(metanode)
    label = label.title()
    label = label.replace(' ', '')
    return label

def as_type(metaedge):
    """Convert metaedge to a rel_type-formatted str"""
    if isinstance(metaedge, str):
        rel_type = metaedge
    if isinstance(metaedge, hetio.hetnet.MetaEdge):
        rel_type = str(metaedge.kind)
    rel_type = rel_type.upper()
    rel_type = rel_type.replace(' ', '_')
    return rel_type

def sanitize_data(data):
    """Create neo4j safe properties"""
    sanitized = dict()
    for k, v in data.items():
        if isinstance(v, list):
            sanitized[k] = v
            continue
        if pandas.isnull(v):
            continue
        if v is None:
            continue
        sanitized[k] = v
    return sanitized

def metapath_to_metarels(metapath):
    return tuple(metaedge_to_metarel(metaedge) for metaedge in metapath)

def metaedge_to_metarel(metaedge):
    source, target, kind, direction = metaedge.get_id()
    rel_type = '{}_{}'.format(as_type(kind), re.sub('[<>]', '', metaedge.get_abbrev()))
    return as_label(source), as_label(target), rel_type, direction

def cypher_path(metarels):
    """
    Format a metapath for cypher.
    """
    # Convert metapath to metarels
    if isinstance(metarels, hetio.hetnet.MetaPath):
        metarels = metapath_to_metarels(metarels)

    # Create cypher query
    q = '(n0:{})'.format(metarels[0][0])
    for i, (source_label, target_label, rel_type, direction) in enumerate(metarels):
        kwargs = {
            'i': i + 1,
            'rel_type': rel_type,
            'target_label': ':{}'.format(target_label) if i + 1 == len(metarels) else '',
            'dir0': '<-' if direction == 'backward' else '-',
            'dir1': '->' if direction == 'forward' else '-',
        }
        q += '{dir0}[:{rel_type}]{dir1}(n{i}{target_label})'.format(**kwargs)
    return q

def construct_dwpc_query(metarels, property='name'):
    """
    Create a cypher query for computing the DWPC for a type of path.
    """
    # Convert metapath to metarels
    if isinstance(metarels, hetio.hetnet.MetaPath):
        metarels = metapath_to_metarels(metarels)

    # create cypher path query
    metapath_query = cypher_path(metarels)

    # create cypher path degree query
    degree_strs = list()
    for i, (source_label, target_label, rel_type, direction) in enumerate(metarels):
        kwargs = {
            'i0': i,
            'i1': i + 1,
            'source_label': source_label,
            'target_label': target_label,
            'rel_type': rel_type,
            'dir0': '<-' if direction == 'backward' else '-',
            'dir1': '->' if direction == 'forward' else '-',
        }
        degree_strs.append(textwrap.dedent(
            '''\
            size((n{i0}){dir0}[:{rel_type}]{dir1}()),
            size((){dir0}[:{rel_type}]{dir1}(n{i1}))'''
            ).format(**kwargs))
    degree_query = ',\n'.join(degree_strs)

    # combine cypher fragments into a single query and add DWPC logic
    query = textwrap.dedent('''\
        MATCH paths = {metapath_query}
        WHERE n0.{property} = {{ source }}
        AND n{length}.{property} = {{ target }}
        WITH
        [
        {degree_query}
        ] AS degrees, paths
        RETURN
        COUNT(paths) AS PC,
        sum(reduce(pdp = 1.0, d in degrees| pdp * d ^ -{{ w }})) AS DWPC\
        ''').format(
        degree_query = degree_query,
        metapath_query = metapath_query,
        length=len(metarels),
        property=property)

    return query
