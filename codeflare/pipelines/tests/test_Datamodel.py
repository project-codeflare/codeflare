import unittest
import ray
import pandas as pd
import numpy as np
from sklearn.compose import ColumnTransformer
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.tree import DecisionTreeClassifier
import sklearn.base as base
import codeflare.pipelines.Datamodel as dm
import codeflare.pipelines.Runtime as rt
from codeflare.pipelines.Datamodel import Xy
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

class MultibranchTestCase(unittest.TestCase):

    def test_multibranch(self):
        ray.shutdown()
        ray.init()

        ## prepare the data
        X = pd.DataFrame(np.random.randint(0, 100, size=(10000, 4)), columns=list('ABCD'))
        y = pd.DataFrame(np.random.randint(0, 2, size=(10000, 1)), columns=['Label'])

        numeric_features = X.select_dtypes(include=['int64']).columns
        numeric_transformer = Pipeline(steps=[
            ('scaler', StandardScaler())])

        ## set up preprocessor as StandardScaler
        preprocessor = ColumnTransformer(
            transformers=[
                ('num', numeric_transformer, numeric_features),
            ])

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)
        ## create two decision tree classifiers with different depth limit
        c_a = DecisionTreeClassifier(max_depth=3)
        c_b = DecisionTreeClassifier(max_depth=5)

        ## initialize codeflare pipeline by first creating the nodes
        pipeline = dm.Pipeline()
        node_a = dm.EstimatorNode('preprocess', preprocessor)
        node_b = dm.EstimatorNode('c_a', c_a)
        node_c = dm.EstimatorNode('c_b', c_b)

        node_d = dm.EstimatorNode('d', MinMaxScaler())
        node_e = dm.EstimatorNode('e', StandardScaler())
        node_f = dm.AndNode('f', FeatureUnion())

        ## codeflare nodes are then connected by edges
        pipeline.add_edge(node_a, node_b)
        pipeline.add_edge(node_a, node_c)

        pipeline.add_edge(node_a, node_d)
        pipeline.add_edge(node_d, node_e)
        pipeline.add_edge(node_d, node_f)

        pipeline_input = dm.PipelineInput()
        pipeline_input.add_xy_arg(node_a, dm.Xy(X_train, y_train))

        terminal_nodes = pipeline.get_output_nodes()
        assert len(terminal_nodes) == 4

        ## execute the codeflare pipeline
        pipeline_output = rt.execute_pipeline(pipeline, ExecutionType.FIT, pipeline_input)
        assert pipeline_output

        ## retrieve node b
        node_b_xyrefs = pipeline_output.get_xyrefs(node_b)
        b_out_xyref = node_b_xyrefs[0]
        ray.get(b_out_xyref.get_Xref())
        b_out_node = ray.get(b_out_xyref.get_curr_node_state_ref())
        sct_b = b_out_node.get_estimator()
        assert sct_b
        print(sct_b.feature_importances_)

        ## retrieve node f
        node_f_xyrefs = pipeline_output.get_xyrefs(node_f)
        assert node_f_xyrefs

        ray.shutdown()


def test_param_grid():
    from sklearn import datasets
    from sklearn.decomposition import PCA
    from sklearn.linear_model import LogisticRegression

    pca = PCA()
    # set the tolerance to a large value to make the example faster
    logistic = LogisticRegression(max_iter=10000, tol=0.1)

    pipeline = dm.Pipeline()
    node_pca = dm.EstimatorNode('pca', pca)
    node_logistic = dm.EstimatorNode('logistic', logistic)

    pipeline.add_edge(node_pca, node_logistic)

    param_grid = {
        'pca__n_components': [5, 15, 30, 45, 64],
        'logistic__C': np.logspace(-4, 4, 4),
    }

    pipeline_param = dm.PipelineParam.from_param_grid(param_grid)

    param_grid_pipeline = pipeline.get_parameterized_pipeline(pipeline_param)
    # num nodes should be 9 by construction
    num_nodes = len(param_grid_pipeline.get_nodes())
    assert num_nodes == 9


if __name__ == '__main__':
    unittest.main()
