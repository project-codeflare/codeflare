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

    X_ref = ray.put(X)
    y_ref = ray.put(None)

    Xy_ref = XYRef(X_ref, y_ref)
    Xy_ref_ptr = ray.put(Xy_ref)
    Xy_ref_ptrs = [Xy_ref_ptr]

    ## initialize codeflare pipeline by first creating the nodes
    pipeline = dm.Pipeline()
    node_a = dm.EstimatorNode('a', MinMaxScaler())
    node_b = dm.EstimatorNode('b', StandardScaler())
    node_c = dm.AndNode('c', FeatureUnion())

    ## codeflare nodes are then connected by edges
    pipeline.add_edge(node_a, node_b)
    pipeline.add_edge(node_a, node_c)

    in_args={node_a: Xy_ref_ptrs, node_b: Xy_ref_ptrs}
    ## execute the codeflare pipeline
    out_args = rt.execute_pipeline(pipeline, ExecutionType.FIT, in_args)

    ## retrieve node c
    out_Xyrefs = ray.get(out_args[node_c])
    assert out_Xyrefs

    for out_xyref in out_Xyrefs:
        x = ray.get(out_xyref.get_Xref())
        and_func = ray.get(out_xyref.get_currnoderef()).get_and_func()
        assert x.any()
        print(x)

    ray.shutdown()


if __name__ == "__main__":
    sys.exit(pytest.main(["-v", __file__]))
