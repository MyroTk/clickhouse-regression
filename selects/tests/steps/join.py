from selects.tests.steps.main_steps import *


@TestStep(Given)
@Name("join step")
def join_step(self, table, tables_auxiliary, join_type="INNER JOIN", node=None):
    """Execute select some join type query without `FINAL` clause and with --final setting disabled."""
    if node is None:
        node = self.context.cluster.node("clickhouse1")

    with When(f"I make {join_type} {tables_auxiliary[0].name} on {table.name}"):
        node.query(
            f"SELECT count() FROM {table.name} {join_type}"
            f" {tables_auxiliary[0].name} on {table.name}.id = {tables_auxiliary[0].name}.id",
            settings=[("final", 0)],
        ).output.strip()


@TestStep(Given)
def join_with_force_final(self, table, tables_auxiliary, join_type="INNER JOIN", node=None):
    """Execute select some join type query without `FINAL` clause and with --final setting enabled."""
    if node is None:
        node = self.context.cluster.node("clickhouse1")

    with When(
        f"I make {join_type} {tables_auxiliary[0].name} on {table} with --final enabled"
    ):
        node.query(
            f"SELECT count() FROM {table} {join_type}"
            f" {tables_auxiliary[0]} on {table}.id = {tables_auxiliary[0]}.id",
            settings=[("final", 1)],
        ).output.strip()


@TestStep(Given)
def join_with_final_on_left_table(self, table, tables_auxiliary, join_type="INNER JOIN", node=None):
    """Execute select some join type query with `FINAL` clause on left table and with --final setting disabled."""
    if node is None:
        node = self.context.cluster.node("clickhouse1")

    with When(f"I make {join_type} {tables_auxiliary[0].name} on {table} with left 'FINAL'"):
        node.query(
            f"SELECT count() FROM {table} "
            f"{' FINAL' if table.final_modifier_available else ''} {join_type}"
            f" {tables_auxiliary[0]} on {table}.id = {tables_auxiliary[0]}.id",
            settings=[("final", 0)],
        ).output.strip()


@TestStep(Given)
def join_with_final_on_left_table_with_force_final(
    self, table, tables_auxiliary, join_type="INNER JOIN", node=None
):
    """Execute select some join type query with `FINAL` clause on left table and with --final setting enabled."""
    if node is None:
        node = self.context.cluster.node("clickhouse1")

    with When(
        f"I make {join_type} {tables_auxiliary[0].name} on {table} with left 'FINAL' with --final enabled"
    ):
        node.query(
            f"SELECT count() FROM {table.name} "
            f"{' FINAL' if table.final_modifier_available else ''} {join_type}"
            f" {tables_auxiliary[0].name} on {table}.id = {tables_auxiliary[0].name}.id",
            settings=[("final", 1)],
        ).output.strip()


@TestStep(Given)
def join_with_final_on_right_table(self, table, tables_auxiliary, join_type="INNER JOIN", node=None):
    """Execute select some join type query with `FINAL` clause on right table and with --final setting disabled."""
    if node is None:
        node = self.context.cluster.node("clickhouse1")

    with When(
        f"I make {join_type} {tables_auxiliary[0].name} on {table} with right 'FINAL'"
    ):
        node.query(
            f"SELECT count() FROM {table} {join_type}"
            f" {tables_auxiliary[0].name} {' FINAL' if tables_auxiliary[0].final_modifier_available else ''} on {table}.id = {tables_auxiliary[0].name}.id",
            settings=[("final", 0)],
        ).output.strip()


@TestStep(Given)
def join_with_final_on_right_table_with_force_final(
    self, table, tables_auxiliary, join_type="INNER JOIN", node=None
):
    """Execute select some join type query with `FINAL` clause on right table and with --final setting enabled."""
    if node is None:
        node = self.context.cluster.node("clickhouse1")

    with When(
        f"I make {join_type} {tables_auxiliary[0].name} on {table} with right 'FINAL' with --final enabled"
    ):
        node.query(
            f"SELECT count() FROM {table} {join_type}"
            f" {tables_auxiliary[0].name} {' FINAL' if tables_auxiliary[0].final_modifier_available else ''} on {table}.id = {tables_auxiliary[0].name}.id",
            settings=[("final", 1)],
        ).output.strip()


@TestStep(Given)
def join_with_final_on_both_tables(self, table, tables_auxiliary, join_type="INNER JOIN", node=None):
    """Execute select some join type query with `FINAL` clause on both tables and with --final setting disabled."""
    if node is None:
        node = self.context.cluster.node("clickhouse1")

    with When(
        f"I make {join_type} {tables_auxiliary[0].name} on {table} with both tables 'FINAL'"
    ):
        node.query(
            f"SELECT count() FROM {table} {' FINAL' if table.final_modifier_available else ''} {join_type}"
            f" {tables_auxiliary[0].name} {' FINAL' if tables_auxiliary[0].final_modifier_available else ''} on {table}.id = {tables_auxiliary[0].name}.id",
            settings=[("final", 0)],
        ).output.strip()


@TestStep(Given)
def join_with_final_on_both_tables_with_force_final(
    self, table, tables_auxiliary, join_type="INNER JOIN", node=None
):
    """Execute select some join type query with `FINAL` clause on both tables and with --final setting enabled."""
    if node is None:
        node = self.context.cluster.node("clickhouse1")

    with When(
        f"I make {join_type} {tables_auxiliary[0]} on {table} with both tables 'FINAL' with --final enabled"
    ):
        node.query(
            f"SELECT count() FROM {table} {' FINAL' if table.final_modifier_available else ''} {join_type}"
            f" {tables_auxiliary[0].name} {' FINAL' if tables_auxiliary[0].final_modifier_available else ''} on {table}.id = {tables_auxiliary[0].name}.id",
            settings=[("final", 1)],
        ).output.strip()
