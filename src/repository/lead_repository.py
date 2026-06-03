from src.database.connections import create_connection, close_connection
import sqlite3
from datetime import datetime
from src.models.lead import Lead
from src.models.errors import LeadNotFoundError, DuplicatePhoneError
from src.utils.logger import logger

class LeadRepository:
    def __init__(self, db_file):
        self.db_file = db_file

    def add_lead(self, lead: Lead):
        conn = create_connection(self.db_file)
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO leads (name, phone, source, stage, notes, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (lead.name, lead.phone, lead.source, lead.stage, lead.notes,
                  datetime.now().isoformat(), datetime.now().isoformat()))
            conn.commit()
            logger.info(f"Lead added: {lead.name} ({lead.phone})")
        except sqlite3.IntegrityError:
            logger.error(f"Duplicate phone number: {lead.phone}")
            raise DuplicatePhoneError(f"Phone number {lead.phone} already exists.")
        finally:
            close_connection(conn)
    
    def get_all_leads(self) -> list[Lead]:
        conn = create_connection(self.db_file)
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM leads")
            rows = cursor.fetchall()
            return [Lead(*row) for row in rows]
        finally:
            close_connection(conn)  

    def get_lead_by_id(self, lead_id: int) -> Lead:
        conn = create_connection(self.db_file)
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM leads WHERE id = ?", (lead_id,))
            row = cursor.fetchone()
            if row:
                return Lead(*row)
            else:
                logger.warning(f"Lead not found with ID: {lead_id}")
                raise LeadNotFoundError(f"Lead with ID {lead_id} not found.")
        finally:
            close_connection(conn)

    def update_lead(self, lead: Lead):
        conn = create_connection(self.db_file)
        try:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE leads
                SET name = ?, phone = ?, source = ?, stage = ?, notes = ?, updated_at = ?
                WHERE id = ?
            """, (lead.name, lead.phone, lead.source, lead.stage, lead.notes,
                  datetime.now().isoformat(), lead.id))
            if cursor.rowcount == 0:
                logger.warning(f"Lead not found for update with ID: {lead.id}")
                raise LeadNotFoundError(f"Lead with ID {lead.id} not found.")
            conn.commit()
            logger.info(f"Lead updated: {lead.name} ({lead.phone})")
        except sqlite3.IntegrityError:
            logger.error(f"Duplicate phone number on update: {lead.phone}")
            raise DuplicatePhoneError(f"Phone number {lead.phone} already exists.")
        finally:
            close_connection(conn)

    def delete_lead(self, lead_id: int):
        conn = create_connection(self.db_file)
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM leads WHERE id = ?", (lead_id,))
            if cursor.rowcount == 0:
                logger.warning(f"Lead not found for deletion with ID: {lead_id}")
                raise LeadNotFoundError(f"Lead with ID {lead_id} not found.")
            conn.commit()
            logger.info(f"Lead deleted: {lead_id}")
        finally:
            close_connection(conn)
