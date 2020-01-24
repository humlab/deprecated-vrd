"""
Contains all tests that run fairly quickly and without having to invoke ffmpeg
"""
import unittest

import tests.test_color_correlation
import tests.test_image_transformation
import tests.test_orb


# initialize the test suite
loader = unittest.TestLoader()
suite = unittest.TestSuite()

# add tests to the test suite
suite.addTests(loader.loadTestsFromModule(tests.test_color_correlation))
suite.addTests(loader.loadTestsFromModule(tests.test_image_transformation))
suite.addTests(loader.loadTestsFromModule(tests.test_orb))

# initialize a runner, and run the suite
runner = unittest.TextTestRunner(verbosity=3)
result = runner.run(suite)
