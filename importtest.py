import sys
import os


def pytest_sessionfinish(session, exitstatus):
    # pip has no official API, nor correct cli options
    imported = set[str](
        line.split(" ")[0] for i, line in enumerate(os.popen("pip list")) if i > 2
    )

    print("""

=== Imported external libraries during tests ===
/!\\ With low test coverage, imports done by the code can be miss.
""")
    for name in sorted(sys.modules.keys()):
        if name in imported:
            print(name)
