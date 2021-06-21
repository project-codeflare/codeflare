#
# Copyright 2021 IBM
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html
#
# Authors: Mudhakar Srivatsa <msrivats@us.ibm.com>
#          Raghu Ganti <rganti@us.ibm.com>
#          Carlos Costa <chcost@us.ibm.com>
#
#

"""codeflare.pipelines.Datamodel
The core data model structures are defined here. These include the various aspects for creating a DAG, the
input and output to the DAG itself.

- :class:`~codeflare.pipelines.Datamodel.Pipeline`: The class that defines the pipeline graph is captured, which is supported by Node and Edge constructs.
- :class:`~codeflare.pipelines.Datamodel.Node`: The node class that has two implementations, :class:`~codeflare.pipelines.Datamodel.EstimatorNode` and :class:`~codeflare.pipelines.Datamodel.AndNode`, the details of these are captured in a separate document on nodes and their semantics defined by the type, firing semantics, and state.
- :class:`~codeflare.pipelines.Datamodel.PipelineInput`: The input for pipeline, supported by Xy and XYRef holder classes.
- :class:`~codeflare.pipelines.Datamodel.PipelineOutput`: The output for pipeline (after execution), supported by Xy and XYRef holder classes.
- :class:`~codeflare.pipelines.Datamodel.Xy`: A basic holder class for X and y, both of which are numpy arrays.
- :class:`~codeflare.pipelines.Datamodel.XYRef`: A basic holder class for pointers to X and y, pointers are reference to objects in Plasma store of Ray.
- :class:`~codeflare.pipelines.Datamodel.PipelineParam`: Finally, the data model allows for morphing of pipeline based on parameterizations, these parameterizations can be for grid search or for other such similar reasons.
"""

from abc import ABC, abstractmethod
from enum import Enum

import sklearn.base as base
from sklearn.base import BaseEstimator
from sklearn.model_selection import ParameterGrid

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
    to the next stage of the pipeline. Since the object references can be potentially in flight (or being
    computed), these holders are essential to the pipeline constructs.

    It also holds the state of the node itself, with the previous state of the node before a transform
    operation is applied being held along with the next state. It also holds the previous
    XYRef instances. In essence, this holder class is a bunch of pointers, but it is enough to reconstruct
    the entire pipeline through appropriate traversals.

    NOTE: Default constructor takes pointer to X and y. The more advanced constructs are pointer
    holders for the pipeline during its execution and are not meant to be used outside by developers.

    Examples
    --------
    .. code-block:: python

        x = np.array([1.0, 2.0, 4.0, 5.0])
        y = np.array(['odd', 'even', 'even', 'odd'])
        x_ref = ray.put(x)
        y_ref = ray.put(y)

        xy_ref = XYRef(x_ref, y_ref)
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

    def __hash__(self):
        return self.__Xref__.__hash__() ^ self.__yref__.__hash__()

    def __eq__(self, other):
        return (
                self.__class__ == other.__class__ and
                self.__Xref__ == other.__Xref__ and
                self.__yref__ == other.__yref__
        )


class NodeInputType(Enum):
    """
    Defines the node input types, currently, it supports an OR and AND node. An OR node is backed by an
    Estimator and an AND node is backed by an arbitrary lambda defined by an AndFunc. The key difference
    is that for an OR node, the parallelism is defined at a single XYRef object, whereas for an AND node,
    the parallelism is defined on a collection of objects coming "into" the AND node.

    For details on parallelism and pipeline semantics, the reader is directed to the pipeline semantics
    introduction of the User guide.
    """
    OR = 0,
    AND = 1


class NodeFiringType(Enum):
    """
    Defines the "firing" semantics of a node, there are two types of firing semantics, ANY and ALL. ANY
    firing semantics means that upon the availability of a single object, the node will start executing
    its work. Whereas, on ALL semantics, the node has to wait for ALL the objects ot be materialized
    before the computation can begin, i.e. it is blocking.

    For details on firing and pipeline semantics, the reader is directed to the pipeline semantics
    introduction of the User guide.
    """
    ANY = 0,
    ALL = 1


class NodeStateType(Enum):
    """
    Defines the state type of a node, there are 4 types of state, which are STATELESS, IMMUTABLE, MUTABLE_SEQUENTIAL
    and MUTABLE_AGGREGATE.

    A STATELESS node is one that keeps no state and can be called any number of times without any change to the "model"
    or "function" state.

    A IMMUTABLE node is one that once a model has "fitted" cannot change, i.e. there is no partial fit available.

    A MUTABLE_SEQUENTIAL node is one that can be updated with a sequence of input object(s) or a stream.

    A MUTABLE_AGGREGATE node is one that can be updated in batches.
    """
    STATELESS = 0,
    IMMUTABLE = 1,
    MUTABLE_SEQUENTIAL = 2,
    MUTABLE_AGGREGATE = 3


class Node(ABC):
    """
    A node class that is an abstract one, this is capturing basic info re the Node.
    The hash code of this node is the name of the node and equality is defined if the
    node name and the type of the node match.

    When doing a grid search, a node can be parameterized with new params for the estimator and updated. This
    is an internal method used by grid search.
    """

    def __init__(self, node_name, estimator: BaseEstimator, node_input_type: NodeInputType, node_firing_type: NodeFiringType, node_state_type: NodeStateType):
        self.__node_name__ = node_name
        self.__estimator__ = estimator
        self.__node_input_type__ = node_input_type
        self.__node_firing_type__ = node_firing_type
        self.__node_state_type__ = node_state_type

    def __str__(self):
        """
        Returns a string representation of the node along with the parameters of the estimator of the node.

        :return: String representation of the node
        """
        estimator_params_str = str(self.get_estimator().get_params())
        retval = self.__node_name__ + estimator_params_str
        return retval

    def get_node_name(self) -> str:
        """
        Returns the node name

        :return: The name of this node
        """
        return self.__node_name__

    def get_node_input_type(self) -> NodeInputType:
        """
        Return the node input type

        :return: The node input type
        """
        return self.__node_input_type__

    def get_node_firing_type(self) -> NodeFiringType:
        """
        Return the node firing type

        :return: The node firing type
        """
        return self.__node_firing_type__

    def get_node_state_type(self) -> NodeStateType:
        """
        Return the node state type

        :return: The node state type
        """
        return self.__node_state_type__

    def get_estimator(self):
        """
        Return the estimator of the node

        :return: The node's estimator
        """
        return self.__estimator__

    def get_parameterized_node(self, node_name, **params):
        """
        Get a parameterized node, given kwargs **params, convert this node and update the estimator with the
        new set of parameters. It will clone the node and its underlying estimator.

        :param node_name: New node name
        :param params: Updated parameters
        :return:
        """
        cloned_node = self.clone()
        cloned_node.__node_name__ = node_name
        estimator = cloned_node.get_estimator()
        estimator.set_params(**params)
        return cloned_node

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
    Basic estimator node, which is the basic node that would be the equivalent of any SKlearn pipeline
    stage. This node is initialized with an estimator that needs to extend sklearn.BaseEstimator.

    This estimator node is typically an OR node, with ANY firing semantics, and IMMUTABLE state. For
    partial fit, we will have to define a different node type to keep semantics very clear.

    .. code-block:: python

        random_forest = RandomForestClassifier(n_estimators=200)
        node_rf = dm.EstimatorNode('randomforest', random_forest)

        # get the estimator
        node_rf_estimator = node_rf.get_estimator()

        # clone the node, clones the estimator as well
        node_rf_cloned = node_rf.clone()
    """

    def __init__(self, node_name: str, estimator: BaseEstimator):
        """
        Init the OrNode with the name of the node and the etimator.

        :param node_name: Name of the node
        :param estimator: The base estimator
        """
        super().__init__(node_name, estimator, NodeInputType.OR, NodeFiringType.ANY, NodeStateType.IMMUTABLE)

    def clone(self):
        """
        Clones the given node and the underlying estimator as well, if it was initialized with

        :return: A cloned node
        """
        cloned_estimator = base.clone(self.__estimator__)
        return EstimatorNode(self.__node_name__, cloned_estimator)


class AndEstimator(BaseEstimator):
    """
    An and estimator, is part of the AndNode, it is very similar to a standard estimator, however the key
    difference is that it takes a `xy_list` as input and outputs an `xy`, contrasting to the EstimatorNode,
    which takes an input as `xy` and outputs `xy_t`.

    In the pipeline execution, we expect three modes: (a) FIT: A regressor or classifier will call the fit
    and then pass on the transform results downstream, a non-regressor/classifier will call the fit_transform
    method, (b) PREDICT: A regressor or classifier will call the predict method, whereas a non-regressor/classifier
    will call the transform method, and (c) SCORE: A regressor will call the score method, and a non-regressor/classifer
    will call the transform method.

    Examples
    --------
    Here is a simple FeatureUnion as an AndEstimator:

    .. code-block:: python

        class FeatureUnion(dm.AndEstimator):
            def __init__(self):
                pass

            def get_estimator_type(self):
                return 'transform'

            def clone(self):
                return base.clone(self)

            def fit_transform(self, xy_list):
                return self.transform(xy_list)

            def transform(self, xy_list):
                X_list = []
                y_vec = None
                for xy in xy_list:
                    X_list.append(xy.get_x())
                    y_vec = xy.get_y()
                X_concat = np.concatenate(X_list, axis=1)
                return dm.Xy(X_concat, y_vec)

    The above is doing a simple feature union by combining inputs from multiple edges and sending "back" a single
    concatenated xy. As a simple transform, it needs to only implement the `transform`, `fit_transform`, `clone`,
    and `get_estimator_type` methods.
    """
    @abstractmethod
    def transform(self, xy_list: list) -> Xy:
        """
        An abstract method that needs to be implemented if a simple estimator

        :param xy_list: List of xy
        :return: A single xy
        """
        raise NotImplementedError("And estimator needs to implement a transform method")

    @abstractmethod
    def fit(self, xy_list: list):
        """
        An abstract method that needs to be implemented if a regressor or a classifier

        :param xy_list: List of xy
        :return: A single xy
        """
        raise NotImplementedError("And estimator needs to implement a fit method")

    @abstractmethod
    def fit_transform(self, xy_list: list):
        """
        An abstract method that needs to be implemented if a simple estimator

        :param xy_list: List of xy
        :return: A single xy
        """
        raise NotImplementedError("And estimator needs to implement a fit method")

    @abstractmethod
    def predict(self, xy_list: list) -> Xy:
        """
        An abstract method that needs to be implemented if a regressor or a classifer

        :param xy_list: List of xy
        :return: A single xy
        """
        raise NotImplementedError("And classifier needs to implement the predict method")

    @abstractmethod
    def score(self, xy_list: list) -> Xy:
        """
        An abstract method that needs to be implemented if a regressor or a classifier

        :param xy_list: List of xy
        :return: A single xy
        """
        raise NotImplementedError("And classifier needs to implement the score method")

    @abstractmethod
    def get_estimator_type(self):
        """
        Any and estimator needs to implement this type, it is 'transform' if a simple transformer or is
        a 'classifier' if classifier and 'regressor' if a regressor.

        :return: The type of the estimator
        """
        raise NotImplementedError("And classifier needs to implement the get_estimator_type method")

    @abstractmethod
    def clone(self):
        """
        Abstract method and all estimators are supposed to implement these. Can be as simple as the basic
        python clone.

        :return: A cloned estimator
        """
        raise NotImplementedError("And estimator needs to implement a clone method")


class AndNode(Node):
    """
    Basic and node, that's capable of combining inputs from multiple edges. As such, it needs to have
    a AndEstimator implemented. The AndEstimator itself inherits from sklearn.BaseEstimator.

    This estimator node is a typical AND node, with ANY firing semantics, and STATELESS state.

    Examples
    --------
    An example building on the one from AndEstimator:

    .. code-block:: python

        feature_union_and_estimator = FeatureUnion()
        node_union_and = dm.AndNode('and_node_sample', feature_union_and_estimator)

    """
    def __init__(self, node_name: str, and_estimator: AndEstimator):
        super().__init__(node_name, and_estimator, NodeInputType.AND, NodeFiringType.ANY, NodeStateType.STATELESS)

    def clone(self):
        cloned_estimator = self.__estimator__.clone()
        return AndNode(self.__node_name__, cloned_estimator)


class Edge:
    """
    An edge connects two nodes, it's an internal data structure  for pipeline construction. An edge
    is a directed edge and has a "from_node" and a "to_node".

    An edge also defines a hash function and an equality, where the equality is on the from and to
    node names being the same.
    """
    def __init__(self, from_node: Node, to_node: Node):
        self.__from_node__ = from_node
        self.__to_node__ = to_node

    def get_from_node(self) -> Node:
        """
        The from_node of this edge (originating node)

        :return:  The from_node of this edge
        """
        return self.__from_node__

    def get_to_node(self) -> Node:
        """
        The to_node of this edge (terminating node)

        :return: The to_node of this edge
        """
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
    The pipeline class that defines the DAG structure composed of Node(s). This is the core data structure that
    defines the computation graph. A key note is that unlike SKLearn pipeline, CodeFlare pipelines are "abstract"
    graphs and get realized only when executed. Upon execution, they can potentially be multiple pathways in
    the pipeline, i.e. multiple "single" pipelines can be realized.

    Examples
    --------
    Pipelines can be constructed quite simply using the builder paradigm with add_node and/or add_edge. In its
    simplest form, one can create nodes and then wire the DAG by adding edges. An example that does a simple
    pipeline is below:

    .. code-block:: python

        feature_union = FeatureUnion(transformer_list=[('PCA', PCA()),
            ('Nystroem', Nystroem()), ('SelectKBest', SelectKBest(k=3))])
        random_forest = RandomForestClassifier(n_estimators=200)
        node_fu = dm.EstimatorNode('feature_union', feature_union)
        node_rf = dm.EstimatorNode('randomforest', random_forest)
        pipeline.add_edge(node_fu, node_rf)

    One can of course construct complex pipelines with multiple outgoing edges as well. An example of one that
    explores multiple models is shown below:

    .. code-block:: python

        preprocessor = ColumnTransformer(
        transformers=[
            ('num', numeric_transformer, numeric_features),
            ('cat', categorical_transformer, categorical_features)])

        classifiers = [
            RandomForestClassifier(),
            GradientBoostingClassifier()
        ]
        pipeline = dm.Pipeline()
        node_pre = dm.EstimatorNode('preprocess', preprocessor)
        node_rf = dm.EstimatorNode('random_forest', classifiers[0])
        node_gb = dm.EstimatorNode('gradient_boost', classifiers[1])

        pipeline.add_edge(node_pre, node_rf)
        pipeline.add_edge(node_pre, node_gb)

    A pipeline can be saved and loaded, which in essence saves the "graph" and not the state of this pipeline.
    For saving the state of the pipeline, one can use the Runtime's save method! Save/load of pipeline uses
    Pickle protocol 5.

    .. code-block:: python

        fname = 'save_pipeline.cfp'
        fh = open(fname, 'wb')
        pipeline.save(fh)
        fh.close()

        r_fh = open(fname, 'rb')
        saved_pipeline = dm.Pipeline.load(r_fh)

    """

    def __init__(self):
        self.__pre_graph__ = {}
        self.__post_graph__ = {}
        self.__node_levels__ = None
        self.__level_nodes__ = None
        self.__node_name_map__ = {}

    def __hash__(self):
        result = 1234
        for node in self.__node_name_map__.keys():
            result = result ^ node.__hash__()
        return result

    def __eq__(self, other):
        return (
                self.__class__ == other.__class__ and
                other.__pre_graph__ == self.__pre_graph__
        )

    def add_node(self, node: Node):
        """
        Adds a node to this pipeline

        :param node: The node to add
        :return: None
        """
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
        """
        Adds an edge to this pipeline

        :param from_node: The from node
        :param to_node: The to node
        :return: None
        """
        self.add_node(from_node)
        self.add_node(to_node)

        self.__pre_graph__[to_node].append(from_node)
        self.__post_graph__[from_node].append(to_node)

    def compute_node_level(self, node: Node, result: dict):
        """
        Computes the node levels for a given node, an internal supporting function that is recursive, so it
        takes the result computed so far.

        :param node: The node for which level needs to be computed
        :param result: The node levels that have already been computed
        :return: The level for this node
        """
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
        """
        Computes node levels for all nodes. If a cache of node levels from previous calls exists, it will return
        the cache to avoid repeated computation.

        :return: The mapping from node to its level as a dict
        """
        # TODO: This is incorrect when pipelines are mutable
        if self.__node_levels__:
            return self.__node_levels__

        result = {}
        for node in self.__pre_graph__.keys():
            result[node] = self.compute_node_level(node, result)

        self.__node_levels__ = result

        return self.__node_levels__

    def get_node_level(self, node: Node):
        """
        Returns the node level for the given node, a number between 0 and max_level (depth of the DAG/Pipeline).

        :param node: Given node
        :return: Level between 0 and max_depth of pipeline
        """
        self.compute_node_levels()
        return self.__node_levels__[node]

    def compute_max_level(self):
        """
        Get the max depth of this pipeline graph.

        :return: The max depth of pipeline
        """
        levels = self.compute_node_levels()
        max_level = 0
        for node, node_level in levels.items():
            max_level = max(node_level, max_level)
        return max_level

    def get_nodes_by_level(self):
        """
        A mapping from level to a list of nodes, useful for pipeline execution time. Similar to compute_levels,
        this method will return a cache if it exists, else will compute the levels and cache it.

        :return: The mapping from level to a list of nodes at that level
        """
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

    def get_post_nodes(self, node: Node):
        """
        Returns the nodes which are "below" the given node, i.e., have incoming edges from the
        given node, empty if it is an output node

        :param node: Given node
        :return: List of nodes that have incoming edges to the given node
        """
        return self.__post_graph__[node]

    def get_pre_nodes(self, node: Node):
        """
        Returns the nodes which are "above" the given node, i.e., have outgoing edges from the given
        node, empty if it is an input node

        :param node: Given node
        :return: List of nodes that have outgoing edges to the given node
        """
        return self.__pre_graph__[node]

    def get_pre_edges(self, node: Node):
        """
        Get the incoming edges to a specific node.

        :param node: Given node
        :return: Incoming edges for the node
        """
        pre_edges = []
        pre_nodes = self.__pre_graph__[node]
        # Empty pre
        if not pre_nodes:
            pre_edges.append(Edge(None, node))

        for pre_node in pre_nodes:
            pre_edges.append(Edge(pre_node, node))
        return pre_edges

    def get_post_edges(self, node: Node):
        """
        Get the outgoing edges for the given node

        :param node: Given node
        :return: Outgoing edges for the node
        """
        post_edges = []
        post_nodes = self.__post_graph__[node]
        # Empty post
        if not post_nodes:
            post_edges.append(Edge(node, None))

        for post_node in post_nodes:
            post_edges.append(Edge(node, post_node))
        return post_edges

    def is_output(self, node: Node):
        """
        Checks if the given node is an output node

        :param node: Given node
        :return: True if output else False
        """
        post_nodes = self.get_post_nodes(node)
        return not post_nodes

    def get_output_nodes(self):
        """
        Gets all the output nodes for this pipeline

        :return: List of output nodes
        """
        # dict from level to nodes
        terminal_nodes = []
        for node in self.__pre_graph__.keys():
            if self.is_output(node):
                terminal_nodes.append(node)
        return terminal_nodes

    def get_nodes(self):
        """
        Returns all the nodes of this pipeline in a dict from node_name to the node

        :return: Dict of node_name to node
        """
        return self.__node_name_map__

    def is_input(self, node: Node):
        """
        Checks if the given node is an input node of this pipeline

        :param node: Given node
        :return: True if input node else False
        """
        pre_nodes = self.get_pre_nodes(node)
        return not pre_nodes

    def get_input_nodes(self):
        """
        Returns all the input nodes of this pipeline

        :return: List of input nodes
        """
        input_nodes = []
        for node in self.__node_name_map__.values():
            if self.get_node_level(node) == 0:
                input_nodes.append(node)

        return input_nodes

    def get_node(self, node_name: str) -> Node:
        """
        Return the node given a node name

        :param node_name: Node name
        :return: The node with this node name
        """
        return self.__node_name_map__[node_name]

    def has_single_estimator(self):
        """
        Checks if this pipeline has only a single OR estimator, this is useful to know when picking a specific
        pipeline

        :return: True if only one OR estimator else False
        """
        if len(self.get_output_nodes()) > 1:
            return False

        for node in self.__node_name_map__.values():
            is_node_estimator = (node.get_node_input_type() == NodeInputType.OR)
            if is_node_estimator:
                pre_nodes = self.get_pre_nodes(node)
                if len(pre_nodes) > 1:
                    return False
        return True

    def save(self, filehandle):
        """
        Saves the pipeline graph (without state) to a file. A filehandle with write and binary mode
        is expected.

        :param filehandle: Filehandle with wb mode
        :return: None
        """
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

    def get_parameterized_pipeline(self, pipeline_param):
        """
        Parameterizes the current pipeline with the provided pipeline_param and returns the newly parameterized
        pipeline. The pipeline_param is explored for all the parameters associated with a given node, which is
        then expanded to multiple nodes with generated node names. The graph is created using the existing
        connections, i.e. if there is an edge between node A and node B and with parameterization node B became
        node B1, node B2, an edge is created between node A and node B1 as well as node A and node B2.

        Depending on the strategy of searches, the appropriate pipeline_param can create the right expansion.
        For example, grid search can expand the cross product of parameters and the pipeline will get expanded.

        Examples
        --------
        The below code shows an example of how a 2 step pipeline gets expanded to a 9 node pipeline for grid
        search.

        .. code-block:: python

            pipeline = dm.Pipeline()
            node_pca = dm.EstimatorNode('pca', pca)
            node_logistic = dm.EstimatorNode('logistic', logistic)

            pipeline.add_edge(node_pca, node_logistic)

            param_grid = {
                'pca__n_components': [5, 15, 30, 45, 64],
                'logistic__C': np.logspace(-4, 4, 4),
            }

            pipeline_param = dm.PipelineParam.from_param_grid(param_grid)

            param_grid_pipeline = pipeline.get_parameterized_pipeline(pipeline_param)

        :param pipeline_param: The pipeline parameters
        :return: A parameterized pipeline
        """
        result = Pipeline()
        pipeline_params = pipeline_param.get_all_params()
        parameterized_nodes = {}
        for node_name, params in pipeline_params.items():
            node_name_part, num = node_name.split('__', 1)
            if node_name_part not in parameterized_nodes.keys():
                parameterized_nodes[node_name_part] = []
            node = self.__node_name_map__[node_name_part]
            parameterized_node = node.get_parameterized_node(node_name, **params)
            parameterized_nodes[node_name_part].append(parameterized_node)

        # update parameterized nodes with missing non-parameterized nodes for completeness
        for node in self.__pre_graph__.keys():
            node_name = node.get_node_name()
            if node_name not in parameterized_nodes.keys():
                parameterized_nodes[node_name] = [node]

        # loop through the graph and add edges
        for node, pre_nodes in self.__pre_graph__.items():
            node_name = node.get_node_name()
            expanded_nodes = parameterized_nodes[node_name]
            for pre_node in pre_nodes:
                pre_node_name = pre_node.get_node_name()
                expanded_pre_nodes = parameterized_nodes[pre_node_name]
                for expanded_pre_node in expanded_pre_nodes:
                    for expanded_node in expanded_nodes:
                        result.add_edge(expanded_pre_node, expanded_node)

        return result

    @staticmethod
    def load(filehandle):
        """
        Loads a pipeline that has been saved given the filehandle. Filehandle is in rb format.

        :param filehandle: Filehandle to load pipeline from
        :return:
        """
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
    """
    Internal class that serializes the pipeline so that it can be pickled. As noted, this only captures
    the graph and not the state of the pipeline.
    """
    def __init__(self, nodes, edges):
        self.__nodes__ = nodes
        self.__edges__ = edges

    def get_nodes(self):
        """
        Nodes of the saved pipeline

        :return: Dict of node name to node mapping
        """
        return self.__nodes__

    def get_edges(self):
        """
        Edges of the saved pipeline

        :return: List of edges
        """
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

    def get_out_args(self):
        return self.__out_args__


class PipelineInput:
    """
    This is a holder to capture the input to the pipeline in an appropriate manner. Internally, it holds
    the input from a node to a pointer to XYref, i.e. it only holds pointers. It does not hold the entire
    data. This is key to distributing the data in the object store.

    Examples
    --------
    The simplest way to add input to a node is by specifying the X and y args, the underlying platform will
    take care of distributing it to the backend in-memory object storage.

    .. code-block:: python

        pipeline_input = dm.PipelineInput()
        pipeline_input.add_xy_arg(node_a, dm.Xy(X_train, y_train))
    """
    def __init__(self):
        self.__in_args__ = {}

    def add_xyref_ptr_arg(self, node: Node, xyref_ptr):
        """
        A direct pointer input addition, this is typically used in internal methods, but enables the advanecd
        developer to have direct access to the pipeline internals.

        :param node: Node to which input needs to be added
        :param xyref_ptr: The pointer to XYref
        :return: None
        """
        if node not in self.__in_args__:
            self.__in_args__[node] = []

        self.__in_args__[node].append(xyref_ptr)

    def add_xyref_arg(self, node: Node, xyref: XYRef):
        """
        A convenience method that adds a XYRef to the given node as input.

        :param node: Node to which input needs to be added
        :param xyref: The XYRef
        :return: None
        """
        if node not in self.__in_args__:
            self.__in_args__[node] = []

        xyref_ptr = ray.put(xyref)
        self.__in_args__[node].append(xyref_ptr)

    def add_xy_arg(self, node: Node, xy: Xy):
        """
        The most common way of adding input to a node, by providing a xy.

        :param node: Node to which input needs to be added
        :param xy: The xy to be added
        :return: None
        """
        if node not in self.__in_args__:
            self.__in_args__[node] = []

        x_ref = ray.put(xy.get_x())
        y_ref = ray.put(xy.get_y())
        xyref = XYRef(x_ref, y_ref)
        self.add_xyref_arg(node, xyref)

    def add_all(self, node, node_inargs):
        """
        Adds all the in args to a given node, this is very useful when cloning a pipeline or "morphing" it
        for grid search, etc.

        :param node: Node to which input needs to be added
        :param node_inargs: All the in args, which will be added whole
        :return: None
        """
        self.__in_args__[node] = node_inargs

    def get_in_args(self):
        """
        Returns the dict with the node to in args mapping

        :return: The internal structure holding the in args
        """
        return self.__in_args__

    def get_parameterized_input(self, pipeline: Pipeline, parameterized_pipeline: Pipeline):
        """
        This is meant to create a parameterized input given a pipeline and the parameterized pipeline.
        This method will explore the nodes from pipeline that are matching the parameterized_pipeline
        and copy the input over to the appropriate nodes of the parameterized_pipeline.

        :param pipeline: The original pipeline
        :param parameterized_pipeline: The parameterized pipeline corresponding to the original pipeline
        :return: The parameterized input for the given parameterized_pipeline
        """
        input_nodes = parameterized_pipeline.get_input_nodes()
        parameterized_pipeline_input = PipelineInput()
        for input_node in input_nodes:
            input_node_name = input_node.get_node_name()
            if '__' not in input_node_name:
                node_name = input_node_name
            else:
                node_name, param = input_node.get_node_name().split('__', 1)

            pipeline_node = pipeline.get_node(node_name)
            if pipeline_node in self.__in_args__:
                parameterized_pipeline_input.add_all(input_node, self.__in_args__[pipeline_node])
        return parameterized_pipeline_input


class PipelineParam:
    """
    This class captures the pipeline parameters, which can be changed for various forms of exploration.
    It is a fairly simple holder class capturing for each node, the corresponding estimators parameters
    as a dictionary.

    It also provides creating a PipelineParam object from a parameter grid, typically used in
    sklearn.GridSearchCV.

    Examples
    --------
    A simple example to create a pipeline param from a parameter grid.

    .. code-block:: python

        param_grid = {
            'pca__n_components': [5, 15, 30, 45, 64],
            'logistic__C': np.logspace(-4, 4, 4),
        }

        pipeline_param = dm.PipelineParam.from_param_grid(param_grid)
    """
    def __init__(self):
        self.__node_name_param_map__ = {}

    @staticmethod
    def from_param_grid(fit_params: dict):
        """
        A method to create a a pipeline param object from a typical parameter grid with the standard
        sklearn convention of __. For example, `pca__n_components` is a parameter for node name pca
        and the parameter name is n_components. The parameter grid creates a full grid exploration of
        the parameters.

        :param fit_params: Dictionary of parameter name in the sklearn convention to the parameter list
        :return: A pipeline param object
        """
        pipeline_param = PipelineParam()
        fit_params_nodes = {}
        for pname, pval in fit_params.items():
            if '__' not in pname:
                raise ValueError(
                    "Pipeline.fit does not accept the {} parameter. "
                    "You can pass parameters to specific steps of your "
                    "pipeline using the stepname__parameter format, e.g. "
                    "`Pipeline.fit(X, y, logisticregression__sample_weight"
                    "=sample_weight)`.".format(pname))
            node_name, param = pname.split('__', 1)
            if node_name not in fit_params_nodes.keys():
                fit_params_nodes[node_name] = {}

            fit_params_nodes[node_name][param] = pval

        # we have the split based on convention, now to create paramter grid for each node
        for node_name, param in fit_params_nodes.items():
            pg = ParameterGrid(param)
            pg_list = list(pg)
            for i in range(len(pg_list)):
                p = pg_list[i]
                curr_node_name = node_name + '__' + str(i)
                pipeline_param.add_param(curr_node_name, p)

        return pipeline_param

    def add_param(self, node_name: str, params: dict):
        """
        Add a parameter to the given node name

        :param node_name: Node name to add parameter to
        :param params: Parameter as a dictionary
        :return: None
        """
        self.__node_name_param_map__[node_name] = params

    def get_param(self, node_name: str):
        """
        Returns the parameter dict for the given node name

        :param node_name: Node name to retrieve parameters for
        :return: Dict of parameters
        """
        return self.__node_name_param_map__[node_name]

    def get_all_params(self):
        """
        Return all the parmaters for the given pipeline param

        :return: A dict from node name to the dictionary of parameters
        """
        return self.__node_name_param_map__
