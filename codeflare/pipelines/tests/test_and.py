import pytest
import ray
import pandas as pd
import numpy as np
import sklearn.base as base
from sklearn.preprocessing import StandardScaler, MinMaxScaler, MaxAbsScaler, RobustScaler
import codeflare.pipelines.Datamodel as dm
import codeflare.pipelines.Runtime as rt
from codeflare.pipelines.Datamodel import Xy
from codeflare.pipelines.Datamodel import XYRef
from codeflare.pipelines.Runtime import ExecutionType

class FeatureUnion(dm.AndEstimator):
    def __init__(self):
        pass
    def get_estimator_type(self):
        return 'transform'
    def clone(self):
        return base.clone(self)
    def fit_transform(self, xy_list):
        return self.transform(xy_list)
    def transform(self, xy_list):
        X_list = []
        y_vec = None
        for xy in xy_list:
            X_list.append(xy.get_x())
            y_vec = xy.get_y()
        X_concat = np.concatenate(X_list, axis=1)
        return Xy(X_concat, y_vec)

def test_two_tier_and():

    ray.shutdown()
    ray.init()

    ## prepare the data
    X = np.random.randint(0,100,size=(10000, 4))
    y = np.random.randint(0,2,size=(10000, 1))

    ## initialize codeflare pipeline by first creating the nodes
    pipeline = dm.Pipeline()
    node_a = dm.EstimatorNode('a', MinMaxScaler())
    node_b = dm.EstimatorNode('b', StandardScaler())
    node_c = dm.EstimatorNode('c', MaxAbsScaler())
    node_d = dm.EstimatorNode('d', RobustScaler())

    node_e = dm.AndNode('e', FeatureUnion())
    node_f = dm.AndNode('f', FeatureUnion())
    node_g = dm.AndNode('g', FeatureUnion())

    ## codeflare nodes are then connected by edges
    pipeline.add_edge(node_a, node_e)
    pipeline.add_edge(node_b, node_e)
    pipeline.add_edge(node_c, node_f)
    pipeline.add_edge(node_d, node_f)
    pipeline.add_edge(node_e, node_g)
    pipeline.add_edge(node_f, node_g)

    pipeline_input = dm.PipelineInput()
    xy = dm.Xy(X,y)
    pipeline_input.add_xy_arg(node_a, xy)
    pipeline_input.add_xy_arg(node_b, xy)
    pipeline_input.add_xy_arg(node_c, xy)
    pipeline_input.add_xy_arg(node_d, xy)

    ## execute the codeflare pipeline
    pipeline_output = rt.execute_pipeline(pipeline, ExecutionType.FIT, pipeline_input)

    ## retrieve node e
    node_g_output = pipeline_output.get_xyrefs(node_g)
    Xout = ray.get(node_g_output[0].get_Xref())
    yout = ray.get(node_g_output[0].get_yref())

    assert Xout.shape[0] == 10000
    assert yout.shape[0] == 10000

    ray.shutdown()

def test_four_input_and():

    ray.shutdown()
    ray.init()

    ## prepare the data
    X = np.random.randint(0,100,size=(10000, 4))
    y = np.random.randint(0,2,size=(10000, 1))

    ## initialize codeflare pipeline by first creating the nodes
    pipeline = dm.Pipeline()
    node_a = dm.EstimatorNode('a', MinMaxScaler())
    node_b = dm.EstimatorNode('b', StandardScaler())
    node_c = dm.EstimatorNode('c', MaxAbsScaler())
    node_d = dm.EstimatorNode('d', RobustScaler())

    node_e = dm.AndNode('e', FeatureUnion())

    ## codeflare nodes are then connected by edges
    pipeline.add_edge(node_a, node_e)
    pipeline.add_edge(node_b, node_e)
    pipeline.add_edge(node_c, node_e)
    pipeline.add_edge(node_d, node_e)

    pipeline_input = dm.PipelineInput()
    xy = dm.Xy(X,y)
    pipeline_input.add_xy_arg(node_a, xy)
    pipeline_input.add_xy_arg(node_b, xy)
    pipeline_input.add_xy_arg(node_c, xy)
    pipeline_input.add_xy_arg(node_d, xy)

    ## execute the codeflare pipeline
    pipeline_output = rt.execute_pipeline(pipeline, ExecutionType.FIT, pipeline_input)

    ## retrieve node e
    node_e_output = pipeline_output.get_xyrefs(node_e)
    Xout = ray.get(node_e_output[0].get_Xref())
    yout = ray.get(node_e_output[0].get_yref())

    assert Xout.shape[0] == 10000
    assert yout.shape[0] == 10000

    ray.shutdown()

def test_two_input_and():

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
    Xout = ray.get(node_c_output[0].get_Xref())
    yout = ray.get(node_c_output[0].get_yref())

    assert Xout.shape[0] == 10000
    assert yout.shape[0] == 10000

    ray.shutdown()


if __name__ == "__main__":
    sys.exit(pytest.main(["-v", __file__]))
