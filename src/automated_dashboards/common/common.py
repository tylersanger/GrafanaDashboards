"""Common utilities for automated dashboards."""

from dataclasses import dataclass
from typing import Type, Generic, Optional, TypeVar, Union
from grafana_foundation_sdk.builders.timeseries import Panel as TimeseriesPanel
from grafana_foundation_sdk.builders.barchart import Panel as BarChartPanel
from grafana_foundation_sdk.builders.bargauge import Panel as BarGaugePanel
from grafana_foundation_sdk.builders.table import Panel as TablePanel
from grafana_foundation_sdk.builders.heatmap import Panel as HeatmapPanel
from grafana_foundation_sdk.builders.histogram import Panel as HistogramPanel
from grafana_foundation_sdk.builders.prometheus import Dataquery as PrometheusQuery
from grafana_foundation_sdk.builders.loki import Dataquery as LokiQuery
from grafana_foundation_sdk.builders.tempo import TempoQuery
from grafana_foundation_sdk.models.dashboard import DynamicConfigValue

# Define a TypeVar for panel types
T = TypeVar(
    "T",
    bound=Union[
        TimeseriesPanel, BarChartPanel, BarGaugePanel, TablePanel, HeatmapPanel, HistogramPanel
    ],
)

# Define a TypeVar for query types
Q = TypeVar("Q", bound=Union[PrometheusQuery, LokiQuery, TempoQuery])

@dataclass
class Panels(Generic[T]):
    """Defines common panel types used in dashboards.
    Attributes:
        TIMESERIES: Timeseries panel type.
        BARCHART: Bar chart panel type.
        BARGAUGE: Bar gauge panel type.
        TABLE: Table panel type.
        HEATMAP: Heatmap panel type.
        HISTOGRAM: Histogram panel type.
    """

    TIMESERIES: Type[T] = TimeseriesPanel
    BARCHART: Type[T] = BarChartPanel
    BARGAUGE: Type[T] = BarGaugePanel
    TABLE: Type[T] = TablePanel
    HEATMAP: Type[T] = HeatmapPanel
    HISTOGRAM: Type[T] = HistogramPanel

@dataclass
class QueryTypes(Generic[Q]):
    """Defines common query types used in dashboards.
    Attributes:
        PROMETHEUS: Prometheus query type.
        LOKI: Loki query type.
        TEMPO: Tempo query type.
    """

    PROMETHEUS: Type[Q] = PrometheusQuery
    LOKI: Type[Q] = LokiQuery
    TEMPO: Type[Q] = TempoQuery

@dataclass
class DeploymentEnv:
    """Defines deployment environments for dashboards.
    Attributes:
        PROD: Production environment.
        NONPROD: Non-production environment.
        TEMPO_PROD: Tempo production environment filter (tempo queries use dot notation)
        TEMPO_NONPROD: Tempo non-production environment filter (tempo queries use dot notation)
    """

    PROD: str = r'deployment_environment=~".*_PROD$|Prod"'
    NONPROD: str = r'deployment_environment!~".*_PROD$|Prod"'
    TEMPO_PROD: str = r'deployment.environment=~".*_PROD$|Prod"'
    TEMPO_NONPROD: str = r'deployment.environment!~".*_PROD$|Prod"'


@dataclass
class Query:
    """Constructs a query object for dashboard panels.
    Attributes:
        query_type: QueryTypes
            The type of query (e.g., PrometheusQuery).
        expr: str
            The query expression. Should be a raw string r'...' to handle special characters.
        datasource: DataSources
            The data source configuration for the query.
        legend: Optional[str]
            The series display for the query results.
        legend_format: Optonal[str]
            The format of the legend (e.g., "timeseries", "table").
    """

    query_type: QueryTypes
    expr: str
    datasource: "DataSources"
    legend: Optional[str] = "__auto"
    legend_format: Optional[str] = "timeseries"

@dataclass
class PanelOverride:
    """Defines an override for a panel.
    A valid override requires exactly one of the following attributes to be set: query_ref_override or field_to_override.

    Attributes:
        query_ref_override: Optional[str]
            The reference ID of the query to override (e.g., "A", "B").
        field_to_override: Optional[str]
            The name of the field to apply the override to.
        values: list[DynamicConfigValue]
            A list of dynamic configuration values for the override.
    """
    query_ref_override: Optional[str] = None
    field_to_override: Optional[str] = None
    values: list[DynamicConfigValue] = []

    def __post_init__(self):
        if bool(self.query_ref_override) + bool(self.field_to_override) != 1:
            raise ValueError(
                "A PanelOverride requires exactly one override type to be set: query_ref or field."
            )


@dataclass
class DataSources:
    """Common data sources used in dashboards.
    Attributes:
        MIMIR: The datasource where metrics are stored.
        LOKI: The datasource where logs are stored.
        TEMPO: The datasource where traces are stored.
        CLOUDWATCH: The datasource for AWS CloudWatch metrics.
        MIXED: A mixed datasource for panels using multiple data sources.
    """

    MIMIR = {"type": "prometheus", "uid": "eeou8qj3gbvgge"}
    LOKI = {"type": "loki", "uid": "eeou8ipbcojcwc"}
    TEMPO = {"type": "tempo", "uid": "aeou8l7tjqk8wd"}
    CLOUDWATCH = {"type": "cloudwatch", "uid": "fepgcad6xa4u8b"}
    MIXED = {"uid": "-- Mixed --", "type": "datasource"}
