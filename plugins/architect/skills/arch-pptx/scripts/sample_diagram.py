"""Build the arch-pptx sample: an order platform in the studio preset.

It uses a zone of each tint, a fence, a group, a box of each kind, chips,
data stores, a person and all four edge kinds with the async and two-way
modifiers. Run it as a template for a new diagram::

    uv run python sample_diagram.py out.pptx
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from studio_pptx import Diagram  # noqa: E402


def build() -> Diagram:
    """Place the sample diagram on one slide and return the deck."""
    d = Diagram()
    d.title(40, 30, 600, "Order platform")

    customer = d.person(40, 310, 140, 60, "Customer", sub="web · mobile")
    d.zone(240, 80, 740, 480, "Order platform", kind="internal")
    d.zone(1060, 280, 200, 160, "Partners", kind="external")
    d.zone(860, 580, 400, 120, "Archive", kind="repo")

    gateway = d.box(280, 310, 180, 60, "API gateway", sub="auth · limits", kind="gate")
    d.zone(270, 280, 200, 150, "Public edge", kind="fence")
    service = d.box(540, 310, 200, 60, "Orders service", code="orders-svc")
    d.box(280, 460, 180, 60, "Secrets", sub="signing keys", kind="secret")
    partner = d.box(1080, 310, 160, 60, "Billing partner", sub="SaaS")
    d.store(900, 620, 140, 60, "Cold storage", sub="S3")

    d.group(540, 120, 400, 140, "Kafka cluster")
    topic = d.chip(580, 180, 140, "orders.v1")
    dlq = d.chip(760, 180, 140, "orders.dlq", kind="deny")
    orders = d.store(800, 300, 140, 80, "orders", sub="PostgreSQL")
    replica = d.store(800, 440, 140, 80, "replica", sub="PostgreSQL")

    d.edge([customer.right(), gateway.left()], label="HTTPS", label_at=(190, 322))
    d.edge([gateway.right(), service.left()], kind="gate", label="checked")
    d.edge([service.right(), orders.left()], kind="ok", label="writes")
    d.edge([partner.left(), orders.right()], kind="deny", label="denied")
    d.edge(
        [service.top(0.55), topic.bottom()],
        is_async=True,
        label="publishes",
        label_at=(658, 272),
    )
    d.edge([topic.right(), dlq.left()], kind="deny", is_async=True)
    d.edge([orders.bottom(), replica.top()], two_way=True, label="replication")
    return d


def main(argv: list[str]) -> int:
    """Build the sample, print QA issues and save it to ``argv[1]``."""
    out = Path(argv[1]) if len(argv) > 1 else Path("arch-pptx-sample.pptx")
    d = build()
    issues = d.qa()
    for issue in issues:
        print(issue)
    d.save(out)
    print(f"saved {out}")
    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
