# ruff: noqa
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

import os
import google.auth
from dotenv import load_dotenv

from google.adk.workflow import Workflow, node
from google.adk.events.request_input import RequestInput
from google.adk.events.event import Event
from google.adk.agents.context import Context
from google.adk.apps import App, ResumabilityConfig

# Load environment variables
load_dotenv()

# Fallback to AI Studio if GEMINI_API_KEY is present
if "GEMINI_API_KEY" in os.environ:
    os.environ.pop("GOOGLE_GENAI_USE_VERTEXAI", None)
else:
    # Use Google Cloud ADC
    try:
        _, project_id = google.auth.default()
        os.environ["GOOGLE_CLOUD_PROJECT"] = project_id or os.getenv("GOOGLE_CLOUD_PROJECT", "")
        os.environ["GOOGLE_CLOUD_LOCATION"] = os.getenv("GOOGLE_CLOUD_LOCATION", "global")
        os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "True"
    except google.auth.exceptions.DefaultCredentialsError:
        pass


from app.expense_agent import root_agent

# App Container
# Note: Resumability MUST be configured to use Human-in-the-Loop (RequestInput).
app = App(
    root_agent=root_agent,
    name="app",
    resumability_config=ResumabilityConfig(is_resumable=True)
)
