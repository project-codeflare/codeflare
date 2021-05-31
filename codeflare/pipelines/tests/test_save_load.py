import codeflare.pipelines.Datamodel as dm
import codeflare.pipelines.Runtime as rt

import numpy as np
from sklearn.preprocessing import MinMaxScaler
import os
import pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier

import ray


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
    assert (len(pre_edges) == 2)
    os.remove(fname)


def test_runtime_save_load():
    """
    Tests for selecting a pipeline and save/load it, we also test the predict to ensure state is
    captured accurately
    :return:
    """
    train = pd.read_csv('../../../resources/data/train_ctrUa4K.csv')
    train = train.drop('Loan_ID', axis=1)

    X = train.drop('Loan_Status', axis=1)
    y = train['Loan_Status']
    from sklearn.model_selection import train_test_split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)
    imputer = SimpleImputer(strategy='median')
    scaler = StandardScaler()

    numeric_transformer = Pipeline(steps=[
        ('imputer', imputer),
        ('scaler', scaler)])

    cat_imputer = SimpleImputer(strategy='constant', fill_value='missing')
    cat_onehot = OneHotEncoder(handle_unknown='ignore')

    categorical_transformer = Pipeline(steps=[
        ('imputer', cat_imputer),
        ('onehot', cat_onehot)])
    numeric_features = train.select_dtypes(include=['int64', 'float64']).columns
    categorical_features = train.select_dtypes(include=['object']).drop(['Loan_Status'], axis=1).columns
    from sklearn.compose import ColumnTransformer
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', numeric_transformer, numeric_features),
            ('cat', categorical_transformer, categorical_features)])

    classifiers = [
        RandomForestClassifier(),
        GradientBoostingClassifier()
    ]
    pipeline = dm.Pipeline()
    node_pre = dm.EstimatorNode('preprocess', preprocessor)
    node_rf = dm.EstimatorNode('random_forest', classifiers[0])
    node_gb = dm.EstimatorNode('gradient_boost', classifiers[1])

    pipeline.add_edge(node_pre, node_rf)
    pipeline.add_edge(node_pre, node_gb)

    import ray
    ray.shutdown()
    ray.init()
    pipeline_input = dm.PipelineInput()
    xy = dm.Xy(X_train, y_train)
    pipeline_input.add_xy_arg(node_pre, xy)

    pipeline_output = rt.execute_pipeline(pipeline, rt.ExecutionType.FIT, pipeline_input)
    node_rf_xyrefs = pipeline_output.get_xyrefs(node_rf)

    # save this pipeline for random forest and load and then predict on test data
    fname = 'random_forest.cfp'
    w_fh = open(fname, 'wb')
    rt.save(pipeline_output, node_rf_xyrefs[0], w_fh)
    w_fh.close()

    # load it
    r_fh = open(fname, 'rb')
    saved_pipeline = dm.Pipeline.load(r_fh)
    nodes = saved_pipeline.get_nodes()
    # this should not exist in the saved pipeline
    assert(node_gb.get_node_name() not in nodes.keys())

    # should be preditable as well
    predict_pipeline_input = dm.PipelineInput()
    predict_pipeline_input.add_xy_arg(node_pre, dm.Xy(X_test, y_test))
    try:
        predict_pipeline_output = rt.execute_pipeline(saved_pipeline, rt.ExecutionType.PREDICT, predict_pipeline_input)
        predict_pipeline_output.get_xyrefs(node_rf)
    except Exception:
        assert False

    os.remove(fname)