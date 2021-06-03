from codeflare.pipelines.tests import test_helper

import codeflare.pipelines.Datamodel as dm
import codeflare.pipelines.Runtime as rt

from sklearn.model_selection import KFold


def test_runtime_pipeline_input_getter():
    """
    A test to get the pipeline inputs after a selection is done
    :return:
    """

    import ray
    ray.shutdown()
    ray.init()
    X_train, X_test, y_train, y_test = test_helper.get_data()
    pipeline = test_helper.get_pipeline(X_train)

    node_rf = pipeline.get_node('random_forest')
    node_gb = pipeline.get_node('gradient_boost')
    input_node = pipeline.get_node('preprocess')

    pipeline_input = dm.PipelineInput()
    xy = dm.Xy(X_train, y_train)
    pipeline_input.add_xy_arg(input_node, xy)

    pipeline_output = rt.execute_pipeline(pipeline, rt.ExecutionType.FIT, pipeline_input)
    node_rf_xyrefs = pipeline_output.get_xyrefs(node_rf)

    selected_pipeline_input = rt.get_pipeline_input(pipeline, pipeline_output, node_rf_xyrefs[0])
    in_args = selected_pipeline_input.get_in_args()
    is_input_node_present = (input_node in in_args.keys())
    assert is_input_node_present

    # check if the XYref is the same
    xyref_ptrs = in_args[input_node]
    xyref_ptr = xyref_ptrs[0]
    xyref = ray.get(xyref_ptr)

    input_xyref = ray.get(pipeline_input.get_in_args()[input_node][0])
    assert xyref.get_Xref() == input_xyref.get_Xref()
    assert xyref.get_yref() == input_xyref.get_yref()


def test_grid_search():
    import ray
    ray.shutdown()
    ray.init()

    import pandas as pd

    X_train, X_test, y_train, y_test = test_helper.get_data()
    pipeline = test_helper.get_pipeline(X_train)

    input_node = pipeline.get_node('preprocess')

    pipeline_input = dm.PipelineInput()
    xy = dm.Xy(X_train, y_train)
    pipeline_input.add_xy_arg(input_node, xy)

    k = 2
    kf = KFold(k)
    result = rt.grid_search_cv(kf, pipeline, pipeline_input)
    node_rf = pipeline.get_node('random_forest')
    node_gb = pipeline.get_node('gradient_boost')
    # result should have two pipelines, with two scored outputs each
    node_rf_pipeline = False
    node_gb_pipeline = False
    for cv_pipeline, scores in result.items():
        out_node = cv_pipeline.get_output_nodes()[0]
        if out_node.get_node_name() == node_rf.get_node_name():
            node_rf_pipeline = True
        elif out_node.get_node_name() == node_gb.get_node_name():
            node_gb_pipeline = True
        if len(scores) != k:
            assert False
    assert node_rf_pipeline
    assert node_gb_pipeline
