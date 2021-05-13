from sklearn.base import BaseEstimator
from abc import ABC, abstractmethod


class Xy:
    """
    Holder class for Xy, where X is array-like and y is array-like. This is the base
    data structure for fully materialized X and y.
    """

    def __init__(self, X, y):
        self.__X__ = X
        self.__y__ = y

    """
    Returns the holder value of X
    """

    def get_x(self):
        return self.__X__

    """
    Returns the holder value of y
    """

    def get_y(self):
        return self.__y__


class XYRef:
    """
    Holder class that maintains a pointer/reference to X and y. The goal of this is to provide
    a holder to the object references of Ray. This is used for passing outputs from a transform/fit
    to the next stage of the pipeline. Since the references can be potentially in flight (or being
    computed), these holders are essential to the pipeline constructs.
    """

    def __init__(self, Xref, yref):
        self.__Xref__ = Xref
        self.__yref__ = yref

    def get_Xref(self):
        """
            Returns the object reference to X
        """
        return self.__Xref__

    def get_yref(self):
        """
            Returns the object reference to y
        """
        return self.__yref__


class Node(ABC):
    """
    A node class that is an abstract one, this is capturing basic info re the Node.
    """

    def __str__(self):
        return self.__node_name__

    @abstractmethod
    def get_and_flag(self):
        raise NotImplementedError("Please implement this method")

    def __hash__(self):
        return self.__node_name__.__hash__()

    def __eq__(self, other):
        return (
                self.__class__ == other.__class__ and
                self.__node_name__ == other.__node_name__
        )


class OrNode(Node):
    __estimator__ = None

    def __init__(self, node_name: str, estimator: BaseEstimator):
        self.__node_name__ = node_name
        self.__estimator__ = estimator

    def get_estimator(self) -> BaseEstimator:
        return self.__estimator__

    def get_and_flag(self):
        return False


class AndFunc(ABC):
    @abstractmethod
    def eval(self, xy_list: list) -> Xy:
        raise NotImplementedError("Please implement this method")


class AndNode(Node):
    __andfunc__ = None

    def __init__(self, node_name: str, and_func: AndFunc):
        self.__node_name__ = node_name
        self.__andfunc__ = and_func

    def get_and_func(self) -> AndFunc:
        return self.__andfunc__

    def get_and_flag(self):
        return True


class Edge:
    __from_node__ = None
    __to_node__ = None

    def __init__(self, from_node: Node, to_node: Node):
        self.__from_node__ = from_node
        self.__to_node__ = to_node

    def get_from_node(self) -> Node:
        return self.__from_node__

    def get_to_node(self) -> Node:
        return self.__to_node__

    def __str__(self):
        return str(self.__from_node__) + ' -> ' + str(self.__to_node__)

    def __hash__(self):
        return self.__from_node__.__hash__() ^ self.__to_node__.__hash__()

    def __eq__(self, other):
        return (
                self.__class__ == other.__class__ and
                self.__from_node__ == other.__from_node__ and
                self.__to_node__ == other.__to_node__
        )


class KeyedObjectRef:
    __key__: object = None
    __object_ref = None

    def __init__(self, obj_ref, key: object = None):
        self.__key__ = key
        self.__object_ref = obj_ref

    def get_key(self):
        return self.__key__

    def get_object_ref(self):
        return self.__object_ref


class Pipeline:
    __pre_graph__ = {}
    __post_graph__ = {}
    __node_levels__ = None
    __level_nodes__ = None

    def __init__(self):
        self.__pre_graph__ = {}
        self.__post_graph__ = {}
        self.__node_levels__ = None
        self.__level_nodes__ = None

    def add_node(self, node: Node):
        self.__node_levels__ = None
        self.__level_nodes__ = None
        if node not in self.__pre_graph__.keys():
            self.__pre_graph__[node] = []
            self.__post_graph__[node] = []

    def __str__(self):
        res = ''
        for node in self.__pre_graph__.keys():
            res += str(node)
            res += '='
            res += self.get_str(self.__pre_graph__[node])
            res += '\r\n'
        return res

    @staticmethod
    def get_str(nodes: list):
        res = ''
        for node in nodes:
            res += str(node)
            res += ' '
        return res

    def add_edge(self, from_node: Node, to_node: Node):
        self.add_node(from_node)
        self.add_node(to_node)

        self.__pre_graph__[to_node].append(from_node)
        self.__post_graph__[from_node].append(to_node)

    def get_preimage(self, node: Node):
        return self.__pre_graph__[node]

    def get_postimage(self, node: Node):
        return self.__post_graph__[node]

    def compute_node_level(self, node: Node, result: dict):
        if node in result:
            return result[node]

        node_preimage = self.get_preimage(node)
        if not node_preimage:
            result[node] = 0
            return 0

        max_level = 0
        for p_node in node_preimage:
            level = self.compute_node_level(p_node, result)
            max_level = max(level, max_level)

        result[node] = max_level + 1

        return max_level + 1

    def compute_node_levels(self):
        if self.__node_levels__:
            return self.__node_levels__

        result = {}
        for node in self.__pre_graph__.keys():
            result[node] = self.compute_node_level(node, result)

        self.__node_levels__ = result

        return self.__node_levels__

    def compute_max_level(self):
        levels = self.compute_node_levels()
        max_level = 0
        for node, node_level in levels.items():
            max_level = max(node_level, max_level)
        return max_level

    def get_nodes_by_level(self):
        if self.__level_nodes__:
            return self.__level_nodes__

        levels = self.compute_node_levels()
        result_size = self.compute_max_level() + 1
        result = []
        for i in range(result_size):
            result.append(list())

        for node, node_level in levels.items():
            result[node_level].append(node)

        self.__level_nodes__ = result
        return self.__level_nodes__

    ###
    # Get downstream node
    ###
    def get_post_nodes(self, node: Node):
        return self.__post_graph__[node]

    def get_pre_nodes(self, node: Node):
        return self.__pre_graph__[node]

    def get_pre_edges(self, node: Node):
        pre_edges = []
        pre_nodes = self.__pre_graph__[node]
        # Empty pre
        if not pre_nodes:
            pre_edges.append(Edge(None, node))

        for pre_node in pre_nodes:
            pre_edges.append(Edge(pre_node, node))
        return pre_edges

    def get_post_edges(self, node: Node):
        post_edges = []
        post_nodes = self.__post_graph__[node]
        # Empty post
        if not post_nodes:
            post_edges.append(Edge(node, None))

        for post_node in post_nodes:
            post_edges.append(Edge(node, post_node))
        return post_edges

    def is_terminal(self, node: Node):
        node_post_edges = self.get_post_edges(node)
        return len(node_post_edges) == 0
