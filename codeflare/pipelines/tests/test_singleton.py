import pytest
import ray
import pandas as pd
import numpy as np
import sklearn.base as base
from sklearn.preprocessing import MinMaxScaler
import codeflare.pipelines.Datamodel as dm
import codeflare.pipelines.Runtime as rt
from codeflare.pipelines.Datamodel import Xy
from codeflare.pipelines.Datamodel import XYRef
from codeflare.pipelines.Runtime import ExecutionType

def test_singleton():

    ray.shutdown()
    ray.init()

    ## prepare the data
    X = np.random.randint(0,100,size=(10000, 4))
    y = np.random.randint(0,2,size=(10000, 1))

    ## initialize codeflare pipeline by first creating the nodes
    pipeline = dm.Pipeline()
    node_a = dm.EstimatorNode('a', MinMaxScaler())
    pipeline.add_node(node_a)

    pipeline_input = dm.PipelineInput()
    xy = dm.Xy(X,y)
    pipeline_input.add_xy_arg(node_a, xy)

    ## execute the codeflare pipeline
    pipeline_output = rt.execute_pipeline(pipeline, ExecutionType.TRANSFORM, pipeline_input)

    ## retrieve node e
    node_a_output = pipeline_output.get_xyrefs(node_a)
    Xout = ray.get(node_a_output[0].get_Xref())
    yout = ray.get(node_a_output[0].get_yref())

    assert Xout.shape[0] == 10000
    assert yout.shape[0] == 10000

    ray.shutdown()

if __name__ == "__main__":
    sys.exit(pytest.main(["-v", __file__]))
