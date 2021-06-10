import graphviz
import codeflare.pipelines.Datamodel as dm


def pipeline_to_graph(pipeline: dm.Pipeline) -> graphviz.Digraph:
    """
    Converts the given pipeline to a networkX graph for visualization.

    :param pipeline: Pipeline to convert to networkX graph
    :return: A directed graph representing this pipeline
    """
    graph = graphviz.Digraph()
    pipeline_nodes = pipeline.get_nodes()
    for pre_node in pipeline_nodes.values():
        post_nodes = pipeline.get_post_nodes(pre_node)
        graph.node(pre_node.get_node_name())
        for post_node in post_nodes:
            graph.node(post_node.get_node_name())
            graph.edge(pre_node.get_node_name(), post_node.get_node_name())
    return graph
