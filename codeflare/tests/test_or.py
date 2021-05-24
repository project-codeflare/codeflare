import pytest
import ray
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from codeflare.pipelines.Datamodel import Xy
from codeflare.pipelines.Datamodel import XYRef
import codeflare.pipelines.Datamodel as dm
import codeflare.pipelines.Runtime as rt
from codeflare.pipelines.Runtime import ExecutionType

def test_or():

    ray.init()
    
    train = pd.read_csv('../resources/data/train_ctrUa4K.csv')
    test = pd.read_csv('../resources/data/test_lAUu6dG.csv')

    X = train.drop('Loan_Status', axis=1)
    y = train['Loan_Status']

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

    X_ref = ray.put(X_train)
    y_ref = ray.put(y_train)

    Xy_ref = XYRef(X_ref, y_ref)
    Xy_ref_list = [Xy_ref]

    pipeline = dm.Pipeline()
    node_a = dm.OrNode('preprocess', preprocessor)
    node_b = dm.OrNode('c_a', c_a)
    node_c = dm.OrNode('c_b', c_b)
    
    pipeline.add_edge(node_a, node_b)
    pipeline.add_edge(node_a, node_c)

    in_args={node_a: Xy_ref_list}
    out_args = rt.execute_pipeline(pipeline, ExecutionType.FIT, in_args)

    node_b_out_args = ray.get(out_args[node_b])
    node_c_out_args = ray.get(out_args[node_c])

    b_out_xyref = node_b_out_args[0]

    ray.get(b_out_xyref.get_Xref())


if __name__ == "__main__":
    sys.exit(pytest.main(["-v", __file__]))


