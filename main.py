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

    x1 = [1, 2]
    x2 = [3, 4]
    x1.extend(x2)
    print(str(x1))
    exit(-1)

    x = CTransformer()
    import numpy as np

    input = np.array([[0, 1], [1, 2]])
    r = x.transform(input)
    print(r)

    x = None
    if not x:
        print('abc')

    import numpy as np
    from sklearn.preprocessing import FunctionTransformer
    from sklearn.preprocessing import Binarizer

    transformer = FunctionTransformer(np.log1p)
    import com.ibm.research.ray.graph.Datamodel as dm

    pipeline = dm.Pipeline()
    node_a = dm.Node('a', transformer)
    node_b = dm.Node('b', transformer)
    node_c = dm.Node('c', transformer, and_flag=True)

    args = {'transformer': transformer, 'node_name': 'x'}
    node_x = dm.Node(**args)
    print(str(node_x))

    pipeline.add_edge(node_a, node_c)
    pipeline.add_edge(node_b, node_c)

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
