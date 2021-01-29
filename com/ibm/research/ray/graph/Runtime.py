import ray
from com.ibm.research.ray.graph.Datamodel import Node
from com.ibm.research.ray.graph.Datamodel import Edge
from com.ibm.research.ray.graph.Datamodel import Pipeline


@ray.remote
def execute_node(node: Node, args):
    return node.get_transformer().transform(args)


###
#in_args is a dict from Node to list of object refs
###
def execute_pipeline(pipeline: Pipeline, in_args: dict):
    nodes_by_level = pipeline.get_nodes_by_level()

    #track args per edge
    edge_args = {}
    for node, node_in_args in in_args.items():
        pre_edges = pipeline.get_pre_edges(node)
        for pre_edge in pre_edges:
            edge_args[pre_edge] = node_in_args

    for nodes in nodes_by_level:
        for node in nodes:
            pre_edges = pipeline.get_pre_edges(node)
            post_edges = pipeline.get_post_edges(node)
            for pre_edge in pre_edges:
                for object_ref in edge_args[pre_edge]:
                    exec_ref = execute_node.remote(node, object_ref)
                    for post_edge in post_edges:
                        if post_edge not in edge_args.keys():
                            edge_args[post_edge] = []
                        edge_args[post_edge].append(exec_ref)

    out_args = {}
    last_level_nodes = nodes_by_level[pipeline.compute_max_level()]
    for last_level_node in last_level_nodes:
        edge = Edge(last_level_node, None)
        out_args[last_level_node] = edge_args[edge]

    return out_args
