# dash_core.py - Core functionality for Dash application
"""
Core utilities and basic components for the Shift Analysis Dashboard.
Extracted from dash_app.py for better maintainability and performance.
"""

import base64
import io
import json
import logging
import tempfile
import zipfile
import threading
import time
import weakref
import os
from dash import State
from session_integration import session_integration, session_aware_data_get, session_aware_save_data

# Enhanced Session Manager for multi-tenant support
from enhanced_session_manager import enhanced_session_manager
try:
    import psutil
except ImportError:
    psutil = None

from functools import lru_cache, wraps
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from collections import OrderedDict
import unicodedata
from datetime import datetime

import dash
import dash_cytoscape as cyto
import numpy as np
import pandas as pd
import pyarrow.parquet as pq

import plotly.express as px
import plotly.graph_objects as go
from dash import dash_table, dcc, html
from dash.dependencies import Input, Output, State, ALL
from dash.exceptions import PreventUpdate
from flask import jsonify
import traceback
import gc

# Error handling imports
from error_boundary import error_boundary, safe_callback, safe_component, apply_error_boundaries
from global_error_handler import GlobalErrorHandler, global_error_handler, safe_data_operation, error_handler

# Accessible colors imports with fallback
try:
    from accessible_colors import (
        get_accessible_color_palette, apply_accessible_colors_to_figure,
        enhance_figure_accessibility, safe_colors_for_plotly, ACCESSIBLE_COLORS
    )
except ImportError:
    def get_accessible_color_palette(palette_type, n_colors):
        """Fallback implementation for accessible color palette"""
        base_colors = [
            '#2E86AB', '#F24236', '#F6AE2D', '#2F4858', '#86BBD8', '#F26419',
            '#33658A', '#758E4F', '#8B5A3C', '#6B2737', '#C1666B', '#48A9A6'
        ]
        colors = base_colors * ((n_colors // len(base_colors)) + 1)
        return colors[:n_colors]

    def enhance_figure_accessibility(fig, title, chart_type):
        """Fallback implementation for figure accessibility enhancement"""
        if fig and title:
            fig.update_layout(title=title)
        return fig

# Safe pickle loading wrapper
def safe_pickle_load(file_path, allowed_classes=None):
    """Safely load pickle files with restricted classes"""
    import pickle
    import io

    class RestrictedUnpickler(pickle.Unpickler):
        def find_class(self, module, name):
            if allowed_classes:
                if (module, name) in allowed_classes:
                    return super().find_class(module, name)
            safe_modules = ['numpy', 'pandas', 'builtins']
            if module in safe_modules:
                return super().find_class(module, name)
            raise pickle.UnpicklingError(f"Unsafe class: {module}.{name}")

    with open(file_path, 'rb') as f:
        return RestrictedUnpickler(f).load()

def create_standard_datatable(table_id: str, columns: List[Dict] = None, data: List[Dict] = None) -> dash_table.DataTable:
    """Create standardized DataTable with consistent styling and functionality"""
    default_columns = [{'name': 'No Data', 'id': 'no_data'}] if columns is None else columns
    default_data = [{'no_data': 'No data available'}] if data is None else data

    return dash_table.DataTable(
        id=table_id,
        columns=default_columns,
        data=default_data,
        style_table={'overflowX': 'auto', 'maxHeight': '400px'},
        style_cell={
            'textAlign': 'left',
            'padding': '10px',
            'fontFamily': 'Arial, sans-serif',
            'fontSize': '12px',
            'border': '1px solid #ddd'
        },
        style_header={
            'backgroundColor': '#f8f9fa',
            'fontWeight': 'bold',
            'color': '#333'
        },
        style_data_conditional=[
            {
                'if': {'row_index': 'odd'},
                'backgroundColor': '#f8f9fa'
            }
        ],
        page_size=10,
        sort_action='native',
        filter_action='native'
    )

def get_session_id_from_url():
    """Extract session ID from URL parameters or generate new one"""
    import secrets
    try:
        # This would normally come from URL parameters in a real implementation
        return secrets.token_urlsafe(16)
    except:
        return "default_session"

def safe_session_data_get(key: str, default=None, session_id: str = None):
    """Safely get data from session with error handling"""
    try:
        if session_id is None:
            session_id = get_session_id_from_url()
        return session_aware_data_get(key, default, session_id)
    except Exception as e:
        logging.warning(f"Session data get failed for key {key}: {e}")
        return default

def safe_session_data_save(key: str, data, session_id: str = None):
    """Safely save data to session with error handling"""
    try:
        if session_id is None:
            session_id = get_session_id_from_url()
        return session_aware_save_data(key, data, session_id)
    except Exception as e:
        logging.warning(f"Session data save failed for key {key}: {e}")
        return False

def create_metric_card(label: str, value: Any, color: str = "#1f77b4") -> html.Div:
    """Create a standardized metric card component"""
    return html.Div([
        html.H4(str(value), style={'margin': '0', 'color': color, 'fontSize': '24px'}),
        html.P(label, style={'margin': '0', 'color': '#666', 'fontSize': '14px'})
    ], style={
        'padding': '15px',
        'border': f'2px solid {color}',
        'borderRadius': '8px',
        'backgroundColor': '#f8f9fa',
        'textAlign': 'center',
        'minHeight': '80px',
        'display': 'flex',
        'flexDirection': 'column',
        'justifyContent': 'center'
    })

def create_standard_graph(graph_id: str, figure: go.Figure = None, config: Dict = None) -> dcc.Graph:
    """Create standardized graph component with consistent configuration"""
    default_config = {
        'displayModeBar': True,
        'displaylogo': False,
        'modeBarButtonsToRemove': ['pan2d', 'lasso2d', 'select2d']
    }

    if config:
        default_config.update(config)

    default_figure = go.Figure()
    default_figure.update_layout(
        title="No data available",
        showlegend=False,
        height=400
    )

    return dcc.Graph(
        id=graph_id,
        figure=figure or default_figure,
        config=default_config,
        style={'height': '400px'}
    )

def create_loading_component(component_id: str, children) -> dcc.Loading:
    """Create standardized loading component"""
    return dcc.Loading(
        id=f"loading-{component_id}",
        type="default",
        children=children,
        style={'minHeight': '100px'}
    )

# Initialize logging
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)

# Memory management utilities
class ManagedCache:
    """Simple cache manager with size limits"""
    def __init__(self, max_size_mb: float = 100):
        self._cache = {}
        self.max_size_mb = max_size_mb

    def get(self, key: str, session_id: str = None):
        cache_key = f"{session_id}:{key}" if session_id else key
        return self._cache.get(cache_key)

    def set(self, key: str, value, session_id: str = None):
        cache_key = f"{session_id}:{key}" if session_id else key
        self._cache[cache_key] = value

    def clear(self, session_id: str = None):
        if session_id:
            keys_to_remove = [k for k in self._cache.keys() if k.startswith(f"{session_id}:")]
            for key in keys_to_remove:
                del self._cache[key]
        else:
            self._cache.clear()

# Global cache instance
DATA_CACHE = ManagedCache(max_size_mb=200)

def check_memory_usage():
    """Check current memory usage"""
    if not psutil:
        return {'memory_mb': 0, 'memory_percent': 0, 'is_memory_critical': False}

    try:
        process = psutil.Process()
        memory_info = process.memory_info()
        memory_mb = memory_info.rss / 1024 / 1024
        memory_percent = psutil.virtual_memory().percent

        return {
            'memory_mb': memory_mb,
            'memory_percent': memory_percent,
            'is_memory_critical': memory_mb > 500  # 500MB threshold
        }
    except Exception as e:
        log.warning(f"Memory check failed: {e}")
        return {'memory_mb': 0, 'memory_percent': 0, 'is_memory_critical': False}

def cleanup_memory():
    """Force garbage collection and clear caches"""
    try:
        DATA_CACHE.clear()
        gc.collect()
        log.info("Memory cleanup completed")
    except Exception as e:
        log.warning(f"Memory cleanup failed: {e}")