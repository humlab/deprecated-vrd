"""
Contains ffmpeg-dependent tests
"""
import unittest

import tests.test_segment
import tests.test_slice


# initialize the test suite
loader = unittest.TestLoader()
suite = unittest.TestSuite()

# add tests to the test suite
suite.addTests(loader.loadTestsFromModule(tests.test_slice))
suite.addTests(loader.loadTestsFromModule(tests.test_segment))

# initialize a runner, and run the suite
runner = unittest.TextTestRunner(verbosity=3)
result = runner.run(suite)
