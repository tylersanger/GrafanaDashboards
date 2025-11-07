"""Common utilities for automated dashboards."""
from dataclasses import dataclass
from typing import Type, Generic, Optional, TypeVar, Union
from grafana_foundation_sdk.builders.timeseries import Panel as TimeseriesPanel
from grafana_foundation_sdk.builders.barchart import Panel as BarChartPanel
from grafana_foundation_sdk.builders.bargauge import Panel as BarGaugePanel
from grafana_foundation_sdk.builders.table import Panel as TablePanel
from grafana_foundation_sdk.builders.prometheus import Dataquery as PrometheusQuery
from grafana_foundation_sdk.builders.loki import Dataquery as LokiQuery
from grafana_foundation_sdk.builders.tempo import TempoQuery
from grafana_foundation_sdk.builders.common import ReduceDataOptions

# Define a TypeVar for panel types
T = TypeVar("T", bound=Union[TimeseriesPanel, BarChartPanel, BarGaugePanel, TablePanel])

# Define a TypeVar for query types
Q = TypeVar("Q", bound=Union[PrometheusQuery, LokiQuery, TempoQuery])

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
class Query(Generic[Q]):
    """Constructs a query object for dashboard panels.
    Attributes:
        query_type: Type[Q]
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

    query_type: Type[Q]
    expr: str
    datasource: "DataSources"
    legend: Optional[str] = "__auto"
    legend_format: Optional[str] = "timeseries"


@dataclass
class PanelOverride:
    """Defines a query override for panel customization.
    Attributes:
        query_ref: str
            Query refs start at 'A' and increment alphabetically for each query added to a panel. 
            For example, the first query added to a panel has a query_ref of 'A', the second 'B', and so on.
        axis_placement: str
            Specifies which axis the override applies to. Valid values are 'left' or 'right'.
        unit: str
            The unit to set for the specified query.
        axis_label: str
            The label to set for the specified axis.   
        """

    query_ref: str
    axis_placement: str
    unit: str
    axis_label: str


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
    MIMIR = {"type": "prometheus"}
    LOKI = {"type": "loki"}
    TEMPO = {"type": "tempo"}
    CLOUDWATCH = {"type": "cloudwatch"}
    MIXED = {"uid": "-- Mixed --", "type": "datasource"}
