from enum import Enum


class JobName(str, Enum):
    INGEST_AUSTIN_DATA = "ingest_austin_data"
    GENERATE_VISUALS = "generate_visuals"
    EXPORT_REVIEW_PACKET = "export_review_packet"
