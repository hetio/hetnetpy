import abc
import functools
import re

import hetnetpy.abbreviation

direction_to_inverse = {"forward": "backward", "backward": "forward", "both": "both"}

direction_to_abbrev = {"forward": ">", "backward": "<", "both": "-"}

direction_to_unicode_abbrev = {"forward": "→", "backward": "←", "both": "–"}


class ElemMask(object):
    def __init__(self):
        self.masked = False

    def is_masked(self):
        return self.masked

    def mask(self):
        self.masked = True

    def unmask(self):
        self.masked = False


class IterMask(object):
    def is_masked(self):
        return any(elem.is_masked() for elem in self.mask_elem_iter())


class BaseGraph(object):
    def __init__(self):
        self.node_dict = dict()
        self.edge_dict = dict()
        self.path_dict = dict()
        self.n_nodes = 0  # Number of nodes
        self.n_edges = 0  # Number of edges excluding inverts
        self.n_inverts = 0  # Number of inverted edges

    def get_node(self, kind):
        return self.node_dict[kind]

    def get_edge(self, edge_tuple):
        return self.edge_dict[edge_tuple]

    def get_nodes(self):
        return iter(self.node_dict.values())

    def get_edges(self, exclude_inverts=True):
        for edge in self.edge_dict.values():
            if exclude_inverts and edge.inverted:
                continue
            yield edge

    def __iter__(self):
        return iter(self.node_dict.values())

    def __contains__(self, item):
        return item in self.node_dict

    def __eq__(self, other):
        return (
            type(other) is type(self)
            and self.node_dict == other.node_dict
            and self.edge_dict == other.edge_dict
        )


class BaseNode(ElemMask):
    def __init__(self, identifier):
        ElemMask.__init__(self)
        self.identifier = identifier

    @abc.abstractmethod
    def get_id(self):
        pass

    def __hash__(self):
        try:
            return self.hash_
        except AttributeError:
            return hash(self.get_id())

    def __lt__(self, other):
        return self.get_id() < other.get_id()

    def __eq__(self, other):
        return type(other) is type(self) and self.get_id() == other.get_id()


class BaseEdge(ElemMask):
    def __init__(self, source, target):
        ElemMask.__init__(self)
        self.source = source
        self.target = target

    def __hash__(self):
        try:
            return self.hash_
        except AttributeError:
            return hash(self.get_id())

    def __eq__(self, other):
        return type(other) is type(self) and self.get_id() == other.get_id()

    def __lt__(self, other):
        return self.get_id() < other.get_id()

    def __str__(self):
        source, target, kind, direction = self.get_id()
        dir_abbrev = direction_to_abbrev[direction]
        return "{0} {3} {2} {3} {1}".format(source, target, kind, dir_abbrev)

    def get_unicode_str(self):
        """
        Returns a pretty str representation of an edge or metaedge.
        """
        source, target, kind, direction = self.get_id()
        dir_abbrev = direction_to_unicode_abbrev[direction]
        return "{0}{3}{2}{3}{1}".format(source, target, kind, dir_abbrev)


class BasePath(IterMask):
    def __init__(self, edges):
        assert isinstance(edges, tuple)
        self.edges = edges

    def source(self):
        return self[0].source

    def target(self):
        return self[-1].target

    def get_nodes(self):
        nodes = tuple(edge.source for edge in self)
        nodes = nodes + (self.target(),)
        return nodes

    def inverse_edges(self):
        return tuple(reversed(list(edge.inverse for edge in self)))

    def is_symmetric(self):
        """Return a bool for whether this path is symmetric."""
        return self.edges == self.inverse_edges()

    def mask_elem_iter(self):
        for edge in self:
            yield edge
            yield edge.source
        yield self.target()

    def max_overlap(self, others):
        for other in others:
            len_other = len(other)
            if len_other > len(self):
                continue
            if self[:len_other] == other:
                return other
        return None

    def get_unicode_str(self):
        """
        Returns a pretty, unicode, human-readable, and verbose str for a path
        or metapath.
        """
        s = ""
        for edge in self:
            *temp, kind, direction = edge.get_id()
            source = (
                edge.source.name if hasattr(edge, "name") else edge.source.identifier
            )
            dir_abbrev = direction_to_unicode_abbrev[direction]
            s += "{0}{2}{1}{2}".format(source, kind, dir_abbrev)
        target = edge.target.name if hasattr(edge, "name") else edge.target.identifier
        s += target
        return s

    def __iter__(self):
        return iter(self.edges)

    def __getitem__(self, key):
        return self.edges[key]

    def __len__(self):
        return len(self.edges)

    def __hash__(self):
        return hash(self.edges)

    def __eq__(self, other):
        return (type(other) is type(self)) and (self.edges == other.edges)

    def __lt__(self, other):
        if len(self) == len(other):
            return self.edges < other.edges
        return len(self) < len(other)


class MetaGraph(BaseGraph):
    def __init__(self):
        BaseGraph.__init__(self)

    def get_metanode(self, metanode):
        """
        Return the metanode specified by the input, which can be either a:
         - MetaNode (passthrough)
         - metanode kind (str)
         - metanode abbreviation (str)
         - neo4j-style node label
        """
        if isinstance(metanode, MetaNode):
            return metanode
        if metanode in self.node_dict:
            return self.get_node(metanode)
        if not isinstance(metanode, str):
            raise ValueError(
                "Cannot interpret object of type {}".format(type(metanode).__name__)
            )
        if metanode in self.abbrev_to_kind:
            return self.get_node(self.abbrev_to_kind[metanode])
        if metanode in self.neo4j_to_metanode:
            return self.neo4j_to_metanode[metanode]
        raise ValueError("metanode not found")

    def get_metaedge(self, metaedge):
        """
        Return the metaedge specified by the input, which can be either a:
         - MetaEdge (passthrough)
         - metaedge_id (tuple)
         - neo4j-style relationship type
         - metaedge abbreviation
        """
        if isinstance(metaedge, MetaEdge):
            return metaedge
        if isinstance(metaedge, tuple):
            return self.get_edge(metaedge)
        if not isinstance(metaedge, str):
            raise ValueError(
                "Cannot interpret object of type {}".format(type(metaedge).__name__)
            )
        if metaedge in self.neo4j_to_metaedge:
            return self.neo4j_to_metaedge[metaedge]
        metaedge_id = hetnetpy.abbreviation.metaedge_id_from_abbreviation(
            self, metaedge
        )
        return self.get_edge(metaedge_id)

    def get_metapath(self, metapath):
        """
        Return the metapath specified by the input, which can be either a:
         - MetaPath object (passthrough)
         - tuple of edges
         - metapath abbreviation
        """
        if isinstance(metapath, MetaPath):
            return metapath
        if isinstance(metapath, tuple):
            return self.get_metapath_from_edges(metapath)
        if isinstance(metapath, str):
            return self.metapath_from_abbrev(metapath)

    @property
    def neo4j_to_metanode(self):
        if not hasattr(self, "_neo4j_to_metanode"):
            self._neo4j_to_metanode = {
                metanode.neo4j_label: metanode for metanode in self.get_nodes()
            }
        return self._neo4j_to_metanode

    @property
    def neo4j_to_metaedge(self):
        if not hasattr(self, "_neo4j_to_metaedge"):
            self._neo4j_to_metaedge = {
                metaedge.neo4j_rel_type: metaedge for metaedge in self.get_edges()
            }
        return self._neo4j_to_metaedge

    @staticmethod
    def from_edge_tuples(metaedge_tuples, kind_to_abbrev=None):
        """Create a new metagraph defined by its edges."""
        metagraph = MetaGraph()
        node_kinds = set()
        for source_kind, target_kind, kind, direction in metaedge_tuples:
            node_kinds.add(source_kind)
            node_kinds.add(target_kind)
        for kind in node_kinds:
            metagraph.add_node(kind)
        for edge_tuple in metaedge_tuples:
            metagraph.add_edge(edge_tuple)

        if kind_to_abbrev is None:
            kind_to_abbrev = hetnetpy.abbreviation.create_abbreviations(metagraph)
        metagraph.set_abbreviations(kind_to_abbrev)

        assert hetnetpy.abbreviation.validate_abbreviations(metagraph)

        return metagraph

    def set_abbreviations(self, kind_to_abbrev):
        """Add abbreviations as an attribute for metanodes and metaedges"""
        self.kind_to_abbrev = kind_to_abbrev
        self.abbrev_to_kind = {v: k for k, v in kind_to_abbrev.items()}
        for kind, metanode in self.node_dict.items():
            metanode.abbrev = kind_to_abbrev[kind]
        for metaedge in self.edge_dict.values():
            abbrev = kind_to_abbrev[metaedge.kind]
            if metaedge.direction == "forward":
                abbrev = "{}>".format(abbrev)
            if metaedge.direction == "backward":
                abbrev = "<{}".format(abbrev)
            metaedge.kind_abbrev = abbrev

    def add_node(self, kind):
        metanode = MetaNode(kind)
        self.node_dict[kind] = metanode
        self.n_nodes += 1

    def add_edge(self, edge_id):
        """source_kind, target_kind, kind, direction"""
        assert edge_id not in self.edge_dict
        source_kind, target_kind, kind, direction = edge_id
        source = self.get_node(source_kind)
        target = self.get_node(target_kind)

        metaedge = MetaEdge(source, target, kind, direction)
        self.edge_dict[edge_id] = metaedge
        source.edges.add(metaedge)
        metaedge.inverted = False
        self.n_edges += 1

        if source == target and direction == "both":
            metaedge.inverse = metaedge
        else:
            inverse_direction = direction_to_inverse[direction]
            inverse_id = target_kind, source_kind, kind, inverse_direction
            assert inverse_id not in self.edge_dict

            inverse = MetaEdge(target, source, kind, inverse_direction)
            self.edge_dict[inverse_id] = inverse
            target.edges.add(inverse)
            metaedge.inverse = inverse
            inverse.inverse = metaedge
            inverse.inverted = True
            self.n_inverts += 1

    def extract_metapaths(self, source, target=None, max_length=4):
        """
        Extact all metapaths from the source metanode to the target metanode up
        to length max_length. These metapaths are equivalent to all walks on
        the metagraph from source to target. If target is None (default), then
        metapaths to any target node are returned.
        """
        source = self.get_metanode(source)
        if target:
            target = self.get_metanode(target)

        assert max_length >= 0
        if max_length == 0:
            return []

        metapaths = [self.get_metapath_from_edges((edge,)) for edge in source.edges]
        previous_metapaths = list(metapaths)
        for depth in range(1, max_length):
            current_metapaths = list()
            for metapath in previous_metapaths:
                for add_edge in metapath.target().edges:
                    new_metapath = self.get_metapath_from_edges(
                        metapath.edges + (add_edge,)
                    )
                    current_metapaths.append(new_metapath)
            metapaths.extend(current_metapaths)
            previous_metapaths = current_metapaths

        if target:
            metapaths = [
                metapath for metapath in metapaths if metapath.target() == target
            ]
        return sorted(metapaths)

    def extract_all_metapaths(self, max_length, exclude_inverts=False):
        """
        Extract all possible metapaths up to max_length by walking the
        metagraph. Unlike extract_metapaths, this function is does not limit
        to a specific source metanode. Unlike metaedges/edges, metapaths do not
        have standard orientations. However, it is possible for a metapath to
        be an inverse of another metapath, e.g. CbGaD and DaGbC.

        Set exclude_inverts=True to return only one orientation of two inverse
        metapaths. This may be useful if metapaths are being used to compute
        symmetric metrics, such as path count or DWPC. In this case, you may
        want to optimize by computing values for only one metapath orientation.
        """
        metapaths = set()
        metanodes = self.get_nodes()
        for source in metanodes:
            from_source = self.extract_metapaths(source, max_length=max_length)
            for metapath in from_source:
                if exclude_inverts:
                    metapath, _ = sorted([metapath, metapath.inverse])
                metapaths.add(metapath)
        return sorted(metapaths)

    def get_metapath_from_edges(self, edges):
        """Store exactly one of each metapath."""
        assert isinstance(edges, tuple)
        if len(edges) == 0:
            return None
        try:
            return self.path_dict[edges]
        except KeyError:
            metapath = MetaPath(edges)
            self.path_dict[edges] = metapath

            inverse_edges = metapath.inverse_edges()
            if metapath.is_symmetric():
                inverse = metapath
            else:
                inverse = MetaPath(inverse_edges)
                self.path_dict[inverse_edges] = inverse
                inverse.inverse = metapath
            metapath.inverse = inverse

            # Create metapaths for metapath segments in this metapath
            sub_edges = edges[1:]
            metapath.sub = self.get_metapath_from_edges(sub_edges)
            inverse.sub = self.get_metapath_from_edges(inverse_edges[1:])

            return metapath

    def metapath_from_abbrev(self, abbrev):
        """Retrieve a metapath from its abbreviation"""
        metaedges = list()
        metaedge_abbrevs = hetnetpy.abbreviation.metaedges_from_metapath(abbrev)
        for metaedge_abbrev in metaedge_abbrevs:
            metaedge_id = hetnetpy.abbreviation.metaedge_id_from_abbreviation(
                self, metaedge_abbrev
            )
            metaedges.append(self.get_edge(metaedge_id))
        return self.get_metapath_from_edges(tuple(metaedges))


class MetaNode(BaseNode):
    def __init__(self, identifier):
        BaseNode.__init__(self, identifier)
        self.edges = set()
        self.hash_ = hash(self)

    def get_id(self):
        return self.identifier

    @property
    @functools.lru_cache()
    def neo4j_label(self):
        """
        Convert metanode to neo4j nomenclature, i.e. a label-formatted str.
        """
        label = str(self)
        label = label.title()
        label = label.replace(" ", "")
        return label

    def __str__(self):
        return str(self.identifier)


class MetaEdge(BaseEdge):
    def __init__(self, source, target, kind, direction):
        """source and target are MetaNodes."""
        BaseEdge.__init__(self, source, target)
        self.kind = kind
        self.direction = direction
        self.hash_ = hash(self)

    def get_id(self):
        """
        Get the metaedge_id as a tuple like:
        (source_id, target_id, kind, direction)
        """
        metaedge_id = (
            self.source.identifier,
            self.target.identifier,
            self.kind,
            self.direction,
        )
        return metaedge_id

    @property
    def abbrev(self):
        """
        Return this metaedge's abbreviation.
        """
        return self.source.abbrev + self.kind_abbrev + self.target.abbrev

    def get_abbrev(self):
        """
        Getter function for a metaedge's abbreviation, kept for backwards
        compatability. Recommended API is to use metaedge.abbrev.
        """
        return self.abbrev

    def get_standard_abbrev(self):
        """
        Return the standard abbreviation, the abbrevation of the non-inverted
        metaedge with inequality symbols removed. Inequality symbols indicate
        the directionality of directed metaedges and can be removed safely
        here.
        """
        metaedge = self.inverse if self.inverted else self
        return re.sub("[<>]", "", metaedge.abbrev)

    def filesystem_str(self):
        s = "{0}{2}{1}-{3}".format(
            self.source.abbrev, self.target.abbrev, self.kind_abbrev, self.direction
        )
        return s.translate(None, "><")

    @property
    @functools.lru_cache()
    def neo4j_rel_type(self):
        """Convert metaedge to a rel_type-formatted str"""
        rel_type = str(self.kind)
        rel_type = rel_type.upper()
        rel_type = rel_type.replace(" ", "_")
        abbrev = self.get_standard_abbrev()
        return "{}_{}".format(rel_type, abbrev)


class MetaPath(BasePath):
    def __init__(self, edges):
        """metaedges is a tuple of edges"""
        assert all(isinstance(edge, MetaEdge) for edge in edges)
        BasePath.__init__(self, edges)

    def __repr__(self):
        return self.abbrev

    @property
    def abbrev(self):
        s = "".join(edge.source.abbrev + edge.kind_abbrev for edge in self)
        s += self.target().abbrev
        return s


class Graph(BaseGraph):
    def __init__(self, metagraph, data=dict()):
        """
        Create a graph.

        Parameters
        ----------
        metagraph : hetnetpy.hetnet.MetaGraph
            metagraph with the potential types of nodes and relationships
        """
        BaseGraph.__init__(self)
        self.metagraph = metagraph
        self.data = data

    def add_node(self, kind, identifier, name=None, data={}):
        """
        Add a node to the graph.

        Parameters
        ----------
        metagraph : hetnetpy.hetnet.MetaGraph
            metagraph with the potential types of nodes and relationships
        kind : str
            metanode kind
        identifier : str or int
            node identifier
        name : str
            node name. defaults to identifier
        data : dict
            node properties / attributes
        """
        if name is None:
            name = identifier
        metanode = self.metagraph.node_dict[kind]
        node = Node(metanode, identifier, name, data)
        node_id = node.get_id()
        assert node_id not in self, "node already exists"
        self.node_dict[node_id] = node
        self.n_nodes += 1
        return node

    def add_edge(self, source_id, target_id, kind, direction, data=dict()):
        """
        Add an edge to the graph. Edge cannot already exist.

        Parameters
        ----------
        source_id : hetnetpy.hetnet.Node or tuple of (metanode, node) identifiers
            the source node for the edge
        target_id : hetnetpy.hetnet.Node or tuple of (metanode, node) identifiers
            the target node for the edge
        kind : str
            the metaedge kind
        direction : str
            the metaedge direction
        data : dict
            edge attributes / properties

        Returns
        -------
        edge, edge.inverse : tuple of edges
            the created edge and its inverse
        """
        source = source_id
        if not isinstance(source, Node):
            source = self.node_dict[source]
        source_id = source.get_id()

        target = target_id
        if not isinstance(target, Node):
            target = self.node_dict[target]
        target_id = target.get_id()

        metaedge_id = (
            source.metanode.get_id(),
            target.metanode.get_id(),
            kind,
            direction,
        )
        metaedge = self.metagraph.edge_dict[metaedge_id]

        # Check that edges do not already exist
        edge_id = source_id, target_id, kind, metaedge.direction
        inverse_id = target_id, source_id, kind, metaedge.inverse.direction
        assert edge_id not in self.edge_dict, "edge already exists"
        assert inverse_id not in self.edge_dict, "inverse edge already exists"

        # Create edge
        edge = Edge(source, target, metaedge, data)
        self.edge_dict[edge.get_id()] = edge
        edge.inverted = metaedge.inverted
        self.n_edges += 1

        # Create inverse edge if not identical
        if edge_id == inverse_id:
            # Self loop of a bidirectional edge
            edge.inverse = edge
        else:
            inverse = Edge(target, source, metaedge.inverse, data)
            inverse_id = inverse.get_id()
            self.edge_dict[inverse_id] = inverse
            inverse.inverted = not edge.inverted
            edge.inverse = inverse
            inverse.inverse = edge
            self.n_inverts += 1

        return edge, edge.inverse

    def unmask(self):
        """Unmask all nodes and edges contained within the graph"""
        for dictionary in self.node_dict, self.edge_dict:
            for value in dictionary.values():
                value.masked = False

    def get_metanode_to_nodes(self):
        metanode_to_nodes = dict()
        for node in self.get_nodes():
            metanode = node.metanode
            metanode_to_nodes.setdefault(metanode, list()).append(node)
        return metanode_to_nodes

    def get_metaedge_to_edges(self, exclude_inverts=False):
        metaedges = self.metagraph.get_edges(exclude_inverts)
        metaedge_to_edges = {metaedge: list() for metaedge in metaedges}
        for edge in self.get_edges(exclude_inverts):
            metaedge_to_edges[edge.metaedge].append(edge)
        return metaedge_to_edges

    def count_nodes(self, metanode):
        """
        Count the number of nodes for the specified metanode.
        """
        metanode = self.metagraph.get_metanode(metanode)
        nodes = self.get_metanode_to_nodes()[metanode]
        return len(nodes)

    def get_subgraph(self, metanodes=None, metaedges=None, nodes=None):
        """
        Return a subgraph of the hetnet. By default, creates a copy of the
        hetnet. If both metanode and metaedge subsets are specified, then
        only the intersection (rather than the union) is preserved.

        Parameters
        ----------
        metanodes : None or set
            metanodes to keep.
        metaedges : None or set
            metaedges to keep. None keeps all metaedges, subject to the
            metanode subset.
        nodes : None or list
            nodes to keep. None keeps all nodes, subject to the metanode and
            metanode subsets.
        """
        if metanodes is None:
            metanodes = self.metagraph.get_nodes()
        metanodes = set(metanodes)
        if metaedges is None:
            metaedges = self.metagraph.get_edges()
        metaedges = set(metaedges)
        metaedges |= {metaedge.inverse for metaedge in metaedges}
        metaedges = {me for me in metaedges if not me.inverted}

        metaedge_tuples = list()
        for metaedge in self.metagraph.get_edges():
            if metaedge.source not in metanodes:
                continue
            if metaedge.target not in metanodes:
                continue
            if metaedge not in metaedges:
                continue
            metaedge_tuples.append(metaedge.get_id())
        metagraph = MetaGraph.from_edge_tuples(metaedge_tuples)
        kinds = set(metagraph.kind_to_abbrev)
        kind_to_abbrev = {
            k: v for k, v in self.metagraph.kind_to_abbrev.items() if k in kinds
        }
        metagraph.set_abbreviations(kind_to_abbrev)
        graph = Graph(metagraph, data=self.data)

        # Overwrite based on metagraph
        metanodes = set(metagraph.get_nodes())
        metaedges = set(metagraph.get_edges(exclude_inverts=True))

        # Create nodes and edges
        if nodes is None:
            nodes = [n for n in self.get_nodes() if n.metanode in metanodes]
        nodes = list(nodes)
        for node in nodes:
            graph.add_node(
                kind=node.metanode.get_id(),
                identifier=node.identifier,
                name=node.name,
                data=node.data.copy(),
            )
        for node in nodes:
            node = self.node_dict[node.get_id()]
            for metaedge in metaedges:
                if metaedge not in node.edges:
                    continue
                for edge in node.edges[metaedge]:
                    if edge.inverted:
                        continue
                    target_id = edge.target.get_id()
                    if target_id not in graph.node_dict:
                        continue
                    kind = metaedge.kind
                    direction = metaedge.direction
                    graph.add_edge(node, target_id, kind, direction)

        return graph


class Node(BaseNode):
    def __init__(self, metanode, identifier, name, data):
        """ """
        BaseNode.__init__(self, identifier)
        self.metanode = metanode
        self.name = name
        self.data = data
        self.edges = {metaedge: set() for metaedge in metanode.edges}

    def get_id(self):
        return self.metanode.identifier, self.identifier

    def get_edges(self, metaedge, exclude_masked=True):
        """
        Returns the set of edges incident to self of the specified metaedge.
        """
        if exclude_masked:
            edges = set()
            for edge in self.edges[metaedge]:
                if edge.masked or edge.target.masked:
                    continue
                edges.add(edge)
        else:
            edges = self.edges[metaedge]
        return edges

    def __repr__(self):
        node_as_dict = self.__dict__.copy()
        del node_as_dict["edges"]
        return "{!s}({!r})".format(self.__class__, node_as_dict)

    def _repr_pretty_(self, p, cycle):
        p.text(str(self))

    def __str__(self):
        return "{}::{}".format(*self.get_id())


class Edge(BaseEdge):
    def __init__(self, source, target, metaedge, data):
        """source and target are Node objects. metaedge is the MetaEdge object
        representing the edge
        """
        BaseEdge.__init__(self, source, target)
        self.metaedge = metaedge
        self.data = data
        self.source.edges[metaedge].add(self)

    def get_id(self):
        edge_id = (
            self.source.get_id(),
            self.target.get_id(),
            self.metaedge.kind,
            self.metaedge.direction,
        )
        return edge_id


class Path(BasePath):
    def __init__(self, edges):
        BasePath.__init__(self, edges)

    def __repr__(self):
        s = ""
        for edge in self:
            dir_abbrev = direction_to_abbrev[edge.metaedge.direction]
            s += "{0} {1} {2} {1} ".format(edge.source, dir_abbrev, edge.metaedge.kind)
        s = "{}{}".format(s, self.target())
        return s
