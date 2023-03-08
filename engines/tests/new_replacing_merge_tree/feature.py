import sys

from testflows.core import *
from engines.requirements import *
from engines.tests.steps import *
from helpers.common import check_clickhouse_version


append_path(sys.path, "..")


@TestModule
@Name("new_replacing_merge_tree")
def feature(self):
    """Check new ReplacingMergeTree engine."""
    Feature(run=load("new_replacing_merge_tree.general", "feature"))
