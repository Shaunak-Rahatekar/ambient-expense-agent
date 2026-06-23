# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import logging
import os
from typing import Any

import vertexai
from dotenv import load_dotenv
from google.adk.artifacts import GcsArtifactService, InMemoryArtifactService
from google.cloud import logging as google_cloud_logging
from vertexai.agent_engines.templates.adk import AdkApp

from app.agent import app as adk_app
from app.app_utils.telemetry import setup_telemetry
from app.app_utils.typing import Feedback

# Load environment variables from .env file at runtime
load_dotenv()


class AgentEngineApp(AdkApp):
    def set_up(self) -> None:
        """Initialize the agent engine app with logging and telemetry."""
        vertexai.init()
        setup_telemetry()
        super().set_up()
        logging.basicConfig(level=logging.INFO)
        logging_client = google_cloud_logging.Client()
        self.logger = logging_client.logger(__name__)
        if gemini_location:
            os.environ["GOOGLE_CLOUD_LOCATION"] = gemini_location

    def register_feedback(self, feedback: dict[str, Any]) -> None:
        """Collect and log feedback."""
        feedback_obj = Feedback.model_validate(feedback)
        self.logger.log_struct(feedback_obj.model_dump(), severity="INFO")

    def query(
        self,
        *,
        input: Any | None = None,
        message: Any | None = None,
        user_id: str | None = None,
        session_id: str | None = None,
        resume_inputs: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> Any:
        """Robust query method that auto-handles Playground chat limitations."""
        # Normalize inputs coming from the Playground (which sends 'input')
        resolved_message = message if message is not None else input
        resolved_user_id = user_id if user_id is not None else "playground-user"

        # Check if we need to auto-resume based on a pending RequestInput
        if session_id and resolved_message and not resume_inputs:
            state = self.app.state_manager.get_state(session_id)
            if state and state.pending_interrupts:
                # We are paused! Map the raw chat text to the expected resume_inputs
                interrupt_id = state.pending_interrupts[-1].interrupt_id
                resume_inputs = {interrupt_id: str(resolved_message)}
                # Clear the new message to prevent ADK from treating it as a new prompt
                resolved_message = ""

        events = list(self.stream_query(
            message=resolved_message,
            user_id=resolved_user_id,
            session_id=session_id, 
            resume_inputs=resume_inputs, 
            **kwargs
        ))
        return events

    def register_operations(self) -> dict[str, list[str]]:
        """Registers the operations of the Agent."""
        operations = super().register_operations()
        operations[""] = [*operations.get("", []), "register_feedback", "query"]
        
        # Remove unsupported async modes to prevent SDK instantiation errors
        if "async" in operations:
            del operations["async"]
        if "async_stream" in operations:
            del operations["async_stream"]
            
        return operations

    def clone(self) -> "AgentEngineApp":
        """Returns a clone of the Agent Runtime application."""
        return self


gemini_location = os.environ.get("GOOGLE_CLOUD_LOCATION")
logs_bucket_name = os.environ.get("LOGS_BUCKET_NAME")
agent_runtime = AgentEngineApp(
    app=adk_app,
    artifact_service_builder=lambda: (
        GcsArtifactService(bucket_name=logs_bucket_name)
        if logs_bucket_name
        else InMemoryArtifactService()
    ),
)
