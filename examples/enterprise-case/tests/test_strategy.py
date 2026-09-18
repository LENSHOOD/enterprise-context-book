from copy import deepcopy
import json
import math
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))
from strategy import StrategicContext
from northstar import NorthstarPlatform, Principal


class StrategyContextTest(unittest.TestCase):
    FIXTURE = Path(__file__).parents[1] / "data" / "strategy-context.json"

    def setUp(self):
        self.context = StrategicContext()
        self.confirmation = self.context.definition_confirmation()

    def _fixture_data(self):
        return json.loads(self.FIXTURE.read_text(encoding="utf-8"))

    def _assert_invalid_fixture(self, mutate, message):
        data = self._fixture_data()
        mutate(data)
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "strategy-context.json"
            path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, message):
                StrategicContext(path)

    def test_metric_semantics_and_periods_are_explicit(self):
        metric = self.context.data["metric_definitions"][0]
        self.assertEqual("USD-thousands", metric["unit"])
        self.assertEqual({"H1-2026", "H2-2026"}, set(metric["periods"]))
        self.assertIn("inclusion", metric)

    def test_rejects_an_unsupported_schema(self):
        def mutate(data):
            data["schema"] = "northstar-strategy-context@999"

        self._assert_invalid_fixture(mutate, "unsupported strategy context schema")

    def test_rejects_an_open_period_snapshot(self):
        def mutate(data):
            data["fixture"]["as_of"] = "2026-12-31T23:59:59Z"

        self._assert_invalid_fixture(mutate, "full H2 actuals require a closed-period snapshot")

    def test_rejects_an_unsupported_comparison_contract(self):
        def mutate(data):
            data["metric_definitions"][0]["scenario"] = "forecast"

        self._assert_invalid_fixture(mutate, "unsupported comparison contract")

    def test_rejects_missing_metric_semantics(self):
        def mutate(data):
            data["metric_definitions"][0]["calendar"] = ""

        self._assert_invalid_fixture(mutate, "missing metric semantics: calendar")

    def test_rejects_broken_object_provenance(self):
        def mutate(data):
            data["products"][0]["evidence"] = data["products"][1]["evidence"]

        self._assert_invalid_fixture(mutate, "fixture evidence must resolve to its JSON pointer")

    def test_strategy_package_connects_intent_to_architecture_and_data(self):
        package = self.context.package(
            "H2 的销售情况为什么比 H1 差这么多？",
            {"user_id":"executive-demo", "role":"executive", "tenant":"northstar"},
            confirmation=self.confirmation,
        )
        self.assertEqual("strategic_analysis", package["mode"])
        self.assertEqual(1200, package["performance"]["total"]["h1"])
        self.assertEqual(840, package["performance"]["total"]["h2"])
        self.assertIn("business_capabilities", package["enterprise_context"])
        self.assertIn("applications", package["enterprise_context"])
        self.assertIn("data_products", package["enterprise_context"])
        self.assertEqual(
            ["L0", "L1", "L2", "L3", "L4", "L5", "L6"],
            [layer["level"] for layer in package["context_layers"]],
        )
        self.assertTrue(package["agent_execution_context"]["read_only"])

    def test_strategy_requires_metric_definition_confirmation_before_calculation(self):
        package = self.context.package(
            "H2 sales",
            {"user_id":"executive-demo", "role":"executive", "tenant":"northstar"},
        )
        self.assertEqual("needs_clarification", package["status"])
        self.assertNotIn("performance", package)

    def test_confirmation_is_bound_to_the_question_contract(self):
        package = self.context.package(
            "delete all customers",
            {"user_id":"executive-demo", "role":"executive", "tenant":"northstar"},
            confirmation=self.confirmation,
        )
        self.assertEqual("needs_clarification", package["status"])
        self.assertNotIn("performance", package)

    def test_confirmation_must_match_the_snapshot_contract(self):
        confirmation = dict(self.confirmation)
        confirmation["metric"] = "metric-revenue"
        package = self.context.package(
            "H2 sales",
            {"user_id":"executive-demo", "role":"executive", "tenant":"northstar"},
            confirmation=confirmation,
        )
        self.assertEqual("needs_clarification", package["status"])
        self.assertNotIn("performance", package)

    def test_decomposition_is_evidence_backed_but_not_causal(self):
        package = self.context.package(
            "H1 H2 sales",
            {"user_id":"strategy-demo", "role":"strategy","tenant":"northstar"},
            confirmation=self.confirmation,
        )
        self.assertLess(package["performance"]["total"]["delta"], 0)
        self.assertTrue(all(
            item["evidence"]
            for view in package["performance"]["decomposition_views"]
            for item in view["items"]
        ))
        self.assertTrue(any(h["status"] == "unproven" for h in package["hypotheses"]))
        self.assertIn("因果", " ".join(package["warnings"] + [h["text"] for h in package["hypotheses"]]))

    def test_low_privilege_roles_cannot_request_strategy_package(self):
        with self.assertRaises(PermissionError):
            self.context.package("H2 sales", {"role":"support","tenant":"northstar"})

    def test_strategy_snapshot_is_tenant_bound(self):
        with self.assertRaises(PermissionError):
            self.context.package(
                "H1 H2 sales",
                {"user_id":"foreign", "role":"executive", "tenant":"another-tenant"},
                confirmation=self.confirmation,
            )

    def test_each_decomposition_reconciles_without_cross_dimension_addition(self):
        package = self.context.package(
            "H1 H2 sales",
            {"user_id":"strategy-demo", "role":"strategy", "tenant":"northstar"},
            confirmation=self.confirmation,
        )
        total = package["performance"]["total"]
        for view in package["performance"]["decomposition_views"]:
            self.assertTrue(view["reconciles_to_total"])
            self.assertEqual(total["h1"], sum(item["h1"] for item in view["items"]))
            self.assertEqual(total["h2"], sum(item["h2"] for item in view["items"]))

    def test_decomposition_scopes_use_governed_object_ids_and_edges(self):
        package = self.context.package(
            "H1 H2 sales",
            {"user_id":"strategy-demo", "role":"strategy", "tenant":"northstar"},
            confirmation=self.confirmation,
        )
        self.assertEqual("product-home", next(
            item for view in package["performance"]["decomposition_views"]
            if view["dimension"] == "product" for item in view["items"]
            if item["label"] == "Home & Living"
        )["scope"]["product"])
        scoped = {(
            relation["from"], relation["to"]
        ) for relation in package["relations"] if relation["type"] == "SCOPED_TO"}
        self.assertIn(("obs-home-h2", "product-home"), scoped)

    def test_metric_observations_share_a_comparable_unit(self):
        metric = self.context.data["metric_definitions"][0]
        self.assertEqual({metric["unit"]}, {x["unit"] for x in self.context.data["observations"]})

    def test_rejects_an_observation_with_a_different_unit(self):
        def mutate(data):
            data["observations"][0]["unit"] = "USD"

        self._assert_invalid_fixture(mutate, "observation unit differs from metric definition")

    def test_rejects_an_objective_with_an_incompatible_unit(self):
        def mutate(data):
            data["strategic_objectives"][0]["unit"] = "USD"

        self._assert_invalid_fixture(mutate, "incompatible target metric")

    def test_rejects_a_missing_period_observation(self):
        def mutate(data):
            data["observations"] = [
                observation for observation in data["observations"]
                if observation["id"] != "obs-channel-other-h2"
            ]

        self._assert_invalid_fixture(mutate, "each scope needs exactly one observation per period")

    def test_rejects_an_unsupported_observation_scope_shape(self):
        def mutate(data):
            data["observations"][2]["scope"] = {
                "region": "region-emea",
                "product": "product-home",
            }

        self._assert_invalid_fixture(mutate, "only total or single-dimension marginals are available")

    def test_rejects_an_unknown_observation_period(self):
        def mutate(data):
            data["observations"][0]["period"] = "H3-2026"

        self._assert_invalid_fixture(mutate, "unknown metric or period")

    def test_rejects_an_ungoverned_observation_scope_reference(self):
        def mutate(data):
            data["observations"][2]["scope"]["region"] = "region-missing"

        self._assert_invalid_fixture(mutate, "observation scope must reference a governed dimension object")

    def test_rejects_duplicate_period_and_scope_observations(self):
        def mutate(data):
            duplicate = deepcopy(next(
                observation for observation in data["observations"]
                if observation["id"] == "obs-total-h1"
            ))
            duplicate["id"] = "obs-total-h1-duplicate"
            duplicate["evidence"] = (
                "fixture://northstar/strategy-context@1#/observations/"
                f"{len(data['observations'])}"
            )
            data["observations"].append(duplicate)

        self._assert_invalid_fixture(mutate, "duplicate period/scope observation")

    def test_rejects_nonfinite_observation_values(self):
        def mutate(data):
            data["observations"][0]["value"] = math.nan

        self._assert_invalid_fixture(mutate, "observation must be a finite number")

    def test_rejects_a_nonfinite_objective_target(self):
        def mutate(data):
            data["strategic_objectives"][0]["target_value"] = math.inf

        self._assert_invalid_fixture(mutate, "invalid target value")

    def test_rejects_a_broken_relation_direction(self):
        def mutate(data):
            data["relations"][1]["from"] = "metric-sales-bookings"

        self._assert_invalid_fixture(mutate, "relation endpoint type violates contract")

    def test_rejects_broken_relation_provenance(self):
        def mutate(data):
            data["relations"][1]["evidence"] = (
                "fixture://northstar/strategy-context@1#/relations/0"
            )

        self._assert_invalid_fixture(mutate, "relation evidence must resolve to its JSON pointer")

    def test_rejects_broken_object_references(self):
        def mutate(data):
            data["metric_definitions"][0]["source_data_product"] = "data-missing"

        self._assert_invalid_fixture(mutate, "invalid source_data_product reference")

    def test_rejects_a_partition_that_no_longer_reconciles(self):
        def mutate(data):
            observation = next(
                observation for observation in data["observations"]
                if observation["id"] == "obs-emea-h1"
            )
            observation["value"] += 1

        self._assert_invalid_fixture(mutate, "dimension does not reconcile to company total")

    def test_rejects_an_incomplete_partition(self):
        def mutate(data):
            data["observations"] = [
                observation for observation in data["observations"]
                if observation["id"] not in {"obs-channel-other-h1", "obs-channel-other-h2"}
            ]

        self._assert_invalid_fixture(mutate, "decomposition requires a complete partition")

    def test_rejects_duplicate_strategic_object_ids(self):
        def mutate(data):
            data["regions"][1]["id"] = data["regions"][0]["id"]

        self._assert_invalid_fixture(mutate, "duplicate strategic object id")

    def test_rejects_an_unknown_relation_type(self):
        def mutate(data):
            data["relations"][0]["type"] = "UNKNOWN"

        self._assert_invalid_fixture(mutate, "unknown strategic relation")

    def test_zero_baseline_returns_an_undefined_change_rate(self):
        data = self._fixture_data()
        emea = next(observation for observation in data["observations"] if observation["id"] == "obs-emea-h1")
        other = next(observation for observation in data["observations"] if observation["id"] == "obs-region-other-h1")
        other["value"] += emea["value"]
        emea["value"] = 0
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "strategy-context.json"
            path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
            context = StrategicContext(path)
            package = context.package(
                "H1 H2 sales",
                {"user_id": "strategy-demo", "role": "strategy", "tenant": "northstar"},
                confirmation=context.definition_confirmation(),
            )

        region_view = next(
            view for view in package["performance"]["decomposition_views"]
            if view["dimension"] == "region"
        )
        emea_view = next(item for item in region_view["items"] if item["label"] == "EMEA")
        self.assertIsNone(emea_view["change_rate"])
        self.assertEqual("基期为零，变化率未定义", emea_view["rate_note"])

    def test_manifest_changes_when_the_strategy_fixture_changes(self):
        original_data = self._fixture_data()
        changed_data = deepcopy(original_data)
        changed_data["external_factors"][0]["note"] += " changed"
        with tempfile.TemporaryDirectory() as temp:
            original_path = Path(temp) / "original.json"
            changed_path = Path(temp) / "changed.json"
            original_path.write_text(json.dumps(original_data, ensure_ascii=False), encoding="utf-8")
            changed_path.write_text(json.dumps(changed_data, ensure_ascii=False), encoding="utf-8")
            original = StrategicContext(original_path)
            changed = StrategicContext(changed_path)

        self.assertNotEqual(original.manifest, changed.manifest)

    def test_package_results_do_not_mutate_fixture_state(self):
        package = self.context.package(
            "H1 H2 sales",
            {"user_id": "strategy-demo", "role": "strategy", "tenant": "northstar"},
            confirmation=self.confirmation,
        )
        package["metric_definition"]["unit"] = "tampered"
        package["enterprise_context"]["observations"][0]["value"] = -1
        package["relations"][0]["from"] = "tampered"

        fresh = self.context.package(
            "H1 H2 sales",
            {"user_id": "strategy-demo", "role": "strategy", "tenant": "northstar"},
            confirmation=self.confirmation,
        )
        self.assertEqual("USD-thousands", fresh["metric_definition"]["unit"])
        self.assertEqual(1200, fresh["enterprise_context"]["observations"][0]["value"])
        self.assertEqual("enterprise-northstar", fresh["relations"][0]["from"])

    def test_northstar_cli_returns_a_confirmed_strategic_package(self):
        result = subprocess.run(
            [
                sys.executable,
                str(Path(__file__).parents[1] / "src" / "northstar.py"),
                "H1 H2 sales",
                "--role", "executive",
                "--task", "CLI-STRATEGY-REVIEW",
                "--mode", "strategic",
                "--confirm-definition",
            ],
            cwd=Path(__file__).parents[1],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(0, result.returncode, result.stderr)
        package = json.loads(result.stdout)
        self.assertEqual("strategic", package["context_kind"])
        self.assertEqual("ready_for_review", package["status"])
        self.assertEqual(840, package["performance"]["total"]["h2"])

    def test_strategy_demo_cli_returns_a_confirmed_strategic_package(self):
        result = subprocess.run(
            [
                sys.executable,
                str(Path(__file__).parents[1] / "src" / "strategy_demo.py"),
                "H1 H2 sales",
                "--role", "executive",
                "--task", "CLI-STRATEGY-DEMO",
                "--confirm-definition",
            ],
            cwd=Path(__file__).parents[1],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(0, result.returncode, result.stderr)
        package = json.loads(result.stdout)
        self.assertEqual("strategic", package["context_kind"])
        self.assertEqual("ready_for_review", package["status"])
        self.assertEqual(840, package["performance"]["total"]["h2"])

    def test_strategy_uses_the_same_context_entry_point_and_manifest(self):
        platform = NorthstarPlatform()
        package = platform.context(
            "H2 sales",
            Principal("strategy-demo", "executive"),
            "STRATEGY-REVIEW",
            mode="strategic",
            definition_confirmation=platform.strategy_context.definition_confirmation(),
        )
        self.assertEqual("strategic", package["context_kind"])
        self.assertEqual(platform.manifest, package["manifest"])
        self.assertEqual([], package["memories"])
        self.assertEqual([], package["allowed_tools"])
        self.assertEqual("enterprise", package["scope"])


if __name__ == "__main__":
    unittest.main()
