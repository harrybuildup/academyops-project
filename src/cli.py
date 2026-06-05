"""src/cli.py — Command-line interface for AcademyOps (WP-01).

Usage examples
--------------
    python -m src.cli add --name "Alice" --phone "9876543210" --source Google
    python -m src.cli list
    python -m src.cli update-stage --id 1 --stage Contacted
    python -m src.cli delete --id 1
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Ensure project root is on the path when invoked directly
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from src.database.connections import get_session_factory
from src.database.schemas import create_tables
from src.models.errors import DuplicatePhoneError, LeadNotFoundError
from src.models.lead import LeadORM, LeadStage


def _session():
    return get_session_factory()()


def cmd_add(args: argparse.Namespace) -> None:
    create_tables()
    db = _session()
    try:
        lead = LeadORM(
            name=args.name,
            phone=args.phone,
            source=args.source,
            stage=LeadStage.NEW.value,
            notes=args.notes or "",
        )
        db.add(lead)
        db.commit()
        db.refresh(lead)
        print(f"✅  Created lead: id={lead.id}  name={lead.name!r}  stage={lead.stage}")
    except Exception as exc:
        db.rollback()
        if "unique" in str(exc).lower() or "duplicate" in str(exc).lower():
            print(f"❌  Phone '{args.phone}' already exists.", file=sys.stderr)
        else:
            print(f"❌  {exc}", file=sys.stderr)
        sys.exit(1)
    finally:
        db.close()


def cmd_list(args: argparse.Namespace) -> None:
    db = _session()
    try:
        leads = db.query(LeadORM).order_by(LeadORM.id).all()
        if not leads:
            print("No leads found.")
            return
        print(f"{'ID':<5} {'Name':<20} {'Phone':<16} {'Source':<12} {'Stage':<12}")
        print("─" * 70)
        for lead in leads:
            print(f"{lead.id:<5} {lead.name:<20} {lead.phone:<16} {(lead.source or ''):<12} {lead.stage:<12}")
    finally:
        db.close()


def cmd_update_stage(args: argparse.Namespace) -> None:
    db = _session()
    try:
        lead = db.query(LeadORM).filter(LeadORM.id == args.id).first()
        if not lead:
            raise LeadNotFoundError(f"Lead id {args.id} not found.")
        lead.stage = args.stage
        db.commit()
        print(f"✅  Lead {args.id} → stage '{args.stage}'")
    except LeadNotFoundError as exc:
        print(f"❌  {exc}", file=sys.stderr)
        sys.exit(1)
    finally:
        db.close()


def cmd_delete(args: argparse.Namespace) -> None:
    db = _session()
    try:
        lead = db.query(LeadORM).filter(LeadORM.id == args.id).first()
        if not lead:
            raise LeadNotFoundError(f"Lead id {args.id} not found.")
        db.delete(lead)
        db.commit()
        print(f"✅  Lead {args.id} deleted.")
    except LeadNotFoundError as exc:
        print(f"❌  {exc}", file=sys.stderr)
        sys.exit(1)
    finally:
        db.close()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="academyops",
        description="AcademyOps CLI — manage leads from the command line.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # add
    p_add = sub.add_parser("add", help="Register a new lead")
    p_add.add_argument("--name",   required=True)
    p_add.add_argument("--phone",  required=True)
    p_add.add_argument("--source", default="Unknown")
    p_add.add_argument("--notes",  default="")

    # list
    sub.add_parser("list", help="List all leads")

    # update-stage
    p_upd = sub.add_parser("update-stage", help="Advance a lead's pipeline stage")
    p_upd.add_argument("--id",    type=int, required=True)
    p_upd.add_argument("--stage", required=True,
                       choices=[s.value for s in LeadStage])

    # delete
    p_del = sub.add_parser("delete", help="Delete a lead")
    p_del.add_argument("--id", type=int, required=True)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    dispatch = {
        "add":          cmd_add,
        "list":         cmd_list,
        "update-stage": cmd_update_stage,
        "delete":       cmd_delete,
    }
    dispatch[args.command](args)


if __name__ == "__main__":
    main()
