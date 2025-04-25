import os
import sys
import unittest
import argparse


def run_tests(directories=None, test=None, test_suite=None):
    """
    Run all the tests in the given paths.
    Args:
        directories: A generator or list of paths containing tests to run.
        test: Optional name of a specific test to run.
        test_suite: Optional TestSuite to run.  If omitted, a TestSuite will be generated.

    """

    if test_suite is None:
        test_suite = get_tests(directories, test)
    runner = unittest.TextTestRunner(verbosity=2)
    runner.failfast = False
    runner.run(test_suite)


def add_to_path(path):
    """
    Add the specified path to the system path.
    Args:
        path(str): Path to add.

    Returns:
        bool: True if path was added. Return false if path does not exist or path was already in sys.path

    """

    if os.path.exists(path) and path not in sys.path:
        sys.path.insert(0, path)
        return True
    return False


def get_tests(directories=None, test=None, test_suite=None):
    """
    Get a unittest.TestSuite containing all the desired tests.
    Args:
        directories(list): Optional list of directories with which to search for tests.
        If omitted, use all "tests" directories of the modules found in the MAYA_MODULE_PATH.
        test(str): Optional test path to find a specific test such as 'test_mytest.SomeTestCase.test_function'.
        test_suite(unittest.TestSuite) : Optional unittest.TestSuite to add the discovered tests to.
          If omitted a new TestSuite will be created.

    Returns:
        (TestSuite): The populated TestSuite
    """

    if directories is None:
        directories = maya_tests_dir()

    # Populate a TestSuite with all the tests
    if test_suite is None:
        test_suite = unittest.TestSuite()

    if test:
        # Find the specified test to run
        directories_added_to_path = [p for p in directories if add_to_path(p)]
        discovered_suite = unittest.TestLoader().loadTestsFromName(test)
        if discovered_suite.countTestCases():
            test_suite.addTests(discovered_suite)
    else:
        # Find all tests to run
        directories_added_to_path = []
        for p in directories:
            discovered_suite = unittest.TestLoader().discover(p)
            if discovered_suite.countTestCases():
                test_suite.addTests(discovered_suite)

    # Remove the added paths.
    for path in directories_added_to_path:
        sys.path.remove(path)

    return test_suite


def maya_tests_dir():
    """Generator function to iterate over all the Maya module tests directories."""
    if 'MHY_MAYA_TEST_PATH' in os.environ:
        for path in os.environ["MHY_MAYA_TEST_PATH"].split(os.pathsep):
            if os.path.exists(path):
                yield path


def run(directories=None, test=None, test_suite=None):
    """
    Runs the tests in Maya standalone mode.
    Args:
        directories(list): Optional list of directories with which to search for tests.
        If omitted, use all "tests" directories of the modules found in the MAYA_MODULE_PATH.
        test(str): Optional test path to find a specific test such as 'test_mytest.SomeTestCase.test_function'.
        test_suite(unittest.TestSuite) : Optional unittest.TestSuite to add the discovered tests to.
          If omitted a new TestSuite will be created.


    """

    parser = argparse.ArgumentParser(description='Runs unit tests for a Maya module')
    parser.add_argument('-p', '--path', help='Test module', type=str, default="")

    pargs = parser.parse_args()
    if pargs.path:
        directories = [pargs.path]

    py_ver = sys.version_info[0]
    if py_ver >= 3:
        import maya.app.commands
        orig_process_command_list = maya.app.commands.processCommandList

        def new_process_command_list():
            orig_process_command_list()
            import maya.cmds as cmds2
            cmds2.optionVar(iv=('SafeModeExecUserSetupScript', 1))

        maya.app.commands.processCommandList = new_process_command_list

    import maya.standalone

    maya.standalone.initialize()
    realsyspath = [os.path.realpath(p) for p in sys.path]
    pythonpath = os.environ.get("PYTHONPATH", "")
    for p in pythonpath.split(os.pathsep):
        p = os.path.realpath(p)  # Make sure symbolic links are resolved
        if p not in realsyspath:
            sys.path.insert(0, p)

    run_tests(directories, test, test_suite)
    maya.standalone.uninitialize()


if __name__ == "__main__":
    run()
