import pandas as pd
from dash import dcc
import dash_cytoscape as cyto

from shift_suite.tasks import enhanced_blueprint_callbacks as ebc
import dash_app


def test_feature_importance_graph_returns_graph():
    df = pd.DataFrame({'feature': ['A', 'B'], 'importance': [0.6, 0.4]})
    graph = ebc.create_feature_importance_graph(df)
    assert isinstance(graph, dcc.Graph)


def test_create_knowledge_network_graph_returns_cytoscape():
    network = {'nodes': [{'id': '1', 'label': 'Rule1'}], 'edges': []}
    graph = dash_app.create_knowledge_network_graph(network)
    assert isinstance(graph, cyto.Cytoscape)
