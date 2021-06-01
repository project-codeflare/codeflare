from abc import ABC, abstractmethod
from enum import Enum

import sklearn.base as base
from sklearn.base import TransformerMixin
from sklearn.base import BaseEstimator

import ray
import pickle5 as pickle
import codeflare.pipelines.Exceptions as pe


class Xy:
    """
    Holder class for Xy, where X is array-like and y is array-like. This is the base
    data structure for fully materialized X and y.

    Examples
    --------
    .. code-block:: python

        x = np.array([1.0, 2.0, 4.0, 5.0])
        y = np.array(['odd', 'even', 'even', 'odd'])
        xy = Xy(x, y)

    """

    def __init__(self, X, y):
        """
        Init this instance with the given X and y, X and y shapes are assumed to
        be consistent.

        :param X: Array-like X
        :param y: Array-like y
        """
        self.__X__ = X
        self.__y__ = y

    def get_x(self):
        """
        Getter for X

        :return: Holder value of X
        """
        return self.__X__

    def get_y(self):
        """
        Getter for y

        :return: Holder value of y
        """
        return self.__y__


class XYRef:
    """
    Holder class that maintains a pointer/reference to X and y. The goal of this is to provide
    a holder to the object references of Ray. This is used for passing outputs from a transform/fit
    to the next stage of the pipeline. Since the references can be potentially in flight (or being
    computed), these holders are essential to the pipeline constructs.

    It also holds the state of the node itself, with the previous state of the node before a transform
    operation is applied being held along with the next state. It also holds the previous
    XYRef instances. In essence, this holder class is a bunch of pointers, but it is enough to reconstruct
    the entire pipeline through appropriate traversals.
    """

    def __init__(self, Xref: ray.ObjectRef, yref: ray.ObjectRef, prev_node_state_ref: ray.ObjectRef=None, curr_node_state_ref: ray.ObjectRef=None, prev_Xyrefs = None):
        """
        Init, default is only references to X and y as object references

        :param Xref: ObjectRef to X
        :param yref: ObjectRef to y
        :param prev_node_state_ref: ObjectRef to previous node state, default is None
        :param curr_node_state_ref: ObjectRef to current node state, default in None
        :param prev_Xyrefs: List of XYrefs
        """
        self.__Xref__ = Xref
        self.__yref__ = yref
        self.__prev_node_state_ref__ = prev_node_state_ref
        self.__curr_node_state_ref__ = curr_node_state_ref
        self.__prev_Xyrefs__ = prev_Xyrefs

    def get_Xref(self) -> ray.ObjectRef:
        """
        Getter for the reference to X

        :return: ObjectRef to X
        """
        return self.__Xref__

    def get_yref(self) -> ray.ObjectRef:
        """
        Getter for the reference to y

        :return: ObjectRef to y
        """
        return self.__yref__

    def get_prev_node_state_ref(self) -> ray.ObjectRef:
        """
        Getter for the reference to previous node state

        :return: ObjectRef to previous node state
        """
        return self.__prev_node_state_ref__

    def get_curr_node_state_ref(self) -> ray.ObjectRef:
        """
        Getter for the reference to current node state

        :return: ObjectRef to current node state
        """
        return self.__curr_node_state_ref__

    def get_prev_xyrefs(self):
        """
        Getter for the list of previous XYrefs

        :return: List of XYRefs
        """
        return self.__prev_Xyrefs__


class NodeInputType(Enum):
    OR = 0,
    AND = 1


class NodeFiringType(Enum):
    ANY = 0,
    ALL = 1


class NodeStateType(Enum):
    STATELESS = 0,
    IMMUTABLE = 1,
    MUTABLE_SEQUENTIAL = 2,
    MUTABLE_AGGREGATE = 3


class Node(ABC):
    """
    A node class that is an abstract one, this is capturing basic info re the Node.
    The hash code of this node is the name of the node and equality is defined if the
    node name and the type of the node match.
    """

    def __init__(self, node_name, node_input_type: NodeInputType, node_firing_type: NodeFiringType, node_state_type: NodeStateType):
        self.__node_name__ = node_name
        self.__node_input_type__ = node_input_type
        self.__node_firing_type__ = node_firing_type
        self.__node_state_type__ = node_state_type

    def __str__(self):
        return self.__node_name__

    def get_node_name(self):
        return self.__node_name__

    def get_node_input_type(self):
        return self.__node_input_type__

    def get_node_firing_type(self):
        return self.__node_firing_type__

    def get_node_state_type(self):
        return self.__node_state_type__

    @abstractmethod
    def clone(self):
        raise NotImplementedError("Please implement the clone method")

    def __hash__(self):
        """
        Hash code, defined as the hash code of the node name

        :return: Hash code
        """
        return self.__node_name__.__hash__()

    def __eq__(self, other):
        """
        Equality with another node, defined as the class names match and the
        node names match

        :param other: Node to compare with
        :return: True if nodes are equal, else False
        """
        return (
                self.__class__ == other.__class__ and
                self.__node_name__ == other.__node_name__
        )


class EstimatorNode(Node):
    """
    Or node, which is the basic node that would be the equivalent of any SKlearn pipeline
    stage. This node is initialized with an estimator that needs to extend sklearn.BaseEstimator.
    """

    def __init__(self, node_name: str, estimator: BaseEstimator):
        """
        Init the OrNode with the name of the node and the etimator.

        :param node_name: Name of the node
        :param estimator: The base estimator
        """

        super().__init__(node_name, NodeInputType.OR, NodeFiringType.ANY, NodeStateType.IMMUTABLE)
        self.__estimator__ = estimator

    def get_estimator(self) -> BaseEstimator:
        """
        Return the estimator that this was initialize with

        :return: Estimator
        """
        return self.__estimator__

    def clone(self):
        cloned_estimator = base.clone(self.__estimator__)
        return EstimatorNode(self.__node_name__, cloned_estimator)


class AndTransform(TransformerMixin, BaseEstimator):
    @abstractmethod
    def transform(self, xy_list: list) -> Xy:
        raise NotImplementedError("Please implement this method")


class GeneralTransform(TransformerMixin, BaseEstimator):
    @abstractmethod
    def transform(self, xy: Xy) -> Xy:
        raise NotImplementedError("Please implement this method")


class AndNode(Node):
    def __init__(self, node_name: str, and_func: AndTransform):
        super().__init__(node_name, NodeInputType.AND, NodeFiringType.ANY, NodeStateType.STATELESS)
        self.__andfunc__ = and_func

    def get_and_func(self) -> AndTransform:
        return self.__andfunc__

    def clone(self):
        return AndNode(self.__node_name__, self.__andfunc__)


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
    """
    The pipeline class that defines the DAG structure composed of Node(s). The
    """

    def __init__(self):
        self.__pre_graph__ = {}
        self.__post_graph__ = {}
        self.__node_levels__ = None
        self.__level_nodes__ = None
        self.__node_name_map__ = {}

    def add_node(self, node: Node):
        self.__node_levels__ = None
        self.__level_nodes__ = None
        if node not in self.__pre_graph__.keys():
            self.__pre_graph__[node] = []
            self.__post_graph__[node] = []
            self.__node_name_map__[node.get_node_name()] = node

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

    def compute_node_level(self, node: Node, result: dict):
        if node in result:
            return result[node]

        pre_nodes = self.get_pre_nodes(node)
        if not pre_nodes:
            result[node] = 0
            return 0

        max_level = 0
        for p_node in pre_nodes:
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

    def get_node_level(self, node: Node):
        self.compute_node_levels()
        return self.__node_levels__[node]

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

    def is_output(self, node: Node):
        post_nodes = self.get_post_nodes(node)
        return not post_nodes

    def get_output_nodes(self):
        # dict from level to nodes
        terminal_nodes = []
        for node in self.__pre_graph__.keys():
            if self.is_output(node):
                terminal_nodes.append(node)
        return terminal_nodes

    def get_nodes(self):
        return self.__node_name_map__

    def get_pre_nodes(self, node):
        return self.__pre_graph__[node]

    def get_post_nodes(self, node):
        return self.__post_graph__[node]

    def is_input(self, node: Node):
        pre_nodes = self.get_pre_nodes(node)
        return not pre_nodes

    def get_input_nodes(self):
        input_nodes = []
        for node in self.__node_name_map__.values():
            if self.get_node_level() == 0:
                input_nodes.append(node)

        return input_nodes

    def get_node(self, node_name: str) -> Node:
        return self.__node_name_map__[node_name]

    def save(self, filehandle):
        nodes = {}
        edges = []

        for node in self.__pre_graph__.keys():
            nodes[node.get_node_name()] = node
            pre_edges = self.get_pre_edges(node)
            for edge in pre_edges:
                # Since we are iterating on pre_edges, to_node cannot be None
                from_node = edge.get_from_node()
                if from_node is not None:
                    to_node = edge.get_to_node()
                    edge_tuple = (from_node.get_node_name(), to_node.get_node_name())
                    edges.append(edge_tuple)
        saved_pipeline = _SavedPipeline(nodes, edges)
        pickle.dump(saved_pipeline, filehandle)

    @staticmethod
    def load(filehandle):
        saved_pipeline = pickle.load(filehandle)
        if not isinstance(saved_pipeline, _SavedPipeline):
            raise pe.PipelineException("Filehandle is not a saved pipeline instance")

        nodes = saved_pipeline.get_nodes()
        edges = saved_pipeline.get_edges()

        pipeline = Pipeline()
        for edge in edges:
            (from_node_str, to_node_str) = edge
            from_node = nodes[from_node_str]
            to_node = nodes[to_node_str]
            pipeline.add_edge(from_node, to_node)
        return pipeline


class _SavedPipeline:
    def __init__(self, nodes, edges):
        self.__nodes__ = nodes
        self.__edges__ = edges

    def get_nodes(self):
        return self.__nodes__

    def get_edges(self):
        return self.__edges__


class PipelineOutput:
    """
    Pipeline output to keep reference counters so that pipelines can be materialized
    """
    def __init__(self, out_args, edge_args):
        self.__out_args__ = out_args
        self.__edge_args__ = edge_args

    def get_xyrefs(self, node: Node):
        if node in self.__out_args__:
            xyrefs_ptr = self.__out_args__[node]
        elif node in self.__edge_args__:
            xyrefs_ptr = self.__edge_args__[node]
        else:
            raise pe.PipelineNodeNotFoundException("Node " + str(node) + " not found")

        xyrefs = ray.get(xyrefs_ptr)
        return xyrefs

    def get_edge_args(self):
        return self.__edge_args__


class PipelineInput:
    """
    in_args is a dict from a node -> [Xy]
    """
    def __init__(self):
        self.__in_args__ = {}

    def add_xyref_ptr_arg(self, node: Node, xyref_ptr):
        if node not in self.__in_args__:
            self.__in_args__[node] = []

        self.__in_args__[node].append(xyref_ptr)

    def add_xyref_arg(self, node: Node, xyref: XYRef):
        if node not in self.__in_args__:
            self.__in_args__[node] = []

        xyref_ptr = ray.put(xyref)
        self.__in_args__[node].append(xyref_ptr)

    def add_xy_arg(self, node: Node, xy: Xy):
        if node not in self.__in_args__:
            self.__in_args__[node] = []

        x_ref = ray.put(xy.get_x())
        y_ref = ray.put(xy.get_y())
        xyref = XYRef(x_ref, y_ref)
        self.add_xyref_arg(node, xyref)

    def get_in_args(self):
        return self.__in_args__
