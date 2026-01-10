"""
Historie tracking setup - Event listeners voor automatische historie logging
"""
from sqlalchemy import event
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from contextvars import ContextVar
from typing import Optional
import uuid

from app.db.session import SessionLocal

# Context variables voor tracking
_user_id: ContextVar[Optional[str]] = ContextVar('user_id', default=None)
_opmerking: ContextVar[Optional[str]] = ContextVar('opmerking', default=None)


class HistorieContext:
    """Context manager voor historie tracking"""

    def __init__(self, db: Session, user_id: str, actie: str, tabel: str, record_id: str, opmerking: Optional[str] = None):
        """
        Initialize historie context

        Args:
            db: Database session
            user_id: ID of user performing action
            actie: Type of action (create, update, delete)
            tabel: Table name
            record_id: Record ID
            opmerking: Optional comment
        """
        self.db = db
        self.user_id = user_id
        self.actie = actie
        self.tabel = tabel
        self.record_id = record_id
        self.opmerking = opmerking
        self._previous_user_id = None
        self._previous_opmerking = None

    def __enter__(self):
        """Enter context - set user ID and opmerking"""
        self._previous_user_id = _user_id.get()
        self._previous_opmerking = _opmerking.get()
        _user_id.set(self.user_id)
        if self.opmerking:
            _opmerking.set(self.opmerking)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context - restore previous values"""
        _user_id.set(self._previous_user_id)
        _opmerking.set(self._previous_opmerking)
        return False

    @staticmethod
    def set_user_id(user_id: str):
        """Set user ID voor huidige operatie"""
        _user_id.set(user_id)

    @staticmethod
    def set_opmerking(opmerking: str):
        """Set opmerking voor huidige operatie"""
        _opmerking.set(opmerking)

    @staticmethod
    def get_user_id() -> Optional[str]:
        """Get current user ID"""
        return _user_id.get()

    @staticmethod
    def get_opmerking() -> Optional[str]:
        """Get current opmerking"""
        return _opmerking.get()

    @staticmethod
    def clear():
        """Clear context"""
        _user_id.set(None)
        _opmerking.set(None)


# ✅ NIEUWE FUNCTIES: Disable/Enable historie tracking
def disable_historie_tracking(session: Session):
    """
    Disable historie tracking voor bulk operations zoals seeding
    
    Args:
        session: SQLAlchemy session
    """
    session.info['disable_historie'] = True


def enable_historie_tracking(session: Session):
    """
    Re-enable historie tracking na bulk operations
    
    Args:
        session: SQLAlchemy session
    """
    session.info['disable_historie'] = False


# Models die historie tracking hebben
TRACKED_MODELS = [
    'User',
    'Project',
    'Contract',
    'Leverancier',
    'Vestiging',
    'ProjectFase',
    'ProjectFaseDocument',
    'ProjectFaseCommentaar'
]


def should_track_model(obj) -> bool:
    """Check of dit model getrackt moet worden"""
    return obj.__class__.__name__ in TRACKED_MODELS


def create_historie_record(session: Session, obj, actie: str, oude_waarde: dict = None, nieuwe_waarde: dict = None):
    """
    Maak een historie record
    
    Args:
        session: SQLAlchemy session
        obj: Het object dat gewijzigd is
        actie: Type actie (INSERT, UPDATE, DELETE)
        oude_waarde: Dict met oude waardes (voor UPDATE/DELETE)
        nieuwe_waarde: Dict met nieuwe waardes (voor INSERT/UPDATE)
    """
    # ✅ CHECK: Is historie tracking disabled?
    if session.info.get('disable_historie', False):
        return
    
    from app.models.historie import Historie
    
    # Get context info
    user_id = HistorieContext.get_user_id()
    opmerking = HistorieContext.get_opmerking()
    
    # Bepaal tabel en record info
    tabel_naam = obj.__class__.__tablename__
    record_id = str(obj.id) if hasattr(obj, 'id') else None
    
    # Maak historie record
    historie = Historie(
        id=str(uuid.uuid4()),
        tabel_naam=tabel_naam,
        record_id=record_id,
        actie=actie,
        oude_waarde=oude_waarde,
        nieuwe_waarde=nieuwe_waarde,
        uitgevoerd_door_id=user_id,
        uitgevoerd_op=datetime.now(timezone.utc),
        opmerking=opmerking
    )
    
    session.add(historie)


@event.listens_for(Session, "before_flush")
def before_flush(session, flush_context, instances):
    """
    Track changes before flush
    """
    # ✅ CHECK: Is historie tracking disabled?
    if session.info.get('disable_historie', False):
        return
    
    # Track nieuwe objecten (INSERT)
    for obj in session.new:
        if should_track_model(obj):
            # Sla object state op voor after_flush
            if not hasattr(session, '_historie_inserts'):
                session._historie_inserts = []
            session._historie_inserts.append(obj)
    
    # Track gewijzigde objecten (UPDATE)
    for obj in session.dirty:
        if should_track_model(obj):
            if not hasattr(session, '_historie_updates'):
                session._historie_updates = []
            
            # Get oude waardes
            from sqlalchemy import inspect as sqla_inspect
            oude_waarde = {}

            # Get the old value of updated_at if it changed
            insp = sqla_inspect(obj)
            if 'updated_at' in insp.attrs:
                hist = insp.attrs.updated_at.history
                if hist.has_changes() and hist.deleted:
                    oude_waarde['updated_at'] = str(hist.deleted[0]) if hist.deleted[0] else None

            session._historie_updates.append((obj, oude_waarde))
    
    # Track verwijderde objecten (DELETE)
    for obj in session.deleted:
        if should_track_model(obj):
            if not hasattr(session, '_historie_deletes'):
                session._historie_deletes = []
            session._historie_deletes.append(obj)


@event.listens_for(Session, "after_flush")
def after_flush(session, flush_context):
    """
    Create historie records after flush
    """
    # ✅ CHECK: Is historie tracking disabled?
    if session.info.get('disable_historie', False):
        return
    
    try:
        # Process INSERTs
        if hasattr(session, '_historie_inserts'):
            for obj in session._historie_inserts:
                nieuwe_waarde = {
                    'id': str(obj.id) if hasattr(obj, 'id') else None
                }
                create_historie_record(session, obj, 'INSERT', nieuwe_waarde=nieuwe_waarde)
            delattr(session, '_historie_inserts')
        
        # Process UPDATEs
        if hasattr(session, '_historie_updates'):
            for obj, oude_waarde in session._historie_updates:
                nieuwe_waarde = {
                    'updated_at': str(obj.updated_at) if hasattr(obj, 'updated_at') else None
                }
                create_historie_record(session, obj, 'UPDATE', oude_waarde=oude_waarde, nieuwe_waarde=nieuwe_waarde)
            delattr(session, '_historie_updates')
        
        # Process DELETEs
        if hasattr(session, '_historie_deletes'):
            for obj in session._historie_deletes:
                oude_waarde = {
                    'id': str(obj.id) if hasattr(obj, 'id') else None
                }
                create_historie_record(session, obj, 'DELETE', oude_waarde=oude_waarde)
            delattr(session, '_historie_deletes')
    
    except Exception as e:
        # Log error maar laat operatie niet falen
        print(f"⚠️  Historie tracking error: {e}")


# Setup event listeners
def setup_historie_listeners():
    """
    Setup historie event listeners

    Dit wordt aangeroepen bij startup
    """
    print("✅ Historie tracking event listeners geregistreerd")
    print("   - User")
    print("   - Project")
    print("   - Contract")
    print("   - Leverancier")
    print("   - Vestiging")
    print("   - ProjectFase")
    print("   - ProjectFaseDocument")
    print("   - ProjectFaseCommentaar")
