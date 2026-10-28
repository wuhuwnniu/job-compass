"""Extension point for a future validated visible-attribute classifier.

Implement classify(person_crop) and register a provider below. Do not infer identity,
income or relationships. Missing/low-confidence observations must stay unknown.
"""
from typing import Protocol

class AttributeProvider(Protocol):
    def classify(self,person_crop)->dict: ...

class UnavailableAttributes:
    def classify(self,person_crop):
        return {'status':'unsupported','observations':{}}

def get_attribute_provider()->AttributeProvider:
    return UnavailableAttributes()
