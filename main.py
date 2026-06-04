import sys
import time
import logging
import inspect
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Direct imports
from scripts.init_db import initialize_database
from scripts.import_leads import LeadImporter
from src.web.app import create_app


class AcademyOpsSetup:
    """Manages pre-flight setup for AcademyOps."""
    
    def __init__(self, 
                 db_path: str = "data/academyops.db",
                 import_csv: str = "data/messy_leads.csv",
                 quarantine_path: str = "data/quarantine.csv"):
        self.db_path = db_path
        self.import_csv = import_csv
        self.quarantine_path = quarantine_path
    
    def run_preflight_setup(self) -> bool:
        """Execute all setup scripts in order."""
        print("\n⚙️  Running Pre-flight Setup...\n")
        
        try:
            # 1. Initialize the Database
            print("   → Initializing Database...")
            initialize_database(self.db_path)
            print("     ✅ Database initialized.\n")
            
            # 2. Import the Leads
            print("   → Importing Leads Data...")
            importer = LeadImporter(
                db_path=self.db_path,
                quarantine_path=self.quarantine_path
            )
            importer.run_import(csv_input_path=self.import_csv)
            stats = importer.stats
            
            print(f"     ✅ Import complete: {stats['imported']} imported, "
                  f"{stats['skipped']} skipped, "
                  f"{stats['deduplicated']} deduplicated.\n")
            
            print("✅ Pre-flight Setup Complete!\n")
            return True
            
        except FileNotFoundError as e:
            logger.error(f"❌ File not found: {e}")
            logger.error(f"   Ensure these files exist:")
            logger.error(f"   - {self.import_csv}")
            logger.error(f"   - data/ folder")
            return False
        except ValueError as e:
            logger.error(f"❌ Validation error during import: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Setup failed: {e}", exc_info=True)
            return False


class AcademyOpsServices:
    """Manages running services (API + Dashboard)."""
    
    def __init__(self, db_path: str = "data/academyops.db", debug: bool = True):
        self.db_path = db_path
        self.debug = debug
        self.app = None
    
    def _create_app_smart(self):
        """
        Create Flask/FastAPI app, intelligently matching the function signature.
        This inspects create_app() to see what it actually accepts.
        """
        sig = inspect.signature(create_app)
        params = sig.parameters
        
        # Build kwargs based on what create_app actually accepts
        kwargs = {}
        
        if 'db_path' in params:
            kwargs['db_path'] = self.db_path
        
        if 'debug' in params:
            kwargs['debug'] = self.debug
        
        logger.debug(f"Calling create_app with: {kwargs}")
        return create_app(**kwargs)
    
    def start_services(self):
        """Start the API and Dashboard servers."""
        print("🚀 Starting AcademyOps Services...\n")
        
        try:
            # Create app with intelligent argument matching
            self.app = self._create_app_smart()
            print("   → API configured")
            print("   → Starting API at http://localhost:5000")
            print("   → Dashboard at http://localhost:8501\n")
            print("Press Ctrl+C to stop.\n")
            
            # Run services
            self._run_services()
            
        except Exception as e:
            logger.error(f"❌ Failed to start services: {e}", exc_info=True)
            sys.exit(1)
    
    def _run_services(self):
        """Run API and Dashboard concurrently."""
        import subprocess
        
        # Start Streamlit in background
        dashboard_process = subprocess.Popen(
            [sys.executable, "-m", "streamlit", "run", 
             "src/dashboard/app.py", "--logger.level=info"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        time.sleep(2)  # Give Streamlit time to boot
        
        try:
            # Run Flask in main thread
            if hasattr(self.app, 'run'):
                # Flask
                self.app.run(
                    host="0.0.0.0",
                    port=5000,
                    debug=self.debug,
                    use_reloader=False
                )
            else:
                # FastAPI - use uvicorn
                import uvicorn
                uvicorn.run(self.app, host="0.0.0.0", port=5000)
                
        except KeyboardInterrupt:
            print("\n\n🛑 Shutting down AcademyOps Services...\n")
            dashboard_process.terminate()
            try:
                dashboard_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                dashboard_process.kill()
            print("✅ All services stopped cleanly. Goodbye!\n")
        except Exception as e:
            dashboard_process.terminate()
            raise e


def main():
    """Main entry point for AcademyOps."""
    
    print("\n" + "="*60)
    print("🎓 ACADEMYOPS - Lead-to-Enrollment Management System")
    print("="*60)
    
    # Stage 1: Pre-flight setup
    setup = AcademyOpsSetup(
        db_path="data/academyops.db",
        import_csv="data/messy_leads.csv",
        quarantine_path="data/quarantine.csv"
    )
    
    if not setup.run_preflight_setup():
        logger.error("❌ Setup failed. Exiting.")
        sys.exit(1)
    
    # Stage 2: Start services
    services = AcademyOpsServices(
        db_path="data/academyops.db",
        debug=True
    )
    services.start_services()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nGoodbye!\n")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)