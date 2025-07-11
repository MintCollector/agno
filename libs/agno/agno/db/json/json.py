import json as json_module
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
from uuid import uuid4

from agno.db.base import BaseDb, SessionType
from agno.db.json.utils import file_lock, safe_json_load, safe_json_save
from agno.db.schemas import MemoryRow
from agno.db.schemas.knowledge import KnowledgeRow
from agno.eval.schemas import EvalFilterType, EvalRunRecord, EvalType
from agno.session import AgentSession, Session, TeamSession, WorkflowSession
from agno.utils.log import log_debug, log_error, log_info, log_warning


class JsonDb(BaseDb):
    def __init__(
        self,
        db_file: Optional[str] = None,
        db_dir: Optional[str] = None,
        session_table: Optional[str] = None,
        user_memory_table: Optional[str] = None,
        metrics_table: Optional[str] = None,
        eval_table: Optional[str] = None,
        knowledge_table: Optional[str] = None,
    ):
        """
        Interface for interacting with JSON file storage.
        
        Args:
            db_file: Path to single JSON file for all data
            db_dir: Directory path for separate JSON files per table
            session_table: Name of the session table/file
            user_memory_table: Name of the user memory table/file
            metrics_table: Name of the metrics table/file
            eval_table: Name of the evaluation table/file
            knowledge_table: Name of the knowledge table/file
        """
        super().__init__(
            session_table=session_table,
            user_memory_table=user_memory_table,
            metrics_table=metrics_table,
            eval_table=eval_table,
            knowledge_table=knowledge_table,
        )
        
        # Set up storage paths
        if db_file:
            self.db_file = Path(db_file)
            self.db_dir = None
            self.storage_type = "single_file"
        else:
            self.db_file = None
            self.db_dir = Path(db_dir) if db_dir else Path("./json_db")
            self.storage_type = "separate_files"
        
        # Create directories if needed
        if self.storage_type == "single_file":
            self.db_file.parent.mkdir(parents=True, exist_ok=True)
        else:
            self.db_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_file_path(self, table_name: str) -> Path:
        """Get the file path for a specific table."""
        if self.storage_type == "single_file":
            return self.db_file
        else:
            return self.db_dir / f"{table_name}.json"
    
    def _load_data(self, table_name: str) -> Dict[str, Any]:
        """Load data from JSON file with file locking."""
        file_path = self._get_file_path(table_name)
        
        with file_lock(file_path):
            if self.storage_type == "single_file":
                data = safe_json_load(file_path)
                return data.get(table_name, {})
            else:
                return safe_json_load(file_path)
    
    def _save_data(self, table_name: str, data: Dict[str, Any]) -> None:
        """Save data to JSON file with file locking."""
        file_path = self._get_file_path(table_name)
        
        with file_lock(file_path):
            if self.storage_type == "single_file":
                # Load existing data and update the specific table
                existing_data = safe_json_load(file_path)
                existing_data[table_name] = data
                
                if not safe_json_save(file_path, existing_data):
                    raise RuntimeError(f"Failed to save data to {file_path}")
            else:
                # Save to separate file
                if not safe_json_save(file_path, data):
                    raise RuntimeError(f"Failed to save data to {file_path}")
    
    def _serialize_session(self, session: Session) -> Dict[str, Any]:
        """Serialize a session object to dictionary."""
        session_dict = session.to_dict()
        session_dict["updated_at"] = int(time.time())
        if "created_at" not in session_dict:
            session_dict["created_at"] = session_dict["updated_at"]
        return session_dict
    
    def _deserialize_session(self, session_dict: Dict[str, Any]) -> Optional[Session]:
        """Deserialize a dictionary to session object."""
        try:
            session_type = session_dict.get("session_type")
            if session_type == SessionType.AGENT.value:
                return AgentSession.from_dict(session_dict)
            elif session_type == SessionType.TEAM.value:
                return TeamSession.from_dict(session_dict)
            elif session_type == SessionType.WORKFLOW.value:
                return WorkflowSession.from_dict(session_dict)
            else:
                log_warning(f"Unknown session type: {session_type}")
                return None
        except Exception as e:
            log_error(f"Error deserializing session: {e}")
            return None
    
    # --- Sessions ---
    
    def delete_session(self, session_id: str, session_type: SessionType = SessionType.AGENT) -> None:
        """Delete a session from storage."""
        if not self.session_table_name:
            raise ValueError("Session table name not provided")
        
        data = self._load_data(self.session_table_name)
        if session_id in data:
            del data[session_id]
            self._save_data(self.session_table_name, data)
            log_debug(f"Deleted session {session_id}")
        else:
            log_debug(f"Session {session_id} not found for deletion")
    
    def delete_sessions(self, session_ids: List[str]) -> None:
        """Delete multiple sessions from storage."""
        if not self.session_table_name:
            raise ValueError("Session table name not provided")
        
        data = self._load_data(self.session_table_name)
        deleted_count = 0
        
        for session_id in session_ids:
            if session_id in data:
                del data[session_id]
                deleted_count += 1
        
        if deleted_count > 0:
            self._save_data(self.session_table_name, data)
            log_debug(f"Deleted {deleted_count} sessions")
    
    def get_session_raw(
        self, session_id: str, session_type: SessionType, user_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Get a session as raw dictionary."""
        if not self.session_table_name:
            raise ValueError("Session table name not provided")
        
        data = self._load_data(self.session_table_name)
        session_data = data.get(session_id)
        
        if session_data is None:
            return None
        
        # Check user_id if provided
        if user_id and session_data.get("user_id") != user_id:
            return None
        
        # Check session_type if provided
        if session_type and session_data.get("session_type") != session_type.value:
            return None
        
        return session_data
    
    def get_session(
        self, session_id: str, session_type: SessionType, user_id: Optional[str] = None
    ) -> Optional[Session]:
        """Get a session from storage."""
        session_data = self.get_session_raw(session_id, session_type, user_id)
        if session_data is None:
            return None
        
        return self._deserialize_session(session_data)
    
    def get_sessions_raw(
        self,
        session_type: SessionType,
        user_id: Optional[str] = None,
        component_id: Optional[str] = None,
        session_name: Optional[str] = None,
        limit: Optional[int] = None,
        page: Optional[int] = None,
        sort_by: Optional[str] = None,
        sort_order: Optional[str] = None,
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Get sessions as raw dictionaries with filtering and pagination."""
        if not self.session_table_name:
            raise ValueError("Session table name not provided")
        
        data = self._load_data(self.session_table_name)
        sessions = []
        
        # Filter sessions
        for session_data in data.values():
            # Filter by session type
            if session_data.get("session_type") != session_type.value:
                continue
            
            # Filter by user_id
            if user_id and session_data.get("user_id") != user_id:
                continue
            
            # Filter by component_id
            if component_id:
                if session_type == SessionType.AGENT and session_data.get("agent_id") != component_id:
                    continue
                elif session_type == SessionType.TEAM and session_data.get("team_id") != component_id:
                    continue
                elif session_type == SessionType.WORKFLOW and session_data.get("workflow_id") != component_id:
                    continue
            
            # Filter by session_name
            if session_name:
                session_data_name = session_data.get("session_data", {}).get("session_name", "")
                if session_name.lower() not in session_data_name.lower():
                    continue
            
            sessions.append(session_data)
        
        total_count = len(sessions)
        
        # Sort sessions
        if sort_by:
            reverse = sort_order == "desc"
            sessions.sort(key=lambda x: x.get(sort_by, 0), reverse=reverse)
        
        # Paginate
        if limit is not None:
            start = 0
            if page is not None:
                start = (page - 1) * limit
            sessions = sessions[start:start + limit]
        
        return sessions, total_count
    
    def get_sessions(
        self,
        session_type: SessionType,
        user_id: Optional[str] = None,
        component_id: Optional[str] = None,
        session_name: Optional[str] = None,
        limit: Optional[int] = None,
        page: Optional[int] = None,
        sort_by: Optional[str] = None,
        sort_order: Optional[str] = None,
    ) -> List[Session]:
        """Get sessions from storage."""
        sessions_raw, _ = self.get_sessions_raw(
            session_type=session_type,
            user_id=user_id,
            component_id=component_id,
            session_name=session_name,
            limit=limit,
            page=page,
            sort_by=sort_by,
            sort_order=sort_order,
        )
        
        sessions = []
        for session_data in sessions_raw:
            session = self._deserialize_session(session_data)
            if session:
                sessions.append(session)
        
        return sessions
    
    def rename_session(self, session_id: str, session_type: SessionType, session_name: str) -> Optional[Session]:
        """Rename a session in storage."""
        if not self.session_table_name:
            raise ValueError("Session table name not provided")
        
        data = self._load_data(self.session_table_name)
        session_data = data.get(session_id)
        
        if session_data is None:
            return None
        
        # Update session name
        if "session_data" not in session_data:
            session_data["session_data"] = {}
        session_data["session_data"]["session_name"] = session_name
        session_data["updated_at"] = int(time.time())
        
        # Save back
        data[session_id] = session_data
        self._save_data(self.session_table_name, data)
        
        return self._deserialize_session(session_data)
    
    def upsert_session(self, session: Session) -> Optional[Session]:
        """Insert or update a session in storage."""
        if not self.session_table_name:
            raise ValueError("Session table name not provided")
        
        try:
            data = self._load_data(self.session_table_name)
            session_data = self._serialize_session(session)
            
            # Add session type
            if isinstance(session, AgentSession):
                session_data["session_type"] = SessionType.AGENT.value
            elif isinstance(session, TeamSession):
                session_data["session_type"] = SessionType.TEAM.value
            elif isinstance(session, WorkflowSession):
                session_data["session_type"] = SessionType.WORKFLOW.value
            
            data[session.session_id] = session_data
            self._save_data(self.session_table_name, data)
            
            return session
            
        except Exception as e:
            log_error(f"Error upserting session: {e}")
            return None
    
    # --- User Memory ---
    
    def delete_user_memory(self, memory_id: str) -> None:
        """Delete a user memory from storage."""
        if not self.user_memory_table_name:
            raise ValueError("User memory table name not provided")
        
        data = self._load_data(self.user_memory_table_name)
        if memory_id in data:
            del data[memory_id]
            self._save_data(self.user_memory_table_name, data)
            log_debug(f"Deleted user memory {memory_id}")
    
    def delete_user_memories(self, memory_ids: List[str]) -> None:
        """Delete multiple user memories from storage."""
        if not self.user_memory_table_name:
            raise ValueError("User memory table name not provided")
        
        data = self._load_data(self.user_memory_table_name)
        deleted_count = 0
        
        for memory_id in memory_ids:
            if memory_id in data:
                del data[memory_id]
                deleted_count += 1
        
        if deleted_count > 0:
            self._save_data(self.user_memory_table_name, data)
            log_debug(f"Deleted {deleted_count} user memories")
    
    def get_all_memory_topics(self) -> List[str]:
        """Get all memory topics from storage."""
        if not self.user_memory_table_name:
            return []
        
        data = self._load_data(self.user_memory_table_name)
        topics = set()
        
        for memory_data in data.values():
            memory_topics = memory_data.get("topics", [])
            if isinstance(memory_topics, list):
                topics.update(memory_topics)
        
        return list(topics)
    
    def get_user_memory_raw(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """Get a user memory as raw dictionary."""
        if not self.user_memory_table_name:
            return None
        
        data = self._load_data(self.user_memory_table_name)
        return data.get(memory_id)
    
    def get_user_memory(self, memory_id: str) -> Optional[MemoryRow]:
        """Get a user memory from storage."""
        memory_data = self.get_user_memory_raw(memory_id)
        if memory_data is None:
            return None
        
        try:
            return MemoryRow(
                id=memory_data["memory_id"],
                user_id=memory_data.get("user_id"),
                agent_id=memory_data.get("agent_id"),
                team_id=memory_data.get("team_id"),
                memory=memory_data["memory"],
                last_updated=memory_data.get("last_updated", int(time.time())),
            )
        except Exception as e:
            log_error(f"Error deserializing memory: {e}")
            return None
    
    def get_user_memories_raw(
        self,
        user_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        team_id: Optional[str] = None,
        workflow_id: Optional[str] = None,
        topics: Optional[List[str]] = None,
        search_content: Optional[str] = None,
        limit: Optional[int] = None,
        page: Optional[int] = None,
        sort_by: Optional[str] = None,
        sort_order: Optional[str] = None,
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Get user memories as raw dictionaries with filtering and pagination."""
        if not self.user_memory_table_name:
            return [], 0
        
        data = self._load_data(self.user_memory_table_name)
        memories = []
        
        # Filter memories
        for memory_data in data.values():
            # Filter by user_id
            if user_id and memory_data.get("user_id") != user_id:
                continue
            
            # Filter by agent_id
            if agent_id and memory_data.get("agent_id") != agent_id:
                continue
            
            # Filter by team_id
            if team_id and memory_data.get("team_id") != team_id:
                continue
            
            # Note: workflow_id not supported in MemoryRow schema
            
            # Filter by topics
            if topics:
                memory_topics = memory_data.get("topics", [])
                if not any(topic in memory_topics for topic in topics):
                    continue
            
            # Filter by search content
            if search_content:
                memory_text = str(memory_data.get("memory", "")).lower()
                if search_content.lower() not in memory_text:
                    continue
            
            memories.append(memory_data)
        
        total_count = len(memories)
        
        # Sort memories
        if sort_by:
            reverse = sort_order == "desc"
            memories.sort(key=lambda x: x.get(sort_by, 0), reverse=reverse)
        
        # Paginate
        if limit is not None:
            start = 0
            if page is not None:
                start = (page - 1) * limit
            memories = memories[start:start + limit]
        
        return memories, total_count
    
    def get_user_memories(
        self,
        user_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        team_id: Optional[str] = None,
        workflow_id: Optional[str] = None,
        topics: Optional[List[str]] = None,
        search_content: Optional[str] = None,
        limit: Optional[int] = None,
        page: Optional[int] = None,
        sort_by: Optional[str] = None,
        sort_order: Optional[str] = None,
    ) -> List[MemoryRow]:
        """Get user memories from storage."""
        memories_raw, _ = self.get_user_memories_raw(
            user_id=user_id,
            agent_id=agent_id,
            team_id=team_id,
            workflow_id=workflow_id,
            topics=topics,
            search_content=search_content,
            limit=limit,
            page=page,
            sort_by=sort_by,
            sort_order=sort_order,
        )
        
        memories = []
        for memory_data in memories_raw:
            memory = self.get_user_memory(memory_data["memory_id"])
            if memory:
                memories.append(memory)
        
        return memories
    
    def get_user_memory_stats(
        self,
        limit: Optional[int] = None,
        page: Optional[int] = None,
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Get user memory statistics."""
        if not self.user_memory_table_name:
            return [], 0
        
        data = self._load_data(self.user_memory_table_name)
        user_stats = {}
        
        # Calculate stats per user
        for memory_data in data.values():
            user_id = memory_data.get("user_id")
            if not user_id:
                continue
            
            if user_id not in user_stats:
                user_stats[user_id] = {
                    "user_id": user_id,
                    "total_memories": 0,
                    "last_memory_updated_at": 0,
                }
            
            user_stats[user_id]["total_memories"] += 1
            last_updated = memory_data.get("last_updated", 0)
            if last_updated > user_stats[user_id]["last_memory_updated_at"]:
                user_stats[user_id]["last_memory_updated_at"] = last_updated
        
        stats_list = list(user_stats.values())
        total_count = len(stats_list)
        
        # Sort by last updated
        stats_list.sort(key=lambda x: x["last_memory_updated_at"], reverse=True)
        
        # Paginate
        if limit is not None:
            start = 0
            if page is not None:
                start = (page - 1) * limit
            stats_list = stats_list[start:start + limit]
        
        return stats_list, total_count
    
    def upsert_user_memory_raw(self, memory: MemoryRow) -> Optional[Dict[str, Any]]:
        """Insert or update a user memory and return raw dictionary."""
        if not self.user_memory_table_name:
            return None
        
        try:
            data = self._load_data(self.user_memory_table_name)
            
            if memory.id is None:
                memory.id = str(uuid4())
            
            memory_data = {
                "memory_id": memory.id,
                "user_id": memory.user_id,
                "agent_id": memory.agent_id,
                "team_id": memory.team_id,
                "memory": memory.memory,
                "topics": memory.memory.get("topics", []) if isinstance(memory.memory, dict) else [],
                "feedback": memory.memory.get("feedback") if isinstance(memory.memory, dict) else None,
                "last_updated": int(time.time()),
            }
            
            data[memory.id] = memory_data
            self._save_data(self.user_memory_table_name, data)
            
            return memory_data
            
        except Exception as e:
            log_error(f"Error upserting user memory: {e}")
            return None
    
    def upsert_user_memory(self, memory: MemoryRow) -> Optional[MemoryRow]:
        """Insert or update a user memory."""
        memory_data = self.upsert_user_memory_raw(memory)
        if memory_data is None:
            return None
        
        return MemoryRow(
            id=memory_data["memory_id"],
            user_id=memory_data["user_id"],
            agent_id=memory_data["agent_id"],
            team_id=memory_data["team_id"],
            memory=memory_data["memory"],
            last_updated=memory_data["last_updated"],
        )
    
    # --- Metrics ---
    
    def calculate_metrics(self) -> Optional[Any]:
        """Calculate metrics (placeholder implementation)."""
        log_info("Metrics calculation not implemented for JsonDb")
        return None
    
    def get_metrics_raw(
        self, starting_date: Optional[date] = None, ending_date: Optional[date] = None
    ) -> Tuple[List[Any], Optional[int]]:
        """Get metrics as raw data."""
        if not self.metrics_table_name:
            return [], None
        
        data = self._load_data(self.metrics_table_name)
        metrics = list(data.values())
        
        # Filter by date range if provided
        if starting_date or ending_date:
            filtered_metrics = []
            for metric in metrics:
                metric_date_str = metric.get("date")
                if not metric_date_str:
                    continue
                
                try:
                    metric_date = datetime.fromisoformat(metric_date_str).date()
                    if starting_date and metric_date < starting_date:
                        continue
                    if ending_date and metric_date > ending_date:
                        continue
                    filtered_metrics.append(metric)
                except ValueError:
                    continue
            
            metrics = filtered_metrics
        
        # Get latest update time
        latest_update = None
        for metric in metrics:
            updated_at = metric.get("updated_at")
            if updated_at and (latest_update is None or updated_at > latest_update):
                latest_update = updated_at
        
        return metrics, latest_update
    
    # --- Knowledge ---
    
    def get_source_status(self, id: str) -> Optional[str]:
        """Get the status of a knowledge source by ID."""
        if not self.knowledge_table_name:
            return None
        
        data = self._load_data(self.knowledge_table_name)
        knowledge_data = data.get(id)
        return knowledge_data.get("status") if knowledge_data else None
    
    def get_knowledge_source(self, id: str) -> Optional[KnowledgeRow]:
        """Get a knowledge document by ID."""
        if not self.knowledge_table_name:
            return None
        
        data = self._load_data(self.knowledge_table_name)
        knowledge_data = data.get(id)
        
        if knowledge_data is None:
            return None
        
        try:
            return KnowledgeRow.model_validate(knowledge_data)
        except Exception as e:
            log_error(f"Error deserializing knowledge source: {e}")
            return None
    
    def get_knowledge_sources(
        self,
        limit: Optional[int] = None,
        page: Optional[int] = None,
        sort_by: Optional[str] = None,
        sort_order: Optional[str] = None,
    ) -> Tuple[List[KnowledgeRow], int]:
        """Get all knowledge documents from storage."""
        if not self.knowledge_table_name:
            return [], 0
        
        data = self._load_data(self.knowledge_table_name)
        knowledge_list = list(data.values())
        total_count = len(knowledge_list)
        
        # Sort
        if sort_by:
            reverse = sort_order == "desc"
            knowledge_list.sort(key=lambda x: x.get(sort_by, 0), reverse=reverse)
        
        # Paginate
        if limit is not None:
            start = 0
            if page is not None:
                start = (page - 1) * limit
            knowledge_list = knowledge_list[start:start + limit]
        
        # Convert to KnowledgeRow objects
        knowledge_rows = []
        for knowledge_data in knowledge_list:
            try:
                knowledge_row = KnowledgeRow.model_validate(knowledge_data)
                knowledge_rows.append(knowledge_row)
            except Exception as e:
                log_error(f"Error deserializing knowledge source: {e}")
                continue
        
        return knowledge_rows, total_count
    
    def upsert_knowledge_source(self, knowledge_row: KnowledgeRow):
        """Insert or update a knowledge document."""
        if not self.knowledge_table_name:
            return None
        
        try:
            data = self._load_data(self.knowledge_table_name)
            knowledge_data = knowledge_row.model_dump()
            
            data[knowledge_row.id] = knowledge_data
            self._save_data(self.knowledge_table_name, data)
            
            return knowledge_row
            
        except Exception as e:
            log_error(f"Error upserting knowledge source: {e}")
            return None
    
    def delete_knowledge_source(self, id: str):
        """Delete a knowledge document by ID."""
        if not self.knowledge_table_name:
            return
        
        data = self._load_data(self.knowledge_table_name)
        if id in data:
            del data[id]
            self._save_data(self.knowledge_table_name, data)
            log_debug(f"Deleted knowledge source {id}")
    
    # --- Eval ---
    
    def create_eval_run(self, eval_run: EvalRunRecord) -> Optional[Dict[str, Any]]:
        """Create an evaluation run."""
        if not self.eval_table_name:
            return None
        
        try:
            data = self._load_data(self.eval_table_name)
            
            current_time = int(time.time())
            eval_data = eval_run.model_dump()
            eval_data["created_at"] = current_time
            eval_data["updated_at"] = current_time
            
            data[eval_run.run_id] = eval_data
            self._save_data(self.eval_table_name, data)
            
            return eval_data
            
        except Exception as e:
            log_error(f"Error creating eval run: {e}")
            return None
    
    def delete_eval_runs(self, eval_run_ids: List[str]) -> None:
        """Delete multiple evaluation runs."""
        if not self.eval_table_name:
            return
        
        data = self._load_data(self.eval_table_name)
        deleted_count = 0
        
        for eval_run_id in eval_run_ids:
            if eval_run_id in data:
                del data[eval_run_id]
                deleted_count += 1
        
        if deleted_count > 0:
            self._save_data(self.eval_table_name, data)
            log_debug(f"Deleted {deleted_count} eval runs")
    
    def get_eval_run_raw(self, eval_run_id: str, table: Optional[Any] = None) -> Optional[Dict[str, Any]]:
        """Get an evaluation run as raw dictionary."""
        if not self.eval_table_name:
            return None
        
        data = self._load_data(self.eval_table_name)
        return data.get(eval_run_id)
    
    def get_eval_run(self, eval_run_id: str, table: Optional[Any] = None) -> Optional[EvalRunRecord]:
        """Get an evaluation run."""
        eval_data = self.get_eval_run_raw(eval_run_id, table)
        if eval_data is None:
            return None
        
        try:
            return EvalRunRecord.model_validate(eval_data)
        except Exception as e:
            log_error(f"Error deserializing eval run: {e}")
            return None
    
    def get_eval_runs_raw(
        self,
        limit: Optional[int] = None,
        page: Optional[int] = None,
        sort_by: Optional[str] = None,
        sort_order: Optional[str] = None,
        table: Optional[Any] = None,
        agent_id: Optional[str] = None,
        team_id: Optional[str] = None,
        workflow_id: Optional[str] = None,
        model_id: Optional[str] = None,
        eval_type: Optional[List[EvalType]] = None,
        filter_type: Optional[EvalFilterType] = None,
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Get evaluation runs as raw dictionaries with filtering."""
        if not self.eval_table_name:
            return [], 0
        
        data = self._load_data(self.eval_table_name)
        eval_runs = []
        
        # Filter eval runs
        for eval_data in data.values():
            # Filter by agent_id
            if agent_id and eval_data.get("agent_id") != agent_id:
                continue
            
            # Filter by team_id
            if team_id and eval_data.get("team_id") != team_id:
                continue
            
            # Filter by workflow_id
            if workflow_id and eval_data.get("workflow_id") != workflow_id:
                continue
            
            # Filter by model_id
            if model_id and eval_data.get("model_id") != model_id:
                continue
            
            # Filter by eval_type
            if eval_type and eval_data.get("eval_type") not in eval_type:
                continue
            
            # Filter by filter_type
            if filter_type:
                if filter_type == EvalFilterType.AGENT and not eval_data.get("agent_id"):
                    continue
                elif filter_type == EvalFilterType.TEAM and not eval_data.get("team_id"):
                    continue
                elif filter_type == EvalFilterType.WORKFLOW and not eval_data.get("workflow_id"):
                    continue
            
            eval_runs.append(eval_data)
        
        total_count = len(eval_runs)
        
        # Sort eval runs
        if sort_by:
            reverse = sort_order == "desc"
            eval_runs.sort(key=lambda x: x.get(sort_by, 0), reverse=reverse)
        else:
            # Default sort by created_at desc
            eval_runs.sort(key=lambda x: x.get("created_at", 0), reverse=True)
        
        # Paginate
        if limit is not None:
            start = 0
            if page is not None:
                start = (page - 1) * limit
            eval_runs = eval_runs[start:start + limit]
        
        return eval_runs, total_count
    
    def get_eval_runs(
        self,
        limit: Optional[int] = None,
        page: Optional[int] = None,
        sort_by: Optional[str] = None,
        sort_order: Optional[str] = None,
        table: Optional[Any] = None,
        agent_id: Optional[str] = None,
        team_id: Optional[str] = None,
        workflow_id: Optional[str] = None,
        model_id: Optional[str] = None,
        eval_type: Optional[List[EvalType]] = None,
    ) -> List[EvalRunRecord]:
        """Get evaluation runs."""
        eval_runs_raw, _ = self.get_eval_runs_raw(
            limit=limit,
            page=page,
            sort_by=sort_by,
            sort_order=sort_order,
            table=table,
            agent_id=agent_id,
            team_id=team_id,
            workflow_id=workflow_id,
            model_id=model_id,
            eval_type=eval_type,
        )
        
        eval_runs = []
        for eval_data in eval_runs_raw:
            try:
                eval_run = EvalRunRecord.model_validate(eval_data)
                eval_runs.append(eval_run)
            except Exception as e:
                log_error(f"Error deserializing eval run: {e}")
                continue
        
        return eval_runs
    
    def rename_eval_run(self, eval_run_id: str, name: str) -> Optional[Dict[str, Any]]:
        """Rename an evaluation run."""
        if not self.eval_table_name:
            return None
        
        data = self._load_data(self.eval_table_name)
        eval_data = data.get(eval_run_id)
        
        if eval_data is None:
            return None
        
        eval_data["name"] = name
        eval_data["updated_at"] = int(time.time())
        
        data[eval_run_id] = eval_data
        self._save_data(self.eval_table_name, data)
        
        return eval_data