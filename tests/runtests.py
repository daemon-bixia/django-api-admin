# -----------------------------------------------------------------------------
# Portions of this file are from Django (https://www.djangoproject.com/)
# Copyright (c) Django Software Foundation and individual contributors.
# All rights reserved.
# Licensed under the BSD 3-Clause License.
#
# Additional code copyright (c) 2021 Muhammad Salah
# Licensed under the MIT License
#
# This file includes both Django code and your my own contributions.
# -----------------------------------------------------------------------------

import argparse
import copy
import os
import sys
from pathlib import Path

# Add the project root to sys.path to allow importing django_api_admin.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    import django
except ImportError as e:
    raise RuntimeError("Django module not found, reference tests/README.rst for instructions.") from e
else:
    from django.apps import apps
    from django.conf import settings
    from django.db import connections
    from django.test import TestCase, TransactionTestCase
    from django.test.runner import get_max_test_processes, parallel_type
    from django.test.utils import NullTimeKeeper, TimeKeeper, get_runner
    from django.utils.log import DEFAULT_LOGGING
    from django.utils.functional import classproperty
    from django.utils.version import PY312


RUNTESTS_DIR = os.path.abspath(os.path.dirname(__file__))


ALWAYS_INSTALLED_APPS = [
    # django's apps
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.staticfiles",
    # my apps
    "django_api_admin.apps.DjangoApiAdminConfig",
    # 3rd party apps
    "rest_framework",
    "drf_spectacular",
]


ALWAYS_MIDDLEWARE = [
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
]


def get_test_modules():
    """
    Scan the tests directory and yield the names of all test modules.

    The yielded names have either one dotted part like "test_runner".
    """
    discovery_dirs = [""]
    for dirname in discovery_dirs:
        dirpath = os.path.join(RUNTESTS_DIR, dirname)
        with os.scandir(dirpath) as entries:
            for f in entries:
                if "." in f.name or f.is_file() or not os.path.exists(os.path.join(f.path, "__init__.py")):
                    continue
                test_module = f.name
                if dirname:
                    test_module = dirname + "." + test_module
                yield test_module


def get_label_module(label):
    """Return the top-level module part for a test label."""
    path = Path(label)
    if len(path.parts) == 1:
        # Interpret the label as a dotted module name.
        return label.split(".")[0]

    # Otherwise, interpret the label as a path. Check existence first to
    # provide a better error message than relative_to() if it doesn't exist.
    if not path.exists():
        raise RuntimeError(f"Test label path {label} does not exist")
    path = path.resolve()
    rel_path = path.relative_to(RUNTESTS_DIR)
    return rel_path.parts[0]


def get_filtered_test_modules(start_at, start_after, test_labels=None):
    if test_labels is None:
        test_labels = []

    # Reduce each test label to just the top-level module part.
    label_modules = set()
    for label in test_labels:
        test_module = get_label_module(label)
        label_modules.add(test_module)

    def _module_match_label(module_name, label):
        # Exact or ancestor match.
        return module_name == label or module_name.startswith(label + ".")

    start_label = start_at or start_after
    for test_module in get_test_modules():
        if start_label:
            if not _module_match_label(test_module, start_label):
                continue
            start_label = ""
            if not start_at:
                assert start_after
                # Skip the current one before starting.
                continue
        # If the module (or an ancestor) was named on the command line, or
        # no modules were named (i.e., run all), include the test module.
        if not test_labels or any(_module_match_label(test_module, label_module) for label_module in label_modules):
            yield test_module


def setup_collect_tests(start_at, start_after, test_labels=None):
    # Redirect some settings for the duration of these tests
    settings.INSTALLED_APPS = ALWAYS_INSTALLED_APPS
    settings.ROOT_URLCONF = "urls"
    settings.LANGUAGE_CODE = "en"
    settings.MIDDLEWARE = ALWAYS_MIDDLEWARE
    settings.MIGRATION_MODULES = {
        # This lets us skip creating migrations for the test models as many of
        # them depend on one of the following contrib applications.
        "auth": None,
        "contenttypes": None,
        "sessions": None,
        "django_api_admin": None,
    }
    log_config = copy.deepcopy(DEFAULT_LOGGING)
    # Filter out non-error logging so we don't have to capture it in lots of
    # tests.
    log_config["loggers"]["django"]["level"] = "ERROR"
    settings.LOGGING = log_config
    settings.SILENCED_SYSTEM_CHECKS = [
        "fields.W342",  # ForeignKey(unique=True) -> OneToOneField
    ]

    # Load all the ALWAYS_INSTALLED_APPS.
    django.setup()

    test_modules = list(
        get_filtered_test_modules(
            start_at,
            start_after,
            test_labels=test_labels,
        )
    )
    return test_modules


def get_installed():
    return [app_config.name for app_config in apps.get_app_configs()]


# This function should be called only after calling django.setup(),
# since it calls connection.features.gis_enabled.
def get_apps_to_install(test_modules):
    for test_module in test_modules:
        yield test_module


def setup_run_tests(verbosity, start_at, start_after, test_labels=None):
    test_modules = setup_collect_tests(start_at, start_after, test_labels=test_labels)

    installed_apps = set(get_installed())
    for app in get_apps_to_install(test_modules):
        if app in installed_apps:
            continue
        if verbosity >= 2:
            print(f"Importing application {app}")
        settings.INSTALLED_APPS.append(app)
        installed_apps.add(app)

    apps.set_installed_apps(settings.INSTALLED_APPS)

    # Force declaring available_apps in TransactionTestCase for faster tests.
    def no_available_apps(cls):
        raise Exception("Please define available_apps in TransactionTestCase and its subclasses.")

    TransactionTestCase.available_apps = classproperty(no_available_apps)
    TestCase.available_apps = None

    # Set an environment variable that other code may consult to see if
    # Django's own test suite is running.
    os.environ["RUNNING_DJANGOS_TEST_SUITE"] = "true"

    test_labels = test_labels or test_modules
    return test_labels


def teardown_run_tests():
    del os.environ["RUNNING_DJANGOS_TEST_SUITE"]


def django_tests(
    verbosity,
    interactive,
    failfast,
    keepdb,
    reverse,
    test_labels,
    debug_sql,
    parallel,
    tags,
    exclude_tags,
    test_name_patterns,
    start_at,
    start_after,
    pdb,
    buffer,
    timing,
    shuffle,
    durations=None,
):
    if parallel in {0, "auto"}:
        max_parallel = get_max_test_processes()
    else:
        max_parallel = parallel

    if verbosity >= 1:
        msg = "Testing against Django installed in '%s'" % os.path.dirname(django.__file__)
        if max_parallel > 1:
            msg += " with up to %d processes" % max_parallel
        print(msg)

    process_setup_args = (verbosity, start_at, start_after, test_labels)
    test_labels = setup_run_tests(*process_setup_args)
    # Run the test suite, including the extra validation tests.
    if not hasattr(settings, "TEST_RUNNER"):
        settings.TEST_RUNNER = "django.test.runner.DiscoverRunner"

    if parallel in {0, "auto"}:
        # This doesn't work before django.setup() on some databases.
        if all(conn.features.can_clone_databases for conn in connections.all()):
            parallel = max_parallel
        else:
            parallel = 1

    TestRunner = get_runner(settings)
    TestRunner.parallel_test_suite.process_setup = setup_run_tests
    TestRunner.parallel_test_suite.process_setup_args = process_setup_args
    test_runner = TestRunner(
        verbosity=verbosity,
        interactive=interactive,
        failfast=failfast,
        keepdb=keepdb,
        reverse=reverse,
        debug_sql=debug_sql,
        parallel=parallel,
        tags=tags,
        exclude_tags=exclude_tags,
        test_name_patterns=test_name_patterns,
        pdb=pdb,
        buffer=buffer,
        timing=timing,
        shuffle=shuffle,
        durations=durations,
    )
    failures = test_runner.run_tests(test_labels)
    teardown_run_tests()
    return failures


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the Django test suite.")
    parser.add_argument(
        "modules",
        nargs="*",
        metavar="module",
        help='Optional path(s) to test modules; e.g. "i18n" or "i18n.tests.TranslationTests.test_lazy_objects".',
    )
    parser.add_argument(
        "-v",
        "--verbosity",
        default=1,
        type=int,
        choices=[0, 1, 2, 3],
        help="Verbosity level; 0=minimal output, 1=normal output, 2=all output",
    )
    parser.add_argument(
        "--noinput",
        action="store_false",
        dest="interactive",
        help="Tells Django to NOT prompt the user for input of any kind.",
    )
    parser.add_argument(
        "--failfast",
        action="store_true",
        help="Tells Django to stop running the test suite after first failed test.",
    )
    parser.add_argument(
        "--keepdb",
        action="store_true",
        help="Tells Django to preserve the test database between runs.",
    )
    parser.add_argument(
        "--settings",
        help='Python path to settings module, e.g. "myproject.settings". If '
        "this isn't provided, either the DJANGO_SETTINGS_MODULE "
        'environment variable or "test_sqlite" will be used.',
    )
    parser.add_argument(
        "--shuffle",
        nargs="?",
        default=False,
        type=int,
        metavar="SEED",
        help=("Shuffle the order of test cases to help check that tests are properly isolated."),
    )
    parser.add_argument(
        "--reverse",
        action="store_true",
        help="Sort test suites and test cases in opposite order to debug "
        "test side effects not apparent with normal execution lineup.",
    )
    parser.add_argument(
        "--debug-sql",
        action="store_true",
        help="Turn on the SQL query logger within tests.",
    )
    # 0 is converted to "auto" or 1 later on, depending on a method used by
    # multiprocessing to start subprocesses and on the backend support for
    # cloning databases.
    parser.add_argument(
        "--parallel",
        nargs="?",
        const="auto",
        default=0,
        type=parallel_type,
        metavar="N",
        help=(
            'Run tests using up to N parallel processes. Use the value "auto" to run one test process for each processor core.'
        ),
    )
    parser.add_argument(
        "--tag",
        dest="tags",
        action="append",
        help="Run only tests with the specified tags. Can be used multiple times.",
    )
    parser.add_argument(
        "--exclude-tag",
        dest="exclude_tags",
        action="append",
        help="Do not run tests with the specified tag. Can be used multiple times.",
    )
    parser.add_argument(
        "--start-after",
        dest="start_after",
        help="Run tests starting after the specified top-level module.",
    )
    parser.add_argument(
        "--start-at",
        dest="start_at",
        help="Run tests starting at the specified top-level module.",
    )
    parser.add_argument("--pdb", action="store_true", help="Runs the PDB debugger on error or failure.")
    parser.add_argument(
        "-b",
        "--buffer",
        action="store_true",
        help="Discard output of passing tests.",
    )
    parser.add_argument(
        "--timing",
        action="store_true",
        help="Output timings, including database set up and total run time.",
    )
    parser.add_argument(
        "-k",
        dest="test_name_patterns",
        action="append",
        help=(
            "Only run test methods and classes matching test name pattern. "
            "Same as unittest -k option. Can be used multiple times."
        ),
    )
    if PY312:
        parser.add_argument(
            "--durations",
            dest="durations",
            type=int,
            default=None,
            metavar="N",
            help="Show the N slowest test cases (N=0 for all).",
        )

    options = parser.parse_args()

    # Allow including a trailing slash on app_labels for tab completion convenience
    options.modules = [os.path.normpath(labels) for labels in options.modules]
    mutually_exclusive_options = [
        options.start_at,
        options.start_after,
        options.modules,
    ]
    enabled_module_options = [bool(option) for option in mutually_exclusive_options].count(True)
    if enabled_module_options > 1:
        print("Aborting: --start-at, --start-after, and test labels are mutually exclusive.")
        sys.exit(1)
    for opt_name in ["start_at", "start_after"]:
        opt_val = getattr(options, opt_name)
        if opt_val:
            if "." in opt_val:
                print("Aborting: --%s must be a top-level module." % opt_name.replace("_", "-"))
                sys.exit(1)
            setattr(options, opt_name, os.path.normpath(opt_val))
    if options.settings:
        os.environ["DJANGO_SETTINGS_MODULE"] = options.settings
    else:
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "test_sqlite")
        options.settings = os.environ["DJANGO_SETTINGS_MODULE"]

    time_keeper = TimeKeeper() if options.timing else NullTimeKeeper()
    with time_keeper.timed("Total run"):
        failures = django_tests(
            options.verbosity,
            options.interactive,
            options.failfast,
            options.keepdb,
            options.reverse,
            options.modules,
            options.debug_sql,
            options.parallel,
            options.tags,
            options.exclude_tags,
            options.test_name_patterns,
            options.start_at,
            options.start_after,
            options.pdb,
            options.buffer,
            options.timing,
            options.shuffle,
            getattr(options, "durations", None),
        )
    time_keeper.print_results()
    if failures:
        sys.exit(1)
