"""
Database module for managing block relationships and keywords.
Uses PostgreSQL to store blocker-blocked relationships and associated keywords.
"""
import psycopg2
import os
from typing import List, Optional, Tuple
from psycopg2.extras import RealDictCursor


class Database:
    """
    Handles all database operations for the blocker bot.
    Manages connections to PostgreSQL and provides methods for block management.
    """
    
    def __init__(self):
        """Initialize database connection using environment variables."""
        # Get database connection details from environment variables
        self.db_name = os.getenv('DB_NAME', 'railway')
        self.db_user = os.getenv('DB_USER', 'postgres')
        self.db_password = os.getenv('DB_PASSWORD', '')
        self.db_host = os.getenv('DB_HOST', 'localhost')
        self.db_port = os.getenv('DB_PORT', '5432')
        
        # Connection will be established on first use
        self.conn = None
        self._ensure_connection()
        self._create_tables()
    
    def _ensure_connection(self):
        """Establish database connection if not already connected."""
        if self.conn is None or self.conn.closed:
            try:
                self.conn = psycopg2.connect(
                    dbname=self.db_name,
                    user=self.db_user,
                    password=self.db_password,
                    host=self.db_host,
                    port=self.db_port,
                    connect_timeout=10
                )
                # Enable autocommit for better performance
                self.conn.autocommit = True
            except psycopg2.Error as e:
                print(f"Database connection error: {e}")
                raise
    
    def _create_tables(self):
        """
        Create necessary database tables if they don't exist.
        Tables:
        - blocks: Stores blocker-blocked relationships with keywords
        """
        try:
            self._ensure_connection()
            cursor = self.conn.cursor()
            
            # Create blocks table
            # blocker_id: The user who created the block
            # blocked_id: The user who is blocked
            # keywords: Array of keywords the blocked user cannot use
            # guild_id: The server where the block applies
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS blocks (
                    id SERIAL PRIMARY KEY,
                    blocker_id BIGINT NOT NULL,
                    blocked_id BIGINT NOT NULL,
                    guild_id BIGINT NOT NULL,
                    keywords TEXT[] DEFAULT '{}',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(blocker_id, blocked_id, guild_id)
                )
            """)
            
            # Create index for faster lookups
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_blocks_blocked 
                ON blocks(blocked_id, guild_id)
            """)
            
            cursor.close()
            print("Database tables created/verified successfully")
        except psycopg2.Error as e:
            print(f"Error creating tables: {e}")
            raise
    
    def add_block(self, blocker_id: int, blocked_id: int, guild_id: int, keywords: List[str]) -> bool:
        """
        Add or update a block relationship.
        
        Args:
            blocker_id: Discord user ID of the person creating the block
            blocked_id: Discord user ID of the person being blocked
            guild_id: Discord server ID where the block applies
            keywords: List of keywords the blocked user cannot use
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self._ensure_connection()
            cursor = self.conn.cursor()
            
            # Insert or update block relationship
            # ON CONFLICT updates keywords if block already exists
            cursor.execute("""
                INSERT INTO blocks (blocker_id, blocked_id, guild_id, keywords)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (blocker_id, blocked_id, guild_id)
                DO UPDATE SET keywords = EXCLUDED.keywords
            """, (blocker_id, blocked_id, guild_id, keywords))
            
            cursor.close()
            return True
        except psycopg2.Error as e:
            print(f"Error adding block: {e}")
            return False
    
    def remove_block(self, blocker_id: int, blocked_id: int, guild_id: int) -> bool:
        """
        Remove a block relationship.
        
        Args:
            blocker_id: Discord user ID of the person who created the block
            blocked_id: Discord user ID of the person being unblocked
            guild_id: Discord server ID where the block applies
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self._ensure_connection()
            cursor = self.conn.cursor()
            
            cursor.execute("""
                DELETE FROM blocks
                WHERE blocker_id = %s AND blocked_id = %s AND guild_id = %s
            """, (blocker_id, blocked_id, guild_id))
            
            cursor.close()
            return True
        except psycopg2.Error as e:
            print(f"Error removing block: {e}")
            return False
    
    def is_blocked(self, blocker_id: int, blocked_id: int, guild_id: int) -> bool:
        """
        Check if a user is blocked by another user.
        
        Args:
            blocker_id: Discord user ID of the potential blocker
            blocked_id: Discord user ID of the potential blocked user
            guild_id: Discord server ID
            
        Returns:
            True if blocked, False otherwise
        """
        try:
            self._ensure_connection()
            cursor = self.conn.cursor()
            
            cursor.execute("""
                SELECT COUNT(*) FROM blocks
                WHERE blocker_id = %s AND blocked_id = %s AND guild_id = %s
            """, (blocker_id, blocked_id, guild_id))
            
            result = cursor.fetchone()
            cursor.close()
            return result[0] > 0 if result else False
        except psycopg2.Error as e:
            print(f"Error checking block: {e}")
            return False
    
    def get_block_keywords(self, blocker_id: int, blocked_id: int, guild_id: int) -> List[str]:
        """
        Get keywords associated with a block relationship.
        
        Args:
            blocker_id: Discord user ID of the blocker
            blocked_id: Discord user ID of the blocked user
            guild_id: Discord server ID
            
        Returns:
            List of keywords, empty list if no block exists
        """
        try:
            self._ensure_connection()
            cursor = self.conn.cursor()
            
            cursor.execute("""
                SELECT keywords FROM blocks
                WHERE blocker_id = %s AND blocked_id = %s AND guild_id = %s
            """, (blocker_id, blocked_id, guild_id))
            
            result = cursor.fetchone()
            cursor.close()
            return result[0] if result and result[0] else []
        except psycopg2.Error as e:
            print(f"Error getting keywords: {e}")
            return []
    
    def get_all_blockers(self, blocked_id: int, guild_id: int) -> List[int]:
        """
        Get all users who have blocked a specific user in a guild.
        
        Args:
            blocked_id: Discord user ID of the blocked user
            guild_id: Discord server ID
            
        Returns:
            List of blocker user IDs
        """
        try:
            self._ensure_connection()
            cursor = self.conn.cursor()
            
            cursor.execute("""
                SELECT blocker_id FROM blocks
                WHERE blocked_id = %s AND guild_id = %s
            """, (blocked_id, guild_id))
            
            results = cursor.fetchall()
            cursor.close()
            return [row[0] for row in results] if results else []
        except psycopg2.Error as e:
            print(f"Error getting blockers: {e}")
            return []
    
    def check_keywords(self, message_content: str, blocked_id: int, guild_id: int) -> Tuple[bool, List[int]]:
        """
        Check if message contains any blocked keywords.
        
        Args:
            message_content: The message content to check
            blocked_id: Discord user ID of the message author
            guild_id: Discord server ID
            
        Returns:
            Tuple of (has_violation, list of blocker_ids who blocked this user)
        """
        try:
            self._ensure_connection()
            cursor = self.conn.cursor(cursor_factory=RealDictCursor)
            
            # Get all blocks for this user in this guild
            cursor.execute("""
                SELECT blocker_id, keywords FROM blocks
                WHERE blocked_id = %s AND guild_id = %s
            """, (blocked_id, guild_id))
            
            results = cursor.fetchall()
            cursor.close()
            
            if not results:
                return False, []
            
            # Check message content against each block's keywords
            message_lower = message_content.lower()
            violating_blockers = []
            
            for row in results:
                keywords = row['keywords'] or []
                # Check if any keyword appears in the message
                for keyword in keywords:
                    if keyword.lower() in message_lower:
                        violating_blockers.append(row['blocker_id'])
                        break  # Only need to know this blocker is violated
            
            return len(violating_blockers) > 0, violating_blockers
        except psycopg2.Error as e:
            print(f"Error checking keywords: {e}")
            return False, []
    
    def reset_all_blocks(self, guild_id: int) -> int:
        """
        Delete all blocks in a guild.
        
        Args:
            guild_id: Discord server ID
            
        Returns:
            Number of blocks deleted
        """
        try:
            self._ensure_connection()
            cursor = self.conn.cursor()
            
            cursor.execute("""
                DELETE FROM blocks
                WHERE guild_id = %s
            """, (guild_id,))
            
            deleted_count = cursor.rowcount
            cursor.close()
            return deleted_count
        except psycopg2.Error as e:
            print(f"Error resetting blocks: {e}")
            return 0
    
    def close(self):
        """Close database connection."""
        if self.conn and not self.conn.closed:
            self.conn.close()

