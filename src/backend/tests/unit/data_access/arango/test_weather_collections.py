"""REQ-046 — assert the weather collections/edges are registered."""

from app.data_access.arango import collections as col


def test_document_collections_registered():
    assert col.WEATHER_FORECASTS == "weather_forecasts"
    assert col.WEATHER_SOURCE_CONFIGS == "weather_source_configs"
    assert col.WEATHER_FORECASTS in col.DOCUMENT_COLLECTIONS
    assert col.WEATHER_SOURCE_CONFIGS in col.DOCUMENT_COLLECTIONS


def test_edge_collections_registered():
    assert col.HAS_FORECAST == "has_forecast"
    assert col.HAS_WEATHER_SOURCE_CONFIG == "has_weather_source_config"
    assert col.HAS_FORECAST in col.EDGE_COLLECTIONS
    assert col.HAS_WEATHER_SOURCE_CONFIG in col.EDGE_COLLECTIONS


def test_graph_edge_definitions_present():
    defs = {ed["edge_collection"]: ed for ed in col.GRAPH_EDGE_DEFINITIONS}

    assert defs[col.HAS_FORECAST]["from_vertex_collections"] == [col.SITES]
    assert defs[col.HAS_FORECAST]["to_vertex_collections"] == [col.WEATHER_FORECASTS]
    assert defs[col.HAS_WEATHER_SOURCE_CONFIG]["from_vertex_collections"] == [col.SITES]
    assert defs[col.HAS_WEATHER_SOURCE_CONFIG]["to_vertex_collections"] == [col.WEATHER_SOURCE_CONFIGS]
