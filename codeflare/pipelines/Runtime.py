import ray

import codeflare.pipelines.Datamodel as dm
import codeflare.pipelines.Exceptions as pe

import sklearn.base as base
from enum import Enum

from queue import SimpleQueue


class ExecutionType(Enum):
    FIT = 0,
    PREDICT = 1,
    SCORE = 2


@ray.remote
def execute_or_node_remote(node: dm.EstimatorNode, train_mode: ExecutionType, xy_ref: dm.XYRef):
    estimator = node.get_estimator()
    # Blocking operation -- not avoidable
    X = ray.get(xy_ref.get_Xref())
    y = ray.get(xy_ref.get_yref())

    # TODO: Can optimize the node pointers without replicating them
    if train_mode == ExecutionType.FIT:
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
    elif train_mode == ExecutionType.SCORE:
        cloned_node = node.clone()
        prev_node_ptr = ray.put(node)

        if base.is_classifier(estimator) or base.is_regressor(estimator):
            cloned_estimator = cloned_node.get_estimator()
            cloned_estimator.fit(X, y)
            curr_node_ptr = ray.put(cloned_node)
            res_Xref = ray.put(cloned_estimator.score(X, y))
            result = dm.XYRef(res_Xref, xy_ref.get_yref(), prev_node_ptr, curr_node_ptr, [xy_ref])
            return result
        else:
            cloned_estimator = cloned_node.get_estimator()
            res_Xref = ray.put(cloned_estimator.fit_transform(X, y))
            curr_node_ptr = ray.put(cloned_node)
            result = dm.XYRef(res_Xref, xy_ref.get_yref(), prev_node_ptr, curr_node_ptr, [xy_ref])
            return result
    elif train_mode == ExecutionType.PREDICT:
        # Test mode does not clone as it is a simple predict or transform
        if base.is_classifier(estimator) or base.is_regressor(estimator):
            res_Xref = estimator.predict(X)
            result = dm.XYRef(res_Xref, xy_ref.get_yref())
            return result
        else:
            res_Xref = estimator.transform(X)
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


def execute_pipeline(pipeline: dm.Pipeline, mode: ExecutionType, in_args: dict):
    nodes_by_level = pipeline.get_nodes_by_level()

    # track args per edge
    edge_args = {}
    for node, node_in_args in in_args.items():
        pre_edges = pipeline.get_pre_edges(node)
        for pre_edge in pre_edges:
            edge_args[pre_edge] = node_in_args

    for nodes in nodes_by_level:
        for node in nodes:
            pre_edges = pipeline.get_pre_edges(node)
            post_edges = pipeline.get_post_edges(node)
            if node.get_node_input_type() == dm.NodeInputType.OR:
                execute_or_node(node, pre_edges, edge_args, post_edges, mode)
            elif node.get_node_input_type() == dm.NodeInputType.AND:
                execute_and_node(node, pre_edges, edge_args, post_edges)

    out_args = {}
    last_level_nodes = nodes_by_level[pipeline.compute_max_level()]
    for last_level_node in last_level_nodes:
        edge = dm.Edge(last_level_node, None)
        out_args[last_level_node] = edge_args[edge]

    return out_args


def select_pipeline(chosen_xyref: dm.XYRef):
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
