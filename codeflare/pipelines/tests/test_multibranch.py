import pytest
import ray
import pandas as pd
import numpy as np
from sklearn.compose import ColumnTransformer
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.tree import DecisionTreeClassifier
from sklearn.linear_model import LogisticRegression
import sklearn.base as base
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

def test_multibranch_1():

    ray.shutdown()
    ray.init()

    ## prepare the data
    X = pd.DataFrame(np.random.randint(0,100,size=(10000, 4)), columns=list('ABCD'))
    y = pd.DataFrame(np.random.randint(0,2,size=(10000, 1)), columns=['Label'])

    numeric_features = X.select_dtypes(include=['int64']).columns
    numeric_transformer = Pipeline(steps=[
        ('scaler', StandardScaler())])

    ## set up preprocessor as StandardScaler
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', numeric_transformer, numeric_features),
            ])

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

    ## initialize codeflare pipeline by first creating the nodes
    pipeline = dm.Pipeline()

    node_a = dm.EstimatorNode('preprocess', preprocessor)
    node_b = dm.EstimatorNode('s_b', MinMaxScaler())
    node_c = dm.AndNode('s_c', FeatureUnion())
    node_d = dm.EstimatorNode('c_d', LogisticRegression())
    node_e = dm.EstimatorNode('c_e', DecisionTreeClassifier(max_depth=3))

    ## codeflare nodes are then connected by edges
    pipeline.add_edge(node_a, node_b)
    pipeline.add_edge(node_b, node_c)
    pipeline.add_edge(node_c, node_d)
    pipeline.add_edge(node_c, node_e)

    pipeline_input = dm.PipelineInput()
    xy = dm.Xy(X_train, y_train)
    pipeline_input.add_xy_arg(node_a, xy)

    ## execute the codeflare pipeline
    pipeline_output = rt.execute_pipeline(pipeline, ExecutionType.FIT, pipeline_input)

    ## retrieve node e
    node_e_output = pipeline_output.get_xyrefs(node_e)
    Xout = ray.get(node_e_output[0].get_Xref())
    yout = ray.get(node_e_output[0].get_yref())

    assert Xout.shape[0] == 8000
    assert yout.shape[0] == 8000

    ray.shutdown()

def test_multibranch_2():

    ray.shutdown()
    ray.init()

    ## prepare the data
    X = pd.DataFrame(np.random.randint(0,100,size=(10000, 4)), columns=list('ABCD'))
    y = pd.DataFrame(np.random.randint(0,2,size=(10000, 1)), columns=['Label'])

    numeric_features = X.select_dtypes(include=['int64']).columns
    numeric_transformer = Pipeline(steps=[
        ('scaler', StandardScaler())])

    ## set up preprocessor as StandardScaler
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', numeric_transformer, numeric_features),
            ])

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

    ## initialize codeflare pipeline by first creating the nodes
    pipeline = dm.Pipeline()

    node_a = dm.EstimatorNode('preprocess', preprocessor)
    node_b = dm.EstimatorNode('c_a', DecisionTreeClassifier(max_depth=3))
    node_c = dm.EstimatorNode('c_b', LogisticRegression())

    node_d = dm.EstimatorNode('s_d', MinMaxScaler())
    node_e = dm.EstimatorNode('s_e', StandardScaler())
    node_f = dm.AndNode('s_f', FeatureUnion())
    node_g = dm.EstimatorNode('c_g', DecisionTreeClassifier(max_depth=5))

    ## codeflare nodes are then connected by edges
    pipeline.add_edge(node_a, node_b)
    pipeline.add_edge(node_a, node_c)

    pipeline.add_edge(node_a, node_d)
    pipeline.add_edge(node_a, node_e)
    pipeline.add_edge(node_d, node_f)
    pipeline.add_edge(node_e, node_f)
    pipeline.add_edge(node_f, node_g)

    pipeline_input = dm.PipelineInput()
    xy = dm.Xy(X_train, y_train)
    pipeline_input.add_xy_arg(node_a, xy)

    ## execute the codeflare pipeline
    pipeline_output = rt.execute_pipeline(pipeline, ExecutionType.FIT, pipeline_input)

    ## retrieve node b
    node_b_output = pipeline_output.get_xyrefs(node_b)
    Xout = ray.get(node_b_output[0].get_Xref())
    yout = ray.get(node_b_output[0].get_yref())

    assert Xout.shape[0] == 8000
    assert yout.shape[0] == 8000

    ## retrieve node g
    node_g_output = pipeline_output.get_xyrefs(node_g)
    Xout = ray.get(node_g_output[0].get_Xref())
    yout = ray.get(node_g_output[0].get_yref())

    assert Xout.shape[0] == 8000
    assert yout.shape[0] == 8000

    ray.shutdown()


if __name__ == "__main__":
    sys.exit(pytest.main(["-v", __file__]))
