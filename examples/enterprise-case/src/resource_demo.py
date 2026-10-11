"""Read a refund business explanation, then discover its runtime evidence."""
import json
from northstar import NorthstarPlatform, Principal
from resource_discovery import investigate_refund


def main():
    platform = NorthstarPlatform()
    print(json.dumps({"build": platform.resources.report,
                      "investigation": investigate_refund(platform, Principal("new-reader", "sre"))},
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
