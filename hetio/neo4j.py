import py2neo
import py2neo.packages.httpstream
import pandas

# Avoid SocketError
py2neo.packages.httpstream.http.socket_timeout = 9999

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
