# Architecture decision record

Select a test framework for Codeflare pipeline.

Contents:

* [Use pytest as test framework](#use-pytest-as-test-framework)
* [Unit test coverage](#unit-test-coverage)

## Use pytest as test framework
PyTest is a testing framework in Python, with simple and easy syntax targeting unit tests and simple functional tests. PyTest can run tests in parallel and automatically detects tests in the test folder. PyTest serves the current goal of testing Codeflare pipelines well.

## Unit test coverage
* and (fan-in) node in a pipeline graph, and variants
* or (fan-out) node in a pipeline graph, and variants
* multibranch with mixtures of and/or nodes in a pipeline graph
