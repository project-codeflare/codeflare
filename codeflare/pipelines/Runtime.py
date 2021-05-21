import ray

from codeflare.pipelines.Datamodel import OrNode
from codeflare.pipelines.Datamodel import AndNode
from codeflare.pipelines.Datamodel import Edge
from codeflare.pipelines.Datamodel import Pipeline
from codeflare.pipelines.Datamodel import XYRef
from codeflare.pipelines.Datamodel import Xy

import sklearn.base as base
from enum import Enum


class ExecutionType(Enum):
    FIT = 0,
    PREDICT = 1,
    SCORE = 2


@ray.remote
def execute_or_node_inner(node: OrNode, train_mode: ExecutionType, Xy: XYRef):
    estimator = node.get_estimator()
    # Blocking operation -- not avoidable
    X = ray.get(Xy.get_Xref())
    y = ray.get(Xy.get_yref())

    if train_mode == ExecutionType.FIT:
        if base.is_classifier(estimator) or base.is_regressor(estimator):
            # Always clone before fit, else fit is invalid
            cloned_estimator = base.clone(estimator)
            cloned_estimator.fit(X, y)
            # TODO: For now, make yref passthrough - this has to be fixed more comprehensively
            res_Xref = ray.put(cloned_estimator.predict(X))
            result = XYRef(res_Xref, Xy.get_yref())
            return result
        else:
            # No need to clone as it is a transform pass through on the fitted estimator
            res_Xref = ray.put(estimator.fit_transform(X, y))
            result = XYRef(res_Xref, Xy.get_yref())
            return result
    elif train_mode == ExecutionType.SCORE:
        if base.is_classifier(estimator) or base.is_regressor(estimator):
            cloned_estimator = base.clone(estimator)
            cloned_estimator.fit(X, y)
            res_Xref = ray.put(cloned_estimator.score(X, y))
            result = XYRef(res_Xref, Xy.get_yref())
            return result
        else:
            # No need to clone as it is a transform pass through on the fitted estimator
            res_Xref = ray.put(estimator.fit_transform(X, y))
            result = XYRef(res_Xref, Xy.get_yref())
            return result
    elif train_mode == ExecutionType.PREDICT:
        # Test mode does not clone as it is a simple predict or transform
        if base.is_classifier(estimator) or base.is_regressor(estimator):
            res_Xref = estimator.predict(X)
            result = XYRef(res_Xref, Xy.get_yref())
            return result
        else:
            res_Xref = estimator.transform(X)
            result = XYRef(res_Xref, Xy.get_yref())
            return result


def execute_or_node(node, pre_edges, edge_args, post_edges, mode: ExecutionType):
    for pre_edge in pre_edges:
        Xyref_ptrs = edge_args[pre_edge]
        exec_xyrefs = []
        for xy_ref_ptr in Xyref_ptrs:
            xy_ref = ray.get(xy_ref_ptr)
            inner_result = execute_or_node_inner.remote(node, mode, xy_ref)
            exec_xyrefs.append(inner_result)

        for post_edge in post_edges:
            if post_edge not in edge_args.keys():
                edge_args[post_edge] = []
            edge_args[post_edge].extend(exec_xyrefs)


@ray.remote
def and_node_eval(and_func, Xyref_list):
    xy_list = []
    for Xyref in Xyref_list:
        X = ray.get(Xyref.get_Xref())
        y = ray.get(Xyref.get_yref())
        xy_list.append(Xy(X, y))

    res_Xy = and_func.eval(xy_list)
    res_Xref = ray.put(res_Xy.get_x())
    res_yref = ray.put(res_Xy.get_y())
    return XYRef(res_Xref, res_yref)


def execute_and_node_inner(node: AndNode, Xyref_ptrs):
    and_func = node.get_and_func()
    result = []

    Xyref_list = []
    for Xyref_ptr in Xyref_ptrs:
        Xyref = ray.get(Xyref_ptr)
        Xyref_list.append(Xyref)

    Xyref_ptr = and_node_eval.remote(and_func, Xyref_list)
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


def execute_pipeline(pipeline: Pipeline, mode: ExecutionType, in_args: dict):
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
            if not node.get_and_flag():
                execute_or_node(node, pre_edges, edge_args, post_edges, mode)
            elif node.get_and_flag():
                execute_and_node(node, pre_edges, edge_args, post_edges)

    out_args = {}
    last_level_nodes = nodes_by_level[pipeline.compute_max_level()]
    for last_level_node in last_level_nodes:
        edge = Edge(last_level_node, None)
        out_args[last_level_node] = edge_args[edge]

    return out_args
