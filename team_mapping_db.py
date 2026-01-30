"""
Team Mapping Database Service

Manages team name mappings between Kambi API and Elo ratings sources.
Provides fuzzy matching with manual override capabilities.
"""

import sqlite3
import logging
from datetime import datetime
from typing import Optional, List, Dict, Tuple
from pathlib import Path
from rapidfuzz import fuzz

logger = logging.getLogger(__name__)


class TeamMapping:
    """Represents a team name mapping between Kambi and Elo systems."""

    def __init__(
        self,
        id: Optional[int] = None,
        kambi_team_name: str = "",
        elo_team_name: str = "",
        league_filter: Optional[str] = None,
        confidence: str = "manual",
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ):
        self.id = id
        self.kambi_team_name = kambi_team_name
        self.elo_team_name = elo_team_name
        self.league_filter = league_filter
        self.confidence = confidence  # 'manual', 'auto_high', 'auto_medium', 'auto_low'
        self.created_at = created_at or datetime.now()
        self.updated_at = updated_at or datetime.now()

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'kambi_team_name': self.kambi_team_name,
            'elo_team_name': self.elo_team_name,
            'league_filter': self.league_filter,
            'confidence': self.confidence,
            'created_at': self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at,
            'updated_at': self.updated_at.isoformat() if isinstance(self.updated_at, datetime) else self.updated_at,
        }


class TeamMappingService:
    """Service for managing team name mappings with SQLite database."""

    def __init__(self, db_path: str = "data/team_mappings.db"):
        """Initialize the service with database path."""
        self.db_path = db_path
        self._ensure_db_directory()
        self._init_database()

    def _ensure_db_directory(self):
        """Ensure the database directory exists."""
        db_dir = Path(self.db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)

    def _get_connection(self) -> sqlite3.Connection:
        """Get a database connection."""
        conn = sqlite3.Connection(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_database(self):
        """Initialize database schema."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()

            # Create team_mappings table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS team_mappings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    kambi_team_name TEXT NOT NULL,
                    elo_team_name TEXT NOT NULL,
                    league_filter TEXT,
                    confidence TEXT NOT NULL DEFAULT 'manual',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    UNIQUE(kambi_team_name, league_filter)
                )
            """)

            # Create indices for faster lookups
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_kambi_team_name
                ON team_mappings(kambi_team_name)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_league_filter
                ON team_mappings(league_filter)
            """)

            # Create unmapped_teams table for tracking teams that failed to match
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS unmapped_teams (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    team_name TEXT NOT NULL,
                    source TEXT NOT NULL,
                    league TEXT,
                    last_seen TEXT NOT NULL,
                    occurrence_count INTEGER DEFAULT 1,
                    UNIQUE(team_name, source, league)
                )
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_unmapped_team_name
                ON unmapped_teams(team_name)
            """)

            conn.commit()
            logger.info(f"Database initialized at {self.db_path}")
        finally:
            conn.close()

    def add_mapping(
        self,
        kambi_team_name: str,
        elo_team_name: str,
        league_filter: Optional[str] = None,
        confidence: str = "manual"
    ) -> TeamMapping:
        """Add or update a team mapping."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            now = datetime.now().isoformat()

            cursor.execute("""
                INSERT INTO team_mappings
                (kambi_team_name, elo_team_name, league_filter, confidence, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(kambi_team_name, league_filter)
                DO UPDATE SET
                    elo_team_name = excluded.elo_team_name,
                    confidence = excluded.confidence,
                    updated_at = excluded.updated_at
            """, (kambi_team_name, elo_team_name, league_filter, confidence, now, now))

            conn.commit()
            mapping_id = cursor.lastrowid

            logger.info(f"Added/updated mapping: {kambi_team_name} -> {elo_team_name}")

            return TeamMapping(
                id=mapping_id,
                kambi_team_name=kambi_team_name,
                elo_team_name=elo_team_name,
                league_filter=league_filter,
                confidence=confidence,
                created_at=datetime.fromisoformat(now),
                updated_at=datetime.fromisoformat(now)
            )
        finally:
            conn.close()

    def get_mapping(
        self,
        kambi_team_name: str,
        league_filter: Optional[str] = None
    ) -> Optional[str]:
        """
        Get the Elo team name for a Kambi team name.

        First tries exact match with league filter, then without.
        Returns None if no mapping found.
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()

            # Try with league filter first if provided
            if league_filter:
                cursor.execute("""
                    SELECT elo_team_name FROM team_mappings
                    WHERE kambi_team_name = ? AND league_filter = ?
                """, (kambi_team_name, league_filter))

                row = cursor.fetchone()
                if row:
                    return row['elo_team_name']

            # Fallback to mapping without league filter
            cursor.execute("""
                SELECT elo_team_name FROM team_mappings
                WHERE kambi_team_name = ? AND league_filter IS NULL
            """, (kambi_team_name,))

            row = cursor.fetchone()
            return row['elo_team_name'] if row else None
        finally:
            conn.close()

    def get_all_mappings(self) -> List[TeamMapping]:
        """Get all team mappings."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM team_mappings
                ORDER BY kambi_team_name
            """)

            mappings = []
            for row in cursor.fetchall():
                mappings.append(TeamMapping(
                    id=row['id'],
                    kambi_team_name=row['kambi_team_name'],
                    elo_team_name=row['elo_team_name'],
                    league_filter=row['league_filter'],
                    confidence=row['confidence'],
                    created_at=datetime.fromisoformat(row['created_at']),
                    updated_at=datetime.fromisoformat(row['updated_at'])
                ))

            return mappings
        finally:
            conn.close()

    def delete_mapping(self, mapping_id: int) -> bool:
        """Delete a team mapping by ID."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM team_mappings WHERE id = ?", (mapping_id,))
            conn.commit()

            deleted = cursor.rowcount > 0
            if deleted:
                logger.info(f"Deleted mapping ID: {mapping_id}")
            return deleted
        finally:
            conn.close()

    def record_unmapped_team(
        self,
        team_name: str,
        source: str,
        league: Optional[str] = None
    ):
        """Record a team that couldn't be mapped for future reference."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            now = datetime.now().isoformat()

            cursor.execute("""
                INSERT INTO unmapped_teams
                (team_name, source, league, last_seen, occurrence_count)
                VALUES (?, ?, ?, ?, 1)
                ON CONFLICT(team_name, source, league)
                DO UPDATE SET
                    last_seen = excluded.last_seen,
                    occurrence_count = occurrence_count + 1
            """, (team_name, source, league, now))

            conn.commit()
        finally:
            conn.close()

    def get_unmapped_teams(self, source: Optional[str] = None) -> List[Dict]:
        """Get list of unmapped teams."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()

            if source:
                cursor.execute("""
                    SELECT * FROM unmapped_teams
                    WHERE source = ?
                    ORDER BY occurrence_count DESC, last_seen DESC
                """, (source,))
            else:
                cursor.execute("""
                    SELECT * FROM unmapped_teams
                    ORDER BY occurrence_count DESC, last_seen DESC
                """)

            unmapped = []
            for row in cursor.fetchall():
                unmapped.append({
                    'id': row['id'],
                    'team_name': row['team_name'],
                    'source': row['source'],
                    'league': row['league'],
                    'last_seen': row['last_seen'],
                    'occurrence_count': row['occurrence_count']
                })

            return unmapped
        finally:
            conn.close()

    def clear_unmapped_teams(self):
        """Clear the unmapped teams tracking table."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM unmapped_teams")
            conn.commit()
            logger.info("Cleared unmapped teams table")
        finally:
            conn.close()

    def find_fuzzy_match(
        self,
        kambi_team_name: str,
        elo_team_names: List[str],
        threshold: int = 85
    ) -> Optional[Tuple[str, int]]:
        """
        Find best fuzzy match for a Kambi team name among Elo team names.

        Returns (matched_name, score) or None if no match above threshold.
        """
        best_match = None
        best_score = 0

        for elo_name in elo_team_names:
            # Use token_sort_ratio for word-order independence
            score = fuzz.token_sort_ratio(kambi_team_name, elo_name)

            if score > best_score:
                best_score = score
                best_match = elo_name

        if best_score >= threshold:
            return (best_match, best_score)

        return None

    def suggest_mapping(
        self,
        kambi_team_name: str,
        elo_team_names: List[str],
        auto_save: bool = False,
        league_filter: Optional[str] = None
    ) -> Optional[Tuple[str, int, str]]:
        """
        Suggest a mapping for a Kambi team using fuzzy matching.

        Returns (elo_team_name, score, confidence_level) or None.
        If auto_save is True and score >= 90, saves the mapping automatically.
        """
        match_result = self.find_fuzzy_match(kambi_team_name, elo_team_names, threshold=70)

        if not match_result:
            return None

        elo_name, score = match_result

        # Determine confidence level
        if score >= 95:
            confidence = "auto_high"
        elif score >= 85:
            confidence = "auto_medium"
        else:
            confidence = "auto_low"

        # Auto-save high confidence matches
        if auto_save and score >= 90:
            self.add_mapping(
                kambi_team_name=kambi_team_name,
                elo_team_name=elo_name,
                league_filter=league_filter,
                confidence=confidence
            )
            logger.info(f"Auto-saved mapping: {kambi_team_name} -> {elo_name} (score: {score})")

        return (elo_name, score, confidence)

    def export_mappings(self) -> List[Dict]:
        """Export all mappings as JSON-serializable list."""
        mappings = self.get_all_mappings()
        return [m.to_dict() for m in mappings]

    def import_mappings(self, mappings: List[Dict]):
        """Import mappings from JSON-serializable list."""
        for mapping_data in mappings:
            self.add_mapping(
                kambi_team_name=mapping_data['kambi_team_name'],
                elo_team_name=mapping_data['elo_team_name'],
                league_filter=mapping_data.get('league_filter'),
                confidence=mapping_data.get('confidence', 'manual')
            )

        logger.info(f"Imported {len(mappings)} mappings")


# Global singleton instance
_mapping_service: Optional[TeamMappingService] = None


def get_mapping_service() -> TeamMappingService:
    """Get or create the global mapping service instance."""
    global _mapping_service
    if _mapping_service is None:
        _mapping_service = TeamMappingService()
    return _mapping_service
