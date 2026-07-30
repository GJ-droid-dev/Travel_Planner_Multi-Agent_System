import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

from src.utils.llm import LLMClient, TransientLLMError
from src.models.agent_io import AgentTask, AgentResult, ResultStatus, AgentType
from src.utils.logger import get_logger

logger = get_logger("agents")

class BaseAgent(ABC):
    def __init__(self, llm_client: LLMClient, agent_name: str):
        self.llm_client = llm_client
        self.agent_name = agent_name
        self.system_prompt = self._load_prompt()
        self._build_tools()
        
    def _load_prompt(self) -> str:
        prompt_path = Path("src/prompts") / f"{self.agent_name.lower()}.md"
        if not prompt_path.exists():
            logger.warning(f"Prompt file not found at {prompt_path}")
            return ""
        with open(prompt_path, "r", encoding="utf-8") as f:
            return f.read()
            
    def _build_tools(self):
        """Override in subclasses to initialize specific tools."""
        pass
        
    @abstractmethod
    async def _do_execute(self, task: AgentTask) -> AgentResult:
        """Core logic to be implemented by subclasses."""
        pass
        
    async def execute(self, task: AgentTask) -> AgentResult:
        """Executes the agent task with timing and error handling."""
        start_time = time.time()
        log = logger.bind(agent_type=self.agent_name, task_id=task.task_id)
        
        try:
            result = await self._do_execute(task)
            result.duration_ms = int((time.time() - start_time) * 1000)
            return result
        except TransientLLMError:
            # Let this bubble up so the orchestrator/API can handle 503
            raise
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            log.error("agent_execution_failed", error=str(e), duration_ms=duration_ms)
            return AgentResult(
                task_id=task.task_id,
                agent_type=task.agent_type,
                status=ResultStatus.FAILED,
                payload={},
                confidence=0.0,
                reasoning="Agent execution failed due to an exception.",
                errors=[str(e)],
                duration_ms=duration_ms
            )
