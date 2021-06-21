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
#           Raghu Ganti <rganti@us.ibm.com>
#           Carlos Costa <chcost@us.ibm.com>
#
#

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
