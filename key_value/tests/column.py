from key_value.tests.steps import *
from key_value.tests.checks import *


@TestOutline
def column_input(self, input, output, params, node=None):
    """Check that clickhouse extractKeyValuePairs function supports column input."""

    if node is None:
        node = self.context.node

    table_name = f"table_{getuid()}"

    if params != "":
        params = ", " + params

    with Given("I have a table"):
        create_partitioned_table(table_name=table_name, extra_table_col="")

    with When("I insert values into the table"):
        insert(table_name=table_name, x=input)
        expected_output = output.replace("\\", "\\\\").replace("'", "\\'")

    with Then("I check extractKeyValuePairs function returns correct value"):
        r = node.query(f"""select toString(extractKeyValuePairs(x{params})) from {table_name}""")
        assert r.output == expected_output, error()


@TestFeature
@Name("column")
@Requirements(RQ_SRS_033_ClickHouse_ExtractKeyValuePairs_InputDataSource_Column("1.0"))
def feature(self, node="clickhouse1"):
    """Check that clickhouse extractKeyValuePairs function support column input."""

    self.context.node = self.context.cluster.node(node)

    for check in checks:
        Feature(test=check)(scenario=column_input)
