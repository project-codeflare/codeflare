import ray
import pandas as pd
import codeflare.pipelines.Datamodel as dm
import codeflare.pipelines.utils as cfutils


def test_utils_split():
    ray.shutdown()
    ray.init()
    d = {'col1': [1, 2, 3, 4, 5, 6, 7, 8], 'col2': [3, 4, 5, 6, 7, 8, 9, 10]}
    df = pd.DataFrame(d)
    x_test_ref = ray.put(df)
    y_test_ref = ray.put(None)
    xy_ref_test = dm.XYRef(x_test_ref, y_test_ref)

    split_ref = cfutils.split.remote(xy_ref_test, 4)
    xy_ref_splits = ray.get(split_ref)
    assert len(xy_ref_splits) == 4

    # get the output and assert again
    X_in_ray = ray.get(xy_ref_splits[0].get_Xref())
    assert len(X_in_ray) == 2