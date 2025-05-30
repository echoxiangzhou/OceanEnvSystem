"""
CF标准相关模块

包含CF标准变量识别、验证和转换功能
"""

from .variable_identifier import CFVariableIdentifier, CFVariableSuggestion
from .global_attributes import GlobalAttributeGenerator, GlobalAttributeSuggestion

__all__ = [
    'CFVariableIdentifier',
    'CFVariableSuggestion',
    'GlobalAttributeGenerator', 
    'GlobalAttributeSuggestion'
] 