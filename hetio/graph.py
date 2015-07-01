# daniel.himmelstein@gmail.com
import abc
import itertools
import collections

direction_to_inverse = {'forward': 'backward',
                         'backward': 'forward',
                         'both': 'both'}

direction_to_abbrev = {'forward': '>', 'backward': '<', 'both': '-'}

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
        return self.get_id() == other.get_id()

    def __repr__(self):
        return self.get_id()

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

    def __repr__(self):
        source, target, kind, direction = self.get_id()
        dir_abbrev = direction_to_abbrev[direction]
        return '{0} {3} {2} {3} {1}'.format(source, target, kind, dir_abbrev)

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
        nodes = nodes + (self.target(), )
        return nodes

    def inverse_edges(self):
        return tuple(reversed(list(edge.inverse for edge in self)))

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

    def __iter__(self):
        return iter(self.edges)

    def __getitem__(self, key):
        return self.edges[key]

    def __len__(self):
        return len(self.edges)

    def __hash__(self):
        return hash(self.edges)

    def __eq__(self, other):
        return self.edges == other.edges

class MetaGraph(BaseGraph):

    def __init__(self):
        """ """
        BaseGraph.__init__(self)

    @staticmethod
    def from_edge_tuples(metaedge_tuples):
        metagraph = MetaGraph()
        node_kinds = set()
        for source_kind, target_kind, kind, direction in metaedge_tuples:
            node_kinds.add(source_kind)
            node_kinds.add(target_kind)
        for kind in node_kinds:
            metagraph.add_node(kind)
        for edge_tuple in metaedge_tuples:
            metagraph.add_edge(edge_tuple)

        metagraph.create_abbreviations()
        return metagraph

    @staticmethod
    def get_duplicates(iterable):
        """Return a set of the elements which appear multiple times in iterable."""
        seen, duplicates = set(), set()
        for elem in iterable:
            if elem in seen:
                duplicates.add(elem)
            else:
                seen.add(elem)
        return duplicates

    @staticmethod
    def find_abbrevs(kinds):
        """For a list of strings (kinds), find the shortest unique abbreviation."""
        kind_to_abbrev = {kind: kind[0] for kind in kinds}
        duplicates = MetaGraph.get_duplicates(list(kind_to_abbrev.values()))
        while duplicates:
            for kind, abbrev in list(kind_to_abbrev.items()):
                if abbrev in duplicates:
                    abbrev += kind[len(abbrev)]
                    kind_to_abbrev[kind] = abbrev
            duplicates = MetaGraph.get_duplicates(list(kind_to_abbrev.values()))
        return kind_to_abbrev

    def create_abbreviations(self):
        """Creates abbreviations for node and edge kinds."""
        kind_to_abbrev = MetaGraph.find_abbrevs(list(self.node_dict.keys()))
        kind_to_abbrev = {kind: abbrev.upper()
                          for kind, abbrev in list(kind_to_abbrev.items())}

        edge_set_to_keys = dict()
        for edge in list(self.edge_dict.keys()):
            key = frozenset(list(map(str.lower, edge[:2])))
            value = edge[2]
            edge_set_to_keys.setdefault(key, list()).append(value)

        for edge_set, keys in list(edge_set_to_keys.items()):
            key_to_abbrev = MetaGraph.find_abbrevs(keys)
            for key, abbrev in list(key_to_abbrev.items()):
                previous_abbrev = kind_to_abbrev.get(key)
                if previous_abbrev and len(abbrev) <= len(previous_abbrev):
                    continue
                kind_to_abbrev[key] = abbrev

        self.set_abbreviations(kind_to_abbrev)
        self.kind_to_abbrev = kind_to_abbrev
        return kind_to_abbrev

    def set_abbreviations(self, kind_to_abbrev):
        for kind, node in self.node_dict.items():
            node.abbrev = kind_to_abbrev[kind]
        for metaedge in self.edge_dict.values():
            metaedge.kind_abbrev = kind_to_abbrev[metaedge.kind]


    def add_node(self, kind):
        metanode = MetaNode(kind)
        self.node_dict[kind] = metanode

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

        if source == target and direction == 'both':
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

    def extract_metapaths(self, source_kind, target_kind, max_length):
        source = self.node_dict[source_kind]
        target = self.node_dict[target_kind]

        metapaths = [self.get_metapath((edge, )) for edge in source.edges]
        previous_metapaths = list(metapaths)
        for depth in range(1, max_length):
            current_metapaths = list()
            for metapath in previous_metapaths:
                for add_edge in metapath.target().edges:
                    new_metapath = self.get_metapath(metapath.edges + (add_edge, ))
                    current_metapaths.append(new_metapath)
            metapaths.extend(current_metapaths)
            previous_metapaths = current_metapaths
        metapaths = [metapath for metapath in metapaths if metapath.target() == target]
        return metapaths

    def get_metapath(self, edges):
        """ """
        try:
            return self.path_dict[edges]
        except KeyError:
            assert isinstance(edges, tuple)
            if len(edges) == 0:
                return None

            metapath = MetaPath(edges)
            self.path_dict[edges] = metapath

            inverse_edges = metapath.inverse_edges()
            inverse = MetaPath(inverse_edges)
            self.path_dict[inverse_edges] = inverse

            metapath.inverse = inverse
            inverse.inverse = metapath

            sub_edges = edges[1:]
            if not sub_edges:
                metapath.sub = None
                inverse.sub = None
            else:
                metapath.sub = self.get_metapath(sub_edges)
                inverse.sub = self.get_metapath(inverse_edges[1:])

            return metapath


class MetaNode(BaseNode):

    def __init__(self, identifier):
        """ """
        BaseNode.__init__(self, identifier)
        self.edges = set()
        self.hash_ = hash(self)

    def get_id(self):
        return self.identifier

class MetaEdge(BaseEdge):

    def __init__(self, source, target, kind, direction):
        """source and target are MetaNodes."""
        BaseEdge.__init__(self, source, target)
        self.kind = kind
        self.direction = direction
        self.hash_ = hash(self)

    def get_id(self):
        """ """
        return self.source.identifier, self.target.identifier, self.kind, self.direction

    def filesystem_str(self):
        return '{0}{2}{1}-{3}'.format(self.source.abbrev, self.target.abbrev,
                                      self.kind_abbrev, self.direction)

class MetaPath(BasePath):

    def __init__(self, edges):
        """metaedges is a tuple of edges"""
        assert all(isinstance(edge, MetaEdge) for edge in edges)
        BasePath.__init__(self, edges)

    def __repr__(self):
        s = str()
        for edge in self:
            source_abbrev = edge.source.abbrev
            dir_abbrev = direction_to_abbrev[edge.direction]
            kind_abbrev = edge.kind_abbrev
            s += '{0}{1}{2}{1}'.format(source_abbrev, dir_abbrev, kind_abbrev)
        s += self.target().abbrev
        return s


class Tree(object):

    __slots__ = ('parent', 'edge') #, 'is_root', 'path_to_root')

    def __init__(self, parent, edge):
        self.parent = parent
        self.edge = edge

    def path_to_root(self):
        path_edges = [self.edge]
        parent = self.parent
        while parent is not None:
            path_edges.append(parent.edge)
            parent = parent.parent
        path_edges = tuple(reversed(path_edges))
        path = Path(path_edges)
        return path

    def nodes_to_root(self):
        nodes = [self.edge.target, self.edge.source]
        parent = self.parent
        while parent is not None:
            nodes.append(parent.edge.source)
            parent = parent.parent
        return nodes


class Graph(BaseGraph):

    def __init__(self, metagraph, data=dict()):
        """ """
        BaseGraph.__init__(self)
        self.metagraph = metagraph
        self.data = data

    def add_node(self, kind, identifier, name=None, data={}):
        """ """
        if name is None:
            name = identifier
        metanode = self.metagraph.node_dict[kind]
        node = Node(metanode, identifier, name, data)
        self.node_dict[node.get_id()] = node
        return node

    def add_edge(self, source_identifier, target_identifier, kind, direction, data=dict()):
        """ """
        source = self.node_dict[source_id]
        target = self.node_dict[target_id]
        metaedge_id = source.metanode.identifier, target.metanode.identifier, kind, direction
        metaedge = self.metagraph.edge_dict[metaedge_id]
        edge = Edge(source, target, metaedge, data)
        self.edge_dict[edge.get_id()] = edge
        edge.inverted = metaedge.inverted

        inverse = Edge(target, source, metaedge.inverse, data)
        inverse_id = inverse.get_id()
        self.edge_dict[inverse_id] = inverse
        inverse.inverted = not edge.inverted

        edge.inverse = inverse
        inverse.inverse = edge

        return edge, inverse

    def paths_tree(self, source, metapath,
                   duplicates=False, masked=True,
                   exclude_nodes=set(), exclude_edges=set()):
        """
        Return a list of Paths starting with source and following metapath.
        Setting duplicates False disallows paths with repeated nodes.
        Setting masked False disallows paths which traverse a masked node or edge.
        exclude_nodes and exclude_edges allow specification of additional nodes
        and edges beyond (or independent of) masked nodes and edges.
        """

        if not isinstance(source, Node):
            source = self.node_dict[source]

        if masked and source.masked:
            return None

        if source in exclude_nodes:
            return None

        leaves = list()
        for edge in source.edges[metapath[0]]:
            edge_target = edge.target
            if not duplicates and source == edge_target:
                continue
            if edge_target in exclude_nodes or edge in exclude_edges:
                continue
            if not masked and (edge_target.masked or edge.masked):
                continue
            tree = Tree(parent=None, edge=edge)
            leaves.append(tree)

        for metaedge in metapath[1:]:
            new_leaves = list()
            for parent in leaves:
                edges = parent.edge.target.edges[metaedge]
                path_members = set(parent.nodes_to_root())
                for edge in edges:
                    edge_target = edge.target
                    if not duplicates and edge_target in path_members:
                        continue
                    if edge_target in exclude_nodes or edge in exclude_edges:
                        continue
                    if not masked and (edge_target.masked or edge.masked):
                        continue

                    tree = Tree(parent=parent, edge=edge)
                    new_leaves.append(tree)
            leaves = new_leaves
            if not leaves:
                break

        return leaves

    def paths_between_tree(self, source, target, metapath,
                      duplicates=False, masked=True,
                      exclude_nodes=set(), exclude_edges=set()):
        """
        Retreive the paths starting with the node source and ending on the
        node target. Future implementations should split the metapath, computing
        paths_from the source and target and look for the intersection at the
        intermediary Node position.
        """
        split_threshold = 2
        if len(metapath) <= split_threshold:
            leaves = self.paths_tree(source, metapath, duplicates, masked, exclude_nodes, exclude_edges)
            leaves = [leaf for leaf in leaves if leaf.edge.target == target]
            paths = [leaf.path_to_root() for leaf in leaves]
            return paths


        split_index = len(metapath) / 2

        get_metapath = self.metagraph.get_metapath
        metapath_head = get_metapath(metapath[:split_index])
        metapath_tail = get_metapath(tuple(mp.inverse for mp in reversed(metapath[split_index:])))
        head_leaves = self.paths_tree(source, metapath_head, duplicates, masked, exclude_nodes, exclude_edges)
        tail_leaves = self.paths_tree(target, metapath_tail, duplicates, masked, exclude_nodes, exclude_edges)

        head_leaf_targets = {head_leaf.edge.target for head_leaf in head_leaves}
        tail_leaf_targets = {tail_leaf.edge.target for tail_leaf in tail_leaves}
        intersecting_leaf_targets = head_leaf_targets & tail_leaf_targets

        head_leaves = [leaf for leaf in head_leaves if leaf.edge.target in intersecting_leaf_targets]
        tail_leaves = [leaf for leaf in tail_leaves if leaf.edge.target in intersecting_leaf_targets]


        head_dict = dict()
        for leaf in head_leaves:
            path = leaf.path_to_root()
            head_dict.setdefault(leaf.edge.target, list()).append(path)

        tail_dict = dict()
        for leaf in tail_leaves:
            path = leaf.path_to_root()
            tail_dict.setdefault(leaf.edge.target, list()).append(path)

        paths = list()
        for node in intersecting_leaf_targets:
            heads = head_dict[node]
            tails = tail_dict[node]
            for head, tail in itertools.product(heads, tails):
                path = Path(head.edges + tail.edges)
                if not duplicates:
                    nodes = path.get_nodes()
                    if len(set(nodes)) < len(nodes):
                        continue
                paths.append(path)

        return paths



    def paths_from(self, source, metapath,
                   duplicates=False, masked=True,
                   exclude_nodes=set(), exclude_edges=set()):
        """
        Return a list of Paths starting with source and following metapath.
        Setting duplicates False disallows paths with repeated nodes.
        Setting masked False disallows paths which traverse a masked node or edge.
        exclude_nodes and exclude_edges allow specification of additional nodes
        and edges beyond (or independent of) masked nodes and edges.
        """

        if not isinstance(source, Node):
            source = self.node_dict[source]

        if masked and source.masked:
            return None

        if source in exclude_nodes:
            return None

        paths = list()

        for edge in source.edges[metapath[0]]:
            edge_target = edge.target
            if edge_target in exclude_nodes:
                continue
            if edge in exclude_edges:
                continue
            if not masked and (edge_target.masked or edge.masked):
                continue
            if not duplicates and edge_target == source:
                continue
            path = Path((edge, ))
            paths.append(path)

        for i in range(1, len(metapath)):
            current_paths = list()
            metaedge = metapath[i]
            for path in paths:
                nodes = path.get_nodes()
                edges = path.target().edges[metaedge]
                for edge in edges:
                    edge_target = edge.target
                    if edge_target in exclude_nodes:
                        continue
                    if edge in exclude_edges:
                        continue
                    if not masked and (edge_target.masked or edge.masked):
                        continue
                    if not duplicates and edge_target in nodes:
                        continue
                    newpath = Path(path.edges + (edge, ))
                    current_paths.append(newpath)
            paths = current_paths

        return paths

    def paths_between(self, source, target, metapath,
                      duplicates=False, masked=True,
                      exclude_nodes=set(), exclude_edges=set()):
        """
        Retreive the paths starting with the node source and ending on the
        node target. Future implementations should split the metapath, computing
        paths_from the source and target and look for the intersection at the
        intermediary Node position.
        """
        if len(metapath) <= 1:
            paths = self.paths_from(source, metapath, duplicates, masked,
                                    exclude_nodes, exclude_edges)
            paths = [path for path in paths if path.target() == target]
            return paths


        split_index = len(metapath) / 2

        get_metapath = self.metagraph.get_metapath
        metapath_head = get_metapath(metapath[:split_index])
        metapath_tail = get_metapath(tuple(mp.inverse for mp in reversed(metapath[split_index:])))
        paths_head = self.paths_from(source, metapath_head, duplicates, masked, exclude_nodes, exclude_edges)
        paths_tail = self.paths_from(target, metapath_tail, duplicates, masked, exclude_nodes, exclude_edges)

        node_intersect = (set(path.target() for path in paths_head) &
                          set(path.target() for path in paths_tail))

        head_dict = dict()
        for path in paths_head:
            path_target = path.target()
            if path_target in node_intersect:
                head_dict.setdefault(path_target, list()).append(path)

        tail_dict = dict()
        for path in paths_tail:
            path_target = path.target()
            if path_target in node_intersect:
                path = Path(path.inverse_edges())
                tail_dict.setdefault(path_target, list()).append(path)

        paths = list()
        for node in node_intersect:
            heads = head_dict[node]
            tails = tail_dict[node]
            for head, tail in itertools.product(heads, tails):
                path = Path(head.edges + tail.edges)
                if not duplicates:
                    nodes = path.get_nodes()
                    if len(set(nodes)) < len(nodes):
                        continue
                paths.append(path)

        return paths


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
        return self.source.identifier, self.target.identifier, self.metaedge.kind, self.metaedge.direction

class Path(BasePath):

    def __init__(self, edges):
        """potentially metapath should be an input although it can be calculated"""
        BasePath.__init__(self, edges)

    def __repr__(self):
        s = ''
        for edge in self:
            dir_abbrev = direction_to_abbrev[edge.metaedge.direction]
            s += '{0} {1} {2} {1} '.format(edge.source, dir_abbrev, edge.metaedge.kind)
        s = '{}{}'.format(s, self.target())
        return s
