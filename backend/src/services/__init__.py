"""Services for FitFindr — lazy imports to avoid loading heavy ML deps unnecessarily"""
__all__ = ["EmbeddingService", "ResumeParserService", "ScreeningService", "GraphScreeningService"]


def __getattr__(name: str):
    if name == "EmbeddingService":
        from .embedding_service import EmbeddingService
        return EmbeddingService
    if name == "ResumeParserService":
        from .resume_parser import ResumeParserService
        return ResumeParserService
    if name == "ScreeningService":
        from .screening_service import ScreeningService
        return ScreeningService
    if name == "GraphScreeningService":
        from .graph_service import GraphScreeningService
        return GraphScreeningService
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

