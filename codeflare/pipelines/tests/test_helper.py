import codeflare.pipelines.Datamodel as dm

import pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier

import pathlib

def get_pipeline(train) -> dm.Pipeline:
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
    categorical_features = train.select_dtypes(include=['object']).columns
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

    return pipeline


def get_data():
    train = pd.read_csv(str(pathlib.Path(__file__).parent.absolute())+'/../../../resources/data/train_ctrUa4K.csv')
    train = train.drop('Loan_ID', axis=1)

    X = train.drop('Loan_Status', axis=1)
    y = train['Loan_Status']
    from sklearn.model_selection import train_test_split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

    return X_train, X_test, y_train, y_test