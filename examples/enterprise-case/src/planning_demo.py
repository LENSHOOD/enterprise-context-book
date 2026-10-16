"""Compare real reads for two refund plans; estimated costs are illustrative."""
import argparse
import json

from northstar import NorthstarPlatform, Principal
from query_planning import compare_refund_plans


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--role", default="sre")
    parser.add_argument("--estimated-budget", type=int, default=60)
    args = parser.parse_args()
    print(json.dumps(compare_refund_plans(NorthstarPlatform(), Principal("plan-reader", args.role),
                                         args.estimated_budget), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
