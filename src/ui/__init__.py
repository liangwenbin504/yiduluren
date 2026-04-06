"""
UI 组件包
"""

try:
    from .tianpan_widget import TianPanWidget, TianPanWithTianJiangWidget
except ImportError:
    from tianpan_widget import TianPanWidget, TianPanWithTianJiangWidget

__all__ = ['TianPanWidget', 'TianPanWithTianJiangWidget']
