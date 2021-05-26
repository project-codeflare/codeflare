import pytest
import ray
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, MinMaxScaler
import codeflare.pipelines.Datamodel as dm
import codeflare.pipelines.Runtime as rt
from codeflare.pipelines.Datamodel import Xy
from codeflare.pipelines.Datamodel import XYRef
from codeflare.pipelines.Runtime import ExecutionType

class FeatureUnion(dm.AndTransform):
    def __init__(self):
        pass

    def transform(self, xy_list):
        X_list = []
        y_list = []

        for xy in xy_list:
            X_list.append(xy.get_x())
        X_concat = np.concatenate(X_list, axis=0)

        return Xy(X_concat, None)

def test_and():

    ray.shutdown()
    ray.init()

    ## prepare the data
    X = np.random.randint(0,100,size=(10000, 4))
    y = np.random.randint(0,2,size=(10000, 1))

    ## initialize codeflare pipeline by first creating the nodes
    pipeline = dm.Pipeline()
    node_a = dm.EstimatorNode('a', MinMaxScaler())
    node_b = dm.EstimatorNode('b', StandardScaler())
    node_c = dm.AndNode('c', FeatureUnion())

    ## codeflare nodes are then connected by edges
    pipeline.add_edge(node_a, node_c)
    pipeline.add_edge(node_b, node_c)

    pipeline_input = dm.PipelineInput()
    xy = dm.Xy(X,y)
    pipeline_input.add_xy_arg(node_a, xy)
    pipeline_input.add_xy_arg(node_b, xy)

    ## execute the codeflare pipeline
    pipeline_output = rt.execute_pipeline(pipeline, ExecutionType.FIT, pipeline_input)

    ## retrieve node c
    node_c_output = pipeline_output.get_xyrefs(node_c)
    assert node_c_output

    ray.shutdown()


if __name__ == "__main__":
    sys.exit(pytest.main(["-v", __file__]))
