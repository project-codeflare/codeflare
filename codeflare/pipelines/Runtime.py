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

"""codeflare.pipelines.Runtime
This class is the core runtime for CodeFlare pipelines. It provides the entry point for execution of the
pipeline that was constructed from codeflare.pipelines.Datamodel. The key entry point is the basic
execute_pipeline, with other enhanced entry points such as cross_validate and grid_search_cv.

The other methods provide supporting functions for execution of pipeline primitives. In addition to this,
methods for selecting a pipeline are provided as well as saving a specific pipeline instance along with
that pipeline's state.

Details on the execution and parallelism exposed are provided in the design documentation.
"""

import ray

import codeflare.pipelines.Datamodel as dm
import codeflare.pipelines.Exceptions as pe

import sklearn.base as base
from sklearn.model_selection import BaseCrossValidator
from enum import Enum

from queue import SimpleQueue
import pandas as pd


class ExecutionType(Enum):
    """
    Pipelines can be executed in different modes, this is targeting the typical AI/ML parlance, with the supported
    types being FIT for training a pipeline, PREDICT for predicting/transforming on the steps of a pipeline, and finally
    SCORE, which scores against a given input.
    """
    FIT = 0,
    PREDICT = 1,
    SCORE = 2


@ray.remote
def execute_or_node_remote(node: dm.EstimatorNode, mode: ExecutionType, xy_ref: dm.XYRef):
    """
    Helper remote function that executes an OR node. As such, this is a remote task that runs the estimator
    in the provided mode with the data pointed to by XYRef. The key aspect to note here is the choice of input
    to be a pointer to data and not the data itself. This enables the access to the data to be delayed until
    it is absolutely necessary. The remote method further returns a pointer to XYref, which in itself is a pointer
    to the data. This again enables the execution to proceed in an asynchronous manner.

    In the FIT mode, the node is always cloned along with its estimator, hence the pipeline state is always
    kept in the "cloned" node.

    :param node: Estimator node whose estimator needs to be executed
    :param mode: The mode of execution
    :param xy_ref: Pointer to the data
    :return: A list of pointers to XYRefs
    """
    estimator = node.get_estimator()
    # Blocking operation -- not avoidable
    X = ray.get(xy_ref.get_Xref())
    y = ray.get(xy_ref.get_yref())
    prev_node_ptr = ray.put(node)

    # TODO: Can optimize the node pointers without replicating them
    if mode == ExecutionType.FIT:
        cloned_node = node.clone()

        if base.is_classifier(estimator) or base.is_regressor(estimator):
            # Always clone before fit, else fit is invalid
            cloned_estimator = cloned_node.get_estimator()
            cloned_estimator.fit(X, y)

            curr_node_ptr = ray.put(cloned_node)
            # TODO: For now, make yref passthrough - this has to be fixed more comprehensively
            res_Xref = ray.put(cloned_estimator.predict(X))
            result = dm.XYRef(res_Xref, xy_ref.get_yref(), prev_node_ptr, curr_node_ptr, [xy_ref])
            return result
        else:
            cloned_estimator = cloned_node.get_estimator()
            res_Xref = ray.put(cloned_estimator.fit_transform(X, y))
            curr_node_ptr = ray.put(cloned_node)
            result = dm.XYRef(res_Xref, xy_ref.get_yref(), prev_node_ptr, curr_node_ptr, [xy_ref])
            return result
    elif mode == ExecutionType.SCORE:
        if base.is_classifier(estimator) or base.is_regressor(estimator):
            estimator = node.get_estimator()
            res_Xref = ray.put(estimator.score(X, y))
            result = dm.XYRef(res_Xref, xy_ref.get_yref(), prev_node_ptr, prev_node_ptr, [xy_ref])
            return result
        else:
            res_Xref = ray.put(estimator.transform(X))
            result = dm.XYRef(res_Xref, xy_ref.get_yref(), prev_node_ptr, prev_node_ptr, [xy_ref])

            return result
    elif mode == ExecutionType.PREDICT:
        # Test mode does not clone as it is a simple predict or transform
        if base.is_classifier(estimator) or base.is_regressor(estimator):
            res_Xref = ray.put(estimator.predict(X))
            result = dm.XYRef(res_Xref, xy_ref.get_yref(), prev_node_ptr, prev_node_ptr, [xy_ref])
            return result
        else:
            res_Xref = ray.put(estimator.transform(X))
            result = dm.XYRef(res_Xref, xy_ref.get_yref(), prev_node_ptr, prev_node_ptr, [xy_ref])
            return result


def execute_or_node(node, pre_edges, edge_args, post_edges, mode: ExecutionType):
    """
    Inner method that executes the estimator node parallelizing at the level of input objects. This defines the
    strategy of execution of the node, in this case, parallel for each object that is input. The function takes
    in the edges coming to this node (pre_edges) and the associated arguments (edge_args) and fires off remote
    tasks for each of the objects (this is defined by the ANY firing semantics). The resulting pointer(s) are then
    captured and passed to the post_edges.

    :param node: Node to execute
    :param pre_edges: Input edges to the given node
    :param edge_args: Data arguments for the edges
    :param post_edges: Data arguments for downstream processing
    :param mode: Execution mode
    :return: None
    """
    for pre_edge in pre_edges:
        Xyref_ptrs = edge_args[pre_edge]
        exec_xyrefs = []
        for xy_ref_ptr in Xyref_ptrs:
            xy_ref = ray.get(xy_ref_ptr)
            inner_result = execute_or_node_remote.remote(node, mode, xy_ref)
            exec_xyrefs.append(inner_result)

        for post_edge in post_edges:
            if post_edge not in edge_args.keys():
                edge_args[post_edge] = []
            edge_args[post_edge].extend(exec_xyrefs)


@ray.remote
def execute_and_node_remote(node: dm.AndNode, mode: ExecutionType, Xyref_list):
    """
    Similar to the estimator node (OR node), this is the remote function that executes the AND node. The key to
    note here is that the input to execute on is a list of XYRefs as opposed to a single XYRef, which differentiates
    the type of nodes. Similar to the OR node, the output is again a pointer to a list of XYRefs.

    The execution mode is FIT for training, PREDICT for predicting/transforming, and SCORE for scoring.

    :param node: Node to execute
    :param mode: Mode of execution
    :param Xyref_list: Input list of XYrefs
    :return: Output as list of XYrefs
    """
    xy_list = []
    prev_node_ptr = ray.put(node)
    for Xyref in Xyref_list:
        X = ray.get(Xyref.get_Xref())
        y = ray.get(Xyref.get_yref())
        xy_list.append(dm.Xy(X, y))

    estimator = node.get_estimator()

    # TODO: Can optimize the node pointers without replicating them
    if mode == ExecutionType.FIT:
        cloned_node = node.clone()

        if base.is_classifier(estimator) or base.is_regressor(estimator):
            # Always clone before fit, else fit is invalid
            cloned_estimator = cloned_node.get_estimator()
            cloned_estimator.fit(xy_list)

            curr_node_ptr = ray.put(cloned_node)
            res_xy = cloned_estimator.predict(xy_list)
            res_xref = ray.put(res_xy.get_x())
            res_yref = ray.put(res_xy.get_y())

            result = dm.XYRef(res_xref, res_yref, prev_node_ptr, curr_node_ptr, Xyref_list)
            return result
        else:
            cloned_estimator = cloned_node.get_estimator()
            res_xy = cloned_estimator.fit_transform(xy_list)
            res_xref = ray.put(res_xy.get_x())
            res_yref = ray.put(res_xy.get_y())

            curr_node_ptr = ray.put(cloned_node)
            result = dm.XYRef(res_xref, res_yref, prev_node_ptr, curr_node_ptr, Xyref_list)
            return result
    elif mode == ExecutionType.SCORE:
        if base.is_classifier(estimator) or base.is_regressor(estimator):
            estimator = node.get_estimator()
            res_xy = estimator.score(xy_list)
            res_xref = ray.put(res_xy.get_x())
            res_yref = ray.put(res_xy.get_y())

            result = dm.XYRef(res_xref, res_yref, prev_node_ptr, prev_node_ptr, Xyref_list)
            return result
        else:
            res_xy = estimator.transform(xy_list)
            res_xref = ray.put(res_xy.get_x())
            res_yref = ray.put(res_xy.get_y())
            result = dm.XYRef(res_xref, res_yref, prev_node_ptr, prev_node_ptr, Xyref_list)

            return result
    elif mode == ExecutionType.PREDICT:
        # Test mode does not clone as it is a simple predict or transform
        if base.is_classifier(estimator) or base.is_regressor(estimator):
            res_xy = estimator.predict(xy_list)
            res_xref = ray.put(res_xy.get_x())
            res_yref = ray.put(res_xy.get_y())

            result = dm.XYRef(res_xref, res_yref, prev_node_ptr, prev_node_ptr, Xyref_list)
            return result
        else:
            res_xy = estimator.transform(xy_list)
            res_xref = ray.put(res_xy.get_x())
            res_yref = ray.put(res_xy.get_y())
            result = dm.XYRef(res_xref, res_yref, prev_node_ptr, prev_node_ptr, Xyref_list)
            return result


def execute_and_node_inner(node: dm.AndNode, mode: ExecutionType, Xyref_ptrs):
    """
    This is a helper method for executing and nodes, which fires off remote tasks. Unlike the helper
    for OR nodes, which can fire off on single objects, this method retrieves the list of inputs,
    unmarshals the pointers to XYrefs to materialize XYRef and then passes it along to the and node
    remote executor.

    :param node: Node to execute on
    :param mode: Mode of execution
    :param Xyref_ptrs: Object ref pointers for data input
    :return:
    """
    result = []

    Xyref_list = []
    for Xyref_ptr in Xyref_ptrs:
        Xyref = ray.get(Xyref_ptr)
        Xyref_list.append(Xyref)

    Xyref_ptr = execute_and_node_remote.remote(node, mode, Xyref_list)
    result.append(Xyref_ptr)
    return result


def execute_and_node(node, pre_edges, edge_args, post_edges, mode: ExecutionType):
    """
    Inner method that executes an and node by combining the inputs coming from multiple edges. Unlike the OR
    node, which only executes a remote task per input object, the and node combines input from across all the
    edges. For example, if there are two edges incoming to this node with two objects each, the combiner will
    create four input combinations. Each of these input combinations is then evaluated by the AND node in
    parallel.

    The result is then sent to the edges outgoing from this node.

    :param node: Node to execute on
    :param pre_edges: Incoming edges to this node
    :param edge_args: Data arguments for each of this edge
    :param post_edges: Outgoing edges
    :param mode: Execution mode
    :return: None
    """
    edge_args_lists = list()
    for pre_edge in pre_edges:
        edge_args_lists.append(edge_args[pre_edge])

    # cross product using itertools
    import itertools
    cross_product = itertools.product(*edge_args_lists)

    for element in cross_product:
        exec_xyref_ptrs = execute_and_node_inner(node, mode, element)
        for post_edge in post_edges:
            if post_edge not in edge_args.keys():
                edge_args[post_edge] = []
            edge_args[post_edge].extend(exec_xyref_ptrs)


def execute_pipeline(pipeline: dm.Pipeline, mode: ExecutionType, pipeline_input: dm.PipelineInput) -> dm.PipelineOutput:
    """
    The entry point for a basic pipeline execution. This method takes a pipeline, the input to it and the execution
    mode and runs the pipeline. Based on the parallelism defined by the DAG structure and the input data, the execution
    of the pipeline will happen in parallel.

    In the FIT mode of execution, the pipeline can materialize into several pipelines which can be examined in further
    detail based on metrics of interest. The method select_pipeline enables selecting a specific pipeline to examine
    further.

    A selected pipeline can be executed in SCORE and PREDICT modes for evaluating the results or saving them for future
    reuse.

    Examples
    --------
    Execution of pipeline is fairly simple and getting the output can be done:

    .. code-block:: python

        pipeline_output = rt.execute_pipeline(pipeline, rt.ExecutionType.FIT, pipeline_input)
        node_rf_xyrefs = pipeline_output.get_xyrefs(node_rf)

    :param pipeline: Abstract DAG representation of the pipeline
    :param mode: Execution mode
    :param pipeline_input: The input to this pipeline
    :return: Pipeline output
    """
    nodes_by_level = pipeline.get_nodes_by_level()

    # track args per edge
    edge_args = {}
    in_args = pipeline_input.get_in_args()
    for node, node_in_args in in_args.items():
        pre_edges = pipeline.get_pre_edges(node)
        for pre_edge in pre_edges:
            edge_args[pre_edge] = node_in_args

    for level in range(len(nodes_by_level)):
        nodes = nodes_by_level[level]
        for node in nodes:
            pre_edges = pipeline.get_pre_edges(node)
            post_edges = pipeline.get_post_edges(node)
            if node.get_node_input_type() == dm.NodeInputType.OR:
                execute_or_node(node, pre_edges, edge_args, post_edges, mode)
            elif node.get_node_input_type() == dm.NodeInputType.AND:
                execute_and_node(node, pre_edges, edge_args, post_edges, mode)

    out_args = {}
    terminal_nodes = pipeline.get_output_nodes()
    for terminal_node in terminal_nodes:
        edge = dm.Edge(terminal_node, None)
        out_args[terminal_node] = edge_args[edge]

    return dm.PipelineOutput(out_args, edge_args)


def select_pipeline(pipeline_output: dm.PipelineOutput, chosen_xyref: dm.XYRef) -> dm.Pipeline:
    """
    Pipeline execution results in a materialization of several pipelines, this entry point method enables the end
    user to select a specific pipeline to examine in further detail. Typical way of examining a pipeline is to select
    a specific output and then "request" which pipeline generated it.

    Internally, the runtime has generated "trackers" to keep a lineage for every input and output and which node
    generated it. These are then selected to create the appropriate pipeline that can be scored, predicted, and saved.

    Examples
    --------
    Selecting a pipeline can be done by identifying an output object of interest. One can select the pipeline without
    going to the output node, i.e. looking at some internal nodes as well

    .. code-block:: python

        # one can examine the output in more detail and select a pipeline of interest
        selected_pipeline = rt.select_pipeline(pipeline_output, node_rf_xyrefs[0])

    :param pipeline_output: Pipeline output from execute pipeline
    :param chosen_xyref: The XYref for which the pipeline needs to be selected
    :return: Selected pipeline
    """
    pipeline = dm.Pipeline()
    xyref_queue = SimpleQueue()

    xyref_queue.put(chosen_xyref)
    while not xyref_queue.empty():
        curr_xyref = xyref_queue.get()
        curr_node_state_ptr = curr_xyref.get_curr_node_state_ref()
        curr_node = ray.get(curr_node_state_ptr)
        prev_xyrefs = curr_xyref.get_prev_xyrefs()

        # TODO: Avoid redundant gets from Plasma
        for prev_xyref in prev_xyrefs:
            prev_node_state_ptr = prev_xyref.get_curr_node_state_ref()
            if prev_node_state_ptr is None:
                continue
            prev_node = ray.get(prev_node_state_ptr)
            pipeline.add_edge(prev_node, curr_node)
            xyref_queue.put(prev_xyref)

    return pipeline


def get_pipeline_input(pipeline: dm.Pipeline, pipeline_output: dm.PipelineOutput, chosen_xyref: dm.XYRef) -> dm.PipelineInput:
    """
    Given the output from a pipeline and a chosen output object, this method gets the inputs that were used to
    generate this output. Combining the input and the selected pipeline, one can then actually recreate the full
    provenance -- graph and data to execute the selected pipeline.

    Note that once the persistence of objects in memory or other persistent stores is lost, it is not possible to
    get the data.

    :param pipeline: Executed pipeline
    :param pipeline_output: Output from the executed pipeline
    :param chosen_xyref: Chosen object from the output
    :return: The pipeline input (for the given chosen object)
    """
    pipeline_input = dm.PipelineInput()

    xyref_queue = SimpleQueue()
    xyref_queue.put(chosen_xyref)
    while not xyref_queue.empty():
        curr_xyref = xyref_queue.get()
        curr_node_state_ptr = curr_xyref.get_curr_node_state_ref()
        curr_node = ray.get(curr_node_state_ptr)
        curr_node_level = pipeline.get_node_level(curr_node)
        prev_xyrefs = curr_xyref.get_prev_xyrefs()

        if curr_node_level == 0:
            # This is an input node
            for prev_xyref in prev_xyrefs:
                pipeline_input.add_xyref_arg(curr_node, prev_xyref)

        for prev_xyref in prev_xyrefs:
            prev_node_state_ptr = prev_xyref.get_curr_node_state_ref()
            if prev_node_state_ptr is None:
                continue
            xyref_queue.put(prev_xyref)

    return pipeline_input


@ray.remote(num_returns=2)
def split(cross_validator: BaseCrossValidator, xy_ref):
    """
    A remote function that splits the data based on the provided cross validator. This allows for remote
    data to be split without having to "collect" the data to a driver.

    :param cross_validator: Cross validator
    :param xy_ref: XYRef that needs to be split
    :return: List of train and test XYRefs, the number determined by the cross validator get_n_splits
    """
    x = ray.get(xy_ref.get_Xref())
    y = ray.get(xy_ref.get_yref())

    xy_train_refs = []
    xy_test_refs = []

    for train_index, test_index in cross_validator.split(x, y):
        if isinstance(x, pd.DataFrame) or isinstance(x, pd.Series):
            x_train, x_test = x.iloc[train_index], x.iloc[test_index]
        else:
            x_train, x_test = x[train_index], x[test_index]

        if isinstance(y, pd.DataFrame) or isinstance(y, pd.Series):
            y_train, y_test = y.iloc[train_index], y.iloc[test_index]
        else:
            y_train, y_test = y[train_index], y[test_index]

        x_train_ref = ray.put(x_train)
        y_train_ref = ray.put(y_train)
        xy_train_ref = dm.XYRef(x_train_ref, y_train_ref)
        xy_train_refs.append(xy_train_ref)

        x_test_ref = ray.put(x_test)
        y_test_ref = ray.put(y_test)
        xy_test_ref = dm.XYRef(x_test_ref, y_test_ref)
        xy_test_refs.append(xy_test_ref)

    return xy_train_refs, xy_test_refs


def cross_validate(cross_validator: BaseCrossValidator, pipeline: dm.Pipeline, pipeline_input: dm.PipelineInput):
    """
    Similar to sklearn cross validate, but a parallelized version on Ray with zero copy sharing of data. This method
    allows for the user to explore a pipeline with a single input object to be explored by cross validation. The output
    is a list of scores that correspond to the SCORE mode of the pipeline execution.

    Examples
    --------
    Cross validation is quite simple:

    .. code-block:: python

        kf = StratifiedKFold(n_splits=10)
        scores = rt.cross_validate(kf, pipeline, pipeline_input)

    :param cross_validator: Cross validator to use
    :param pipeline: Pipeline to execute
    :param pipeline_input: Input to the pipeline
    :return: Scored outputs from the pipeline
    """
    has_single_estimator = pipeline.has_single_estimator()
    if not has_single_estimator:
        raise pe.PipelineException("Cross validation can only be done on pipelines with single estimator, "
                                   "use grid_search_cv instead")

    result_grid_search_cv = _grid_search_cv(cross_validator, pipeline, pipeline_input)
    # only one output here
    result_scores = None
    for scores in result_grid_search_cv.values():
        result_scores = scores
        break

    return result_scores


def grid_search_cv(cross_validator: BaseCrossValidator, pipeline: dm.Pipeline, pipeline_input: dm.PipelineInput, pipeline_params: dm.PipelineParam):
    """
    A top-level method that does a grid search with cross validation. This method takes pipeline, the input to it,
    a set of parameters for the pipeline, and a cross validator similar to the traditional GridSearchCV of sklearn
    and executes the various pipelines and cross validation in parallel.

    This method will first transform the input pipeline and expand it to perform a parameter grid search and then
    the cross validator is run in parallel. The goal is to execute each of the cross validation for each of the
    parameter combination in parallel to provide the results.

    The results are captured in a dict that maps each pipeline to its corresponding cross validation scores.

    Examples
    --------
    An example of grid search using a parameter grid similar to what SKLearn does:

    .. code-block:: python

        k = 2
        kf = KFold(k)
        result = rt._grid_search_cv(kf, pipeline, pipeline_input)

        # Results can be examined by iterating over the pipeline, for example to pick a best pipeline based
        # on mean scores
        best_pipeline = None
        best_mean_scores = 0.0

        for cv_pipeline, scores in result.items():
            mean = statistics.mean(scores)
            if mean > best_mean_scores:
                best_pipeline = cv_pipeline
                best_mean_scores = mean

    :param cross_validator: Cross validator for grid search
    :param pipeline: Pipeline graph
    :param pipeline_input: Input to the pipeline
    :param pipeline_params: Parameter space to explore using a grid search approach
    :return: Dict from pipeline to the cross validation scores
    """
    parameterized_pipeline = pipeline.get_parameterized_pipeline(pipeline_params)
    parameterized_pipeline_input = pipeline_input.get_parameterized_input(pipeline, parameterized_pipeline)
    return _grid_search_cv(cross_validator, parameterized_pipeline, parameterized_pipeline_input)


def _grid_search_cv(cross_validator: BaseCrossValidator, pipeline: dm.Pipeline, pipeline_input: dm.PipelineInput):
    """
    Internal helper method to do a grid search CV on the "expanded" pipeline. This method does not expand the
    input parameters and simply executes a grid search with a cross validator. The key is to explore the
    various pipelines in parallel and then provide the lineage from the output for each pipeline that was
    explored.

    :param cross_validator: Cross validator
    :param pipeline: Pipeline graph
    :param pipeline_input: Pipeline input
    :return: Dict from pipeline to the resulting cross validation scores
    """
    pipeline_input_train = dm.PipelineInput()

    pipeline_input_test = []
    k = cross_validator.get_n_splits()
    # add k pipeline inputs for testing
    for i in range(k):
        pipeline_input_test.append(dm.PipelineInput())

    in_args = pipeline_input.get_in_args()
    # Keep a map from the pointer of train to test
    train_test_mapper = {}

    for node, xyref_ptrs in in_args.items():
        # NOTE: The assumption is that this node has only one input!
        xyref_ptr = xyref_ptrs[0]
        if len(xyref_ptrs) > 1:
            raise pe.PipelineException("Grid search supports single object input only, multiple provided, number is " + str(len(xyref_ptrs)))

        xy_train_refs_ptr, xy_test_refs_ptr = split.remote(cross_validator, xyref_ptr)
        xy_train_refs = ray.get(xy_train_refs_ptr)
        xy_test_refs = ray.get(xy_test_refs_ptr)

        for i in range(len(xy_train_refs)):
            xy_train_ref = xy_train_refs[i]
            xy_test_ref = xy_test_refs[i]
            pipeline_input_train.add_xyref_arg(node, xy_train_ref)
            train_test_mapper[xy_train_ref] = xy_test_ref

        # for testing, add only to the specific input
        for i in range(k):
            pipeline_input_test[i].add_xyref_arg(node, xy_test_refs[i])

    # Ready for execution now that data has been prepared! This execution happens in parallel
    # because of the underlying pipeline graph and multiple input objects
    pipeline_output_train = execute_pipeline(pipeline, ExecutionType.FIT, pipeline_input_train)

    # For grid search, we will have multiple output nodes that need to be iterated on
    selected_pipeline_test_outputs = {}
    out_nodes = pipeline.get_output_nodes()
    for out_node in out_nodes:
        out_node_xyrefs = pipeline_output_train.get_xyrefs(out_node)
        for out_node_xyref in out_node_xyrefs:
            selected_pipeline = select_pipeline(pipeline_output_train, out_node_xyref)
            selected_pipeline_input = get_pipeline_input(pipeline, pipeline_output_train, out_node_xyref)
            selected_pipeline_inargs = selected_pipeline_input.get_in_args()
            test_pipeline_input = dm.PipelineInput()
            for node, train_xyref_ptr in selected_pipeline_inargs.items():
                # xyrefs is a singleton by construction
                train_xyrefs = ray.get(train_xyref_ptr)
                test_xyref = train_test_mapper[train_xyrefs[0]]
                test_pipeline_input.add_xyref_arg(node, test_xyref)
            selected_pipeline_test_output = execute_pipeline(selected_pipeline, ExecutionType.SCORE, test_pipeline_input)
            if selected_pipeline not in selected_pipeline_test_outputs.keys():
                selected_pipeline_test_outputs[selected_pipeline] = []
            selected_pipeline_test_outputs[selected_pipeline].append(selected_pipeline_test_output)

    # now, test outputs can be materialized
    result_scores = {}
    for selected_pipeline, selected_pipeline_test_output_list in selected_pipeline_test_outputs.items():
        output_nodes = selected_pipeline.get_output_nodes()
        # by design, output_nodes will only have one node
        output_node = output_nodes[0]
        for selected_pipeline_test_output in selected_pipeline_test_output_list:
            pipeline_out_xyrefs = selected_pipeline_test_output.get_xyrefs(output_node)
            # again, only single xyref to be gotten out
            pipeline_out_xyref = pipeline_out_xyrefs[0]
            out_x = ray.get(pipeline_out_xyref.get_Xref())
            if selected_pipeline not in result_scores.keys():
                result_scores[selected_pipeline] = []
            result_scores[selected_pipeline].append(out_x)

    return result_scores


def save(pipeline_output: dm.PipelineOutput, xy_ref: dm.XYRef, filehandle):
    """
    Saves a selected pipeline, i.e. this selected pipeline will save the state of the estimators enabling for the
    end user to load and execute the pipeline in SCORE/PREDICT modes in the future.

    Examples
    --------
    Saving a selected pipeline can be done as follows:

    .. code-block:: python

        # this pipeline can also be saved
        fname = 'random_forest.cfp'
        w_fh = open(fname, 'wb')
        rt.save(pipeline_output, node_rf_xyrefs[0], w_fh)
        w_fh.close()

    :param pipeline_output: Pipeline output from an executed pipeline
    :param xy_ref: The chosen XYRef that will be used to materialize a selected pipeline
    :param filehandle: The file handle to save this pipeline to
    :return: None
    """
    pipeline = select_pipeline(pipeline_output, xy_ref)
    pipeline.save(filehandle)