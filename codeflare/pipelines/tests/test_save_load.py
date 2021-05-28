import pytest

import codeflare.pipelines.Datamodel as dm
import codeflare.pipelines.Runtime as rt

import numpy as np
from sklearn.preprocessing import FunctionTransformer
from sklearn.preprocessing import MinMaxScaler
import os


class FeatureUnion(dm.AndTransform):
    def __init__(self):
        pass

    def transform(self, xy_list):
        X_list = []
        y_list = []

        for xy in xy_list:
            X_list.append(xy.get_x())
        X_concat = np.concatenate(X_list, axis=0)

        return dm.Xy(X_concat, None)


def test_save_load():
    """
    A simple save load test for a pipeline graph
    :return:
    """
    pipeline = dm.Pipeline()
    minmax_scaler = MinMaxScaler()

    node_a = dm.EstimatorNode('a', minmax_scaler)
    node_b = dm.EstimatorNode('b', minmax_scaler)
    node_c = dm.AndNode('c', FeatureUnion())

    pipeline.add_edge(node_a, node_c)
    pipeline.add_edge(node_b, node_c)

    fname = 'save_pipeline.cfp'
    fh = open(fname, 'wb')
    pipeline.save(fh)
    fh.close()

    r_fh = open(fname, 'rb')
    saved_pipeline = dm.Pipeline.load(r_fh)
    pre_edges = saved_pipeline.get_pre_edges(node_c)
    assert(len(pre_edges) == 2)

    os.remove(fname)


def test_runtime_save_load():
    """
    Tests for selecting a pipeline and save/load it, we also test the predict to ensure state is
    captured accurately
    :return:
    """
    