import ray

import codeflare.pipelines.Datamodel as dm
import codeflare.pipelines.Exceptions as pe

import sklearn.base as base
from sklearn.model_selection import BaseCrossValidator
from enum import Enum

from queue import SimpleQueue


class ExecutionType(Enum):
    FIT = 0,
    PREDICT = 1,
    SCORE = 2


@ray.remote
def execute_or_node_remote(node: dm.EstimatorNode, mode: ExecutionType, xy_ref: dm.XYRef):
    estimator = node.get_estimator()
    # Blocking operation -- not avoidable
    X = ray.get(xy_ref.get_Xref())
    y = ray.get(xy_ref.get_yref())

    # TODO: Can optimize the node pointers without replicating them
    if mode == ExecutionType.FIT:
        cloned_node = node.clone()
        prev_node_ptr = ray.put(node)

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
            result = dm.XYRef(res_Xref, xy_ref.get_yref())
            return result
        else:
            res_Xref = ray.put(estimator.transform(X))
            result = dm.XYRef(res_Xref, xy_ref.get_yref())

            return result
    elif mode == ExecutionType.PREDICT:
        # Test mode does not clone as it is a simple predict or transform
        if base.is_classifier(estimator) or base.is_regressor(estimator):
            res_Xref = ray.put(estimator.predict(X))
            result = dm.XYRef(res_Xref, xy_ref.get_yref())
            return result
        else:
            res_Xref = ray.put(estimator.transform(X))
            result = dm.XYRef(res_Xref, xy_ref.get_yref())
            return result


def execute_or_node(node, pre_edges, edge_args, post_edges, mode: ExecutionType):
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
def execute_and_node_remote(node: dm.AndNode, Xyref_list):
    xy_list = []
    prev_node_ptr = ray.put(node)
    for Xyref in Xyref_list:
        X = ray.get(Xyref.get_Xref())
        y = ray.get(Xyref.get_yref())
        xy_list.append(dm.Xy(X, y))

    cloned_node = node.clone()
    curr_node_ptr = ray.put(cloned_node)

    cloned_and_func = cloned_node.get_and_func()
    res_Xy = cloned_and_func.transform(xy_list)
    res_Xref = ray.put(res_Xy.get_x())
    res_yref = ray.put(res_Xy.get_y())
    return dm.XYRef(res_Xref, res_yref, prev_node_ptr, curr_node_ptr, Xyref_list)


def execute_and_node_inner(node: dm.AndNode, Xyref_ptrs):
    result = []

    Xyref_list = []
    for Xyref_ptr in Xyref_ptrs:
        Xyref = ray.get(Xyref_ptr)
        Xyref_list.append(Xyref)

    Xyref_ptr = execute_and_node_remote.remote(node, Xyref_list)
    result.append(Xyref_ptr)
    return result


def execute_and_node(node, pre_edges, edge_args, post_edges):
    edge_args_lists = list()
    for pre_edge in pre_edges:
        edge_args_lists.append(edge_args[pre_edge])

    # cross product using itertools
    import itertools
    cross_product = itertools.product(*edge_args_lists)

    for element in cross_product:
        exec_xyref_ptrs = execute_and_node_inner(node, element)
        for post_edge in post_edges:
            if post_edge not in edge_args.keys():
                edge_args[post_edge] = []
            edge_args[post_edge].extend(exec_xyref_ptrs)


def execute_pipeline(pipeline: dm.Pipeline, mode: ExecutionType, pipeline_input: dm.PipelineInput) -> dm.PipelineOutput:
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
                execute_and_node(node, pre_edges, edge_args, post_edges)

    out_args = {}
    terminal_nodes = pipeline.get_output_nodes()
    for terminal_node in terminal_nodes:
        edge = dm.Edge(terminal_node, None)
        out_args[terminal_node] = edge_args[edge]

    return dm.PipelineOutput(out_args, edge_args)


def select_pipeline(pipeline_output: dm.PipelineOutput, chosen_xyref: dm.XYRef):
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


def get_pipeline_input(pipeline: dm.Pipeline, pipeline_output: dm.PipelineOutput, chosen_xyref: dm.XYRef):
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
    x = ray.get(xy_ref.get_Xref())
    y = ray.get(xy_ref.get_yref())

    xy_train_refs = []
    xy_test_refs = []

    for train_index, test_index in cross_validator.split(x, y):
        x_train, x_test = x[train_index], x[test_index]
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
    pipeline_input_train = dm.PipelineInput()

    pipeline_input_test = []
    k = cross_validator.get_n_splits()
    # add k pipeline inputs for testing
    for i in range(k):
        pipeline_input_test.append(dm.PipelineInput())

    in_args = pipeline_input.get_in_args()
    for node, xyref_ptrs in in_args.items():
        # NOTE: The assumption is that this node has only one input!
        xyref_ptr = xyref_ptrs[0]
        xy_train_refs_ptr, xy_test_refs_ptr = split.remote(cross_validator, xyref_ptr)
        xy_train_refs = ray.get(xy_train_refs_ptr)
        xy_test_refs = ray.get(xy_test_refs_ptr)

        for xy_train_ref in xy_train_refs:
            pipeline_input_train.add_xyref_arg(node, xy_train_ref)

        # for testing, add only to the specific input
        for i in range(k):
            pipeline_input_test[i].add_xyref_arg(node, xy_test_refs[i])

    # Ready for execution now that data has been prepared! This execution happens in parallel
    # because of the underlying pipeline graph and multiple input objects
    pipeline_output_train = execute_pipeline(pipeline, ExecutionType.FIT, pipeline_input_train)

    # Now we can choose the pipeline and then score for each of the chosen pipelines
    out_nodes = pipeline.get_output_nodes()
    if len(out_nodes) > 1:
        raise pe.PipelineException("Cannot cross validate as output is not a single node")

    out_node = out_nodes[0]
    out_xyref_ptrs = pipeline_output_train.get_xyrefs(out_node)

    k = cross_validator.get_n_splits()
    if len(out_xyref_ptrs) != k:
        raise pe.PipelineException("Number of outputs from pipeline fit is not equal to the folds from cross validator")

    pipeline_score_outputs = []
    # Below, jobs get submitted and then we can collect the results in the next loop
    for i in range(k):
        selected_pipeline = select_pipeline(pipeline_output_train, out_xyref_ptrs[i])
        selected_pipeline_output = execute_pipeline(selected_pipeline, ExecutionType.SCORE, pipeline_input_test[i])
        pipeline_score_outputs.append(selected_pipeline_output)

    result_scores = []
    for pipeline_score_output in pipeline_score_outputs:
        pipeline_out_xyrefs = pipeline_score_output.get_xyrefs(out_node)
        # again, only single xyref to be gotten out
        pipeline_out_xyref = pipeline_out_xyrefs[0]
        out_x = ray.get(pipeline_out_xyref.get_Xref())
        result_scores.append(out_x)

    return result_scores


def grid_search(cross_validator: BaseCrossValidator, pipeline: dm.Pipeline, pipeline_input: dm.PipelineInput):
    pipeline_input_train = dm.PipelineInput()

    pipeline_input_test = []
    k = cross_validator.get_n_splits()
    # add k pipeline inputs for testing
    for i in range(k):
        pipeline_input_test.append(dm.PipelineInput())

    in_args = pipeline_input.get_in_args()
    for node, xyref_ptrs in in_args.items():
        # NOTE: The assumption is that this node has only one input!
        xyref_ptr = xyref_ptrs[0]
        if len(xyref_ptrs) > 1:
            raise pe.PipelineException("Input to grid search is multiple objects, re-run with only single object")

        xy_train_refs_ptr, xy_test_refs_ptr = split.remote(cross_validator, xyref_ptr)
        xy_train_refs = ray.get(xy_train_refs_ptr)
        xy_test_refs = ray.get(xy_test_refs_ptr)

        for xy_train_ref in xy_train_refs:
            pipeline_input_train.add_xyref_arg(node, xy_train_ref)

        # for testing, add only to the specific input
        for i in range(k):
            pipeline_input_test[i].add_xyref_arg(node, xy_test_refs[i])

    # Ready for execution now that data has been prepared! This execution happens in parallel
    # because of the underlying pipeline graph and multiple input objects
    pipeline_output_train = execute_pipeline(pipeline, ExecutionType.FIT, pipeline_input_train)

    # For grid search, we will have multiple output nodes that need to be iterated on and select the pipeline
    # that is "best"
    out_nodes = pipeline.get_output_nodes()


def save(pipeline_output: dm.PipelineOutput, xy_ref: dm.XYRef, filehandle):
    pipeline = select_pipeline(pipeline_output, xy_ref)
    pipeline.save(filehandle)