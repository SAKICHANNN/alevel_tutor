"""
A-Level Tutor Agent — public API surface.
"""
from agent.tutoring.core import Agent
from agent.config import MODELS, Subject, SUBJECTS, SUBJECT_BY_CODE, register_subject
from agent.retrieval.builder import build_all
from agent.retrieval.search import get_collection_stats
from agent.ocr.content_types import SUBJECT_CONTENT_TYPES, get_subject_types, get_p0_types
from agent.ocr.pipeline import OCRPipeline, get_pipeline
