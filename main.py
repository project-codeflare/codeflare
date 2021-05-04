# This is a sample Python script.

# Press ⌃R to execute it or replace it with your code.
# Press Double ⇧ to search everywhere for classes, files, tool windows, actions, and settings.

from sklearn.preprocessing import FunctionTransformer
from sklearn.base import ClassifierMixin
from sklearn.ensemble import RandomForestClassifier


class CTransformer(FunctionTransformer):
    def transform(self, X):
        retval = np.zeros(len(X[0]))
        for x in X:
            retval = retval + x
        return retval


class ScaleTestEstimator(ClassifierMixin):
    __num_iters__ = 100
    __randomforest_classifier__ : RandomForestClassifier = None

    def __init__(self, num_iters, rf_classifier: RandomForestClassifier):
        self.__num_iters__ = num_iters
        self.__randomforest_classifier__ = rf_classifier

    def fit(self, X, y):
        for i in range(self.__num_iters__):
            self.__randomforest_classifier__.fit(X, y)

    def score(self, X, y, sample_weight=None):
        return self.__randomforest_classifier__.score(X, y, sample_weight)


def print_hi(name):
    # Use a breakpoint in the code line below to debug your script.
    print(f'Hi, {name}')  # Press ⌘F8 to toggle the breakpoint.


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    print_hi('PyCharm')

    import pandas as pd

    train = pd.read_csv('resources/data/train_ctrUa4K.csv')
    test = pd.read_csv('resources/data/test_lAUu6dG.csv')
    train = train.drop('Loan_ID', axis=1)
    train.dtypes

    X = train.drop('Loan_Status', axis=1)
    y = train['Loan_Status']
    from sklearn.model_selection import train_test_split

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

    from sklearn.tree import DecisionTreeClassifier
    from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier

    c_a = ScaleTestEstimator(50, DecisionTreeClassifier())
    c_b = ScaleTestEstimator(50, RandomForestClassifier())
    c_c = ScaleTestEstimator(50, GradientBoostingClassifier())

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
