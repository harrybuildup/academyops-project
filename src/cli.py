# src/cli.py
import argparse
import sys

from repository.lead_repository import LeadRepository
from models.lead import Lead, LeadStage
from models.errors import LeadNotFoundError, DuplicatePhoneError

def main():
    parser = argparse.ArgumentParser(
        description="AcademyOps CLI Lead Management Console"
    )
    subparsers = parser.add_subparsers(dest="command", help="Operational commands")

    # Command: 'add'
    add_parser = subparsers.add_parser("add", help="Register a brand new lead entry")
    add_parser.add_argument("--name", required=True, help="Full name of prospective student")
    add_parser.add_argument("--phone", required=True, help="Unique primary contact number")
    add_parser.add_argument("--source", required=False, default="Unknown", help="Lead discovery source channel")
    add_parser.add_argument("--notes", required=False, default="", help="Relevant background logs")

    # Command: 'list'
    subparsers.add_parser("list", help="View a tabular sequence of all leads")

    # Command: 'update-stage'
    update_parser = subparsers.add_parser("update-stage", help="Advance a lead along the pipeline")
    update_parser.add_argument("--id", type=int, required=True, help="Target lead numeric identifier")
    update_parser.add_argument(
        "--stage", 
        required=True, 
        choices=[stage.value for stage in LeadStage],
        help="Target destination pipeline sequence state"
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    # Initialize Repository layer pointing directly to the runtime file database
    repo = LeadRepository("data/academyops.db")

    try:
        if args.command == "add":
            # Instantiate your Lead Domain Model Object
            new_lead = Lead(
                id=None,  # Handled automatically by AUTOINCREMENT in SQLite
                name=args.name,
                phone=args.phone,
                source=args.source,
                stage=LeadStage.NEW.value,  # Starts as "New"
                notes=args.notes,
                created_at=None,  # Set by repository inside DB write
                updated_at=None
            )
            
            # Call your exact repo method name
            repo.add_lead(new_lead)
            print(f"SUCCESS: Successfully processed and registered new lead entry for {args.name}!")

        elif args.command == "list":
            # Call your exact repo method name
            leads = repo.get_all_leads()
            if not leads:
                print("No lead records currently recorded in the system of record.")
                return

            print(f"{'ID':<5} | {'Name':<15} | {'Phone':<15} | {'Source':<12} | {'Stage':<10}")
            print("-" * 65)
            for lead in leads:
                # Accessing data fields directly from your returned Lead domain objects
                print(f"{lead.id:<5} | {lead.name:<15} | {lead.phone:<15} | {lead.source:<12} | {lead.stage:<10}")

        elif args.command == "update-stage":
            # 1. Fetch the existing lead entity
            existing_lead = repo.get_lead_by_id(args.id)
            
            # 2. Modify the properties
            existing_lead.stage = args.stage
            
            # 3. Persist via your exact update method name
            repo.update_lead(existing_lead)
            print(f"SUCCESS: Lead ID {args.id} has been moved to pipeline stage: '{args.stage}'")

    except DuplicatePhoneError as e:
        print(f"OPERATION ERROR: Cannot create entry. {e}", file=sys.stderr)
        sys.exit(1)
    except LeadNotFoundError as e:
        print(f"OPERATION ERROR: Lookup execution failed. {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"UNEXPECTED FATAL EXCEPTION: An unhandled error occurred: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()