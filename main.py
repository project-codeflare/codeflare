# This is a sample Python script.

# Press ⌃R to execute it or replace it with your code.
# Press Double ⇧ to search everywhere for classes, files, tool windows, actions, and settings.


def print_hi(name):
    # Use a breakpoint in the code line below to debug your script.
    print(f'Hi, {name}')  # Press ⌘F8 to toggle the breakpoint.


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    print_hi('PyCharm')

    x = None
    if not x:
        print('abc')

    import numpy as np
    from sklearn.preprocessing import FunctionTransformer
    from sklearn.preprocessing import Binarizer

    transformer = FunctionTransformer(np.log1p)
    binarizer = Binarizer(threshold=0.5)
    import com.ibm.research.ray.graph.Datamodel as dm

    pipeline = dm.Pipeline()
    node_a = dm.Node('a', transformer)
    node_b = dm.Node('b', binarizer)
    node_c = dm.Node('c', transformer)

    pipeline.add_edge(node_a, node_b)
    pipeline.add_edge(node_b, node_c)
    node_levels = pipeline.compute_node_levels()

    for node, level in node_levels.items():
        print(str(node) + ' at ' + str(level))
    # for i in range(len(node_levels)):
    #     print('level=' + str(i))
    #     for node in node_levels[i]:
    #         print('node=' + str(node))
    #     print('end level...')

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
