import unittest

if __name__ == "__main__":
    loader = unittest.defaultTestLoader.discover('tests')
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(loader)
