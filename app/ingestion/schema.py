from dataclasses import dataclass, field

@dataclass
class Section:
    text: str
    metadata: dict = field(default_factory=dict)