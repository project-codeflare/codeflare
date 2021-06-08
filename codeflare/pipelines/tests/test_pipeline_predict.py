import pytest
import ray

# Taking an example from sklearn pipeline to assert that
# the classification report from a rediction from sklearn pipeline is
# the same as that from the converted codeflare pipeline

from sklearn import set_config
set_config(display='diagram')
from sklearn.datasets import make_classification
from sklearn.model_selection import train_test_split
from sklearn.feature_selection import SelectKBest, f_classif
from sklearn.pipeline import make_pipeline
from sklearn.svm import LinearSVC
from sklearn.metrics import classification_report

import codeflare.pipelines.Datamodel as dm
import codeflare.pipelines.Runtime as rt
from codeflare.pipelines.Datamodel import Xy
from codeflare.pipelines.Datamodel import XYRef
from codeflare.pipelines.Runtime import ExecutionType

#
# prediction from an sklearn pipeline
#

def test_pipeline_predict():

	ray.shutdown()
	ray.init()

	#
	# prediction from an sklearn pipeline
	#
	X, y = make_classification(
    	n_features=20, n_informative=3, n_redundant=0, n_classes=2,
    	n_clusters_per_class=2, random_state=42)
	X_train, X_test, y_train, y_test = train_test_split(X, y, random_state=42)

	anova_filter = SelectKBest(f_classif, k=3)
	clf = LinearSVC()

	anova_svm = make_pipeline(anova_filter, clf)
	anova_svm.fit(X_train, y_train)

	y_pred = anova_svm.predict(X_test)

	report_sklearn = classification_report(y_test, y_pred)
	print(report_sklearn)

	#
	# constructing a codeflare pipeline
	#
	pipeline = dm.Pipeline()
	node_anova_filter = dm.EstimatorNode('anova_filter', anova_filter)
	node_clf = dm.EstimatorNode('clf', clf)
	pipeline.add_edge(node_anova_filter, node_clf)

	pipeline_input = dm.PipelineInput()
	xy = dm.Xy(X_train, y_train)

	pipeline_input.add_xy_arg(node_anova_filter, xy)

	pipeline_output = rt.execute_pipeline(pipeline, ExecutionType.FIT, pipeline_input)

	node_clf_output = pipeline_output.get_xyrefs(node_clf)

	Xout = ray.get(node_clf_output[0].get_Xref())
	yout = ray.get(node_clf_output[0].get_yref())

	selected_pipeline = rt.select_pipeline(pipeline_output, node_clf_output[0])

	pipeline_input = dm.PipelineInput()
	pipeline_input.add_xy_arg(node_anova_filter, dm.Xy(X_test, y_test))

	predict_output = rt.execute_pipeline(selected_pipeline, ExecutionType.PREDICT, pipeline_input)

	predict_clf_output = predict_output.get_xyrefs(node_clf)

	#y_pred = ray.get(predict_clf_output[0].get_yref())
	y_pred = ray.get(predict_clf_output[0].get_Xref())


	report_codeflare = classification_report(y_test, y_pred)

	print(report_codeflare)

	assert(report_sklearn == report_codeflare)

	ray.shutdown()


if __name__ == "__main__":
    sys.exit(pytest.main(["-v", __file__]))

