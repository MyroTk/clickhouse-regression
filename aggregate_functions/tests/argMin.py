import itertools

from helpers.tables import common_columns
from aggregate_functions.tests.steps import *
from aggregate_functions.requirements import (
    RQ_SRS_031_ClickHouse_AggregateFunctions_Specific_ArgMin,
)


@TestCheck
def execute_multi_query(self, query):
    """Execute multi query statement."""
    execute_query("".join(query), use_file=True, format=None, hash_output=False)


@TestCheck
def datatype(self, func, table, col1_name, col2_name):
    """Check different column types."""
    execute_query(
        f"SELECT {func.format(params=col1_name+','+col2_name)} FROM {table.name} FORMAT JSONEachRow"
    )


@TestFeature
@Name("argMin")
@Requirements(RQ_SRS_031_ClickHouse_AggregateFunctions_Specific_ArgMin("1.0"))
def feature(self, func="argMin({params})", table=None):
    """Check argMin or argMax or one of their combinator aggregate functions. By default: argMin."""
    self.context.snapshot_id = name.basename(current().name)

    if table is None:
        table = self.context.table

    with Check("constant"):
        execute_query(f"SELECT {func.format(params='1,2')}")

    with Check("zero rows"):
        execute_query(
            f"SELECT {func.format(params='number, number+1')} FROM numbers(0)"
        )

    with Check("with group by"):
        execute_query(
            f"SELECT number % 2 AS even, {func.format(params='number, even')} FROM numbers(10) GROUP BY even"
        )

    with Check("NULL value handling"):
        execute_query(
            f"SELECT {func.format(params='x, y')} FROM values('x Nullable(Int8), y Nullable(String)', (1, NULL), (NULL, 'hello'), (3, 'there'), (NULL, NULL), (5, 'you'))"
        )

    with Check("doc example"):
        execute_query(
            f"SELECT {func.format(params='user, salary')} FROM values('user String, salary Float64',('director',5000),('manager',3000),('worker', 1000))"
        )

    with Feature("datatypes"):
        with Pool(3) as executor:
            for column in table.columns:
                col_name, col_type = column.split(" ", 1)
                Check(
                    f"String,{col_type}",
                    test=datatype,
                    parallel=True,
                    executor=executor,
                )(func=func, table=table, col1_name="string", col2_name=col_name)
                Check(
                    f"{col_type},String",
                    test=datatype,
                    parallel=True,
                    executor=executor,
                )(func=func, table=table, col1_name=col_name, col2_name="string")

            join()

        with Feature(
            "permutations",
            description="sanity check most common column type permutations",
        ):
            with Pool(3) as executor:
                columns = [col for col in table.columns if col in common_columns]
                permutations = list(permutations_with_replacement(columns, 2))
                permutations.sort()

                for col1, col2 in permutations:
                    col1_name, col1_type = col1.split(" ", 1)
                    col2_name, col2_type = col2.split(" ", 1)
                    # we already cover String data type above so skip it here
                    if col1_type == "String" or col2_type == "String":
                        continue
                    Check(
                        f"{col1_type},{col2_type}",
                        test=datatype,
                        parallel=True,
                        executor=executor,
                    )(func=func, table=table, col1_name=col1_name, col2_name=col2_name)

                join()
