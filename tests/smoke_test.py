"""
Will signal if something is wrong with the fingerprinting pipeline
"""
import unittest

import tests.test_fingerprint


# initialize the test suite
loader = unittest.TestLoader()
suite = unittest.TestSuite()

# add tests to the test suite
suite.addTests(loader.loadTestsFromModule(tests.test_fingerprint))

# initialize a runner, and run the suite
runner = unittest.TextTestRunner(verbosity=3)
result = runner.run(suite)
