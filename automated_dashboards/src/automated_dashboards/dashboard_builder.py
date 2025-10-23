"""
An interface that implements a high-level dashboard builder using the Grafana Foundation SDK.
High-level abstractions include DashboardSection, DashboardRow, and DashboardPanel to facilitate
the construction of complex dashboards.
"""

from typing import List, Optional, Union, Type, Generic
import re
import os
import requests
from collections import defaultdict
from string import ascii_uppercase
from abc import ABC, abstractmethod
from grafana_foundation_sdk.cog.encoder import JSONEncoder
from grafana_foundation_sdk.builders.dashboard import Dashboard, Row, QueryVariable
from grafana_foundation_sdk.builders.timeseries import Panel as TimeseriesPanel
from grafana_foundation_sdk.builders.barchart import Panel as BarChartPanel
from grafana_foundation_sdk.builders.bargauge import Panel as BarGaugePanel
from grafana_foundation_sdk.builders.tempo import TempoQuery
from grafana_foundation_sdk.builders.prometheus import Dataquery as PrometheusQuery
from grafana_foundation_sdk.builders.loki import Dataquery as LokiQuery
from grafana_foundation_sdk.builders.common import ScaleDistributionConfig, ReduceDataOptions, VizLegendOptions
from grafana_foundation_sdk.models.common import TimeZoneBrowser
from grafana_foundation_sdk.models.dashboard import DataTransformerConfig
from .common.common import Query, PanelOverride, DataSources, T, Q


class DashboardComponent(ABC):
    """Base interface for dashboard components."""

    @abstractmethod
    def construct(self) -> Union[Row, TimeseriesPanel, BarChartPanel]:
        """Return the SDK object representing this component."""


class DashboardRow(Row, DashboardComponent):
    """A row component extending Grafana SDK's Row."""

    def __init__(self, title: str):
        super().__init__(title)
        self.title(title)

    def construct(self) -> Row:
        return self


class DashboardPanel(DashboardComponent, Generic[T, Q]):
    """A panel component extending Grafana SDK's Panel."""

    def __init__(
        self,
        title: str,
        queries: list[Query],
        datasource: DataSources,
        panel_type: Type[T],
        unit: Optional[str] = "none",
        stacking_mode: Optional[str] = "none",
        visual_orientation: Optional[str] = "auto",
        display_mode: Optional[str] = "basic",
        scale_distribution: Optional[ScaleDistributionConfig] = ScaleDistributionConfig().type(
            "linear"
        ),
        transformations: Optional[List[DataTransformerConfig]] = None,
        overrides: Optional[List[PanelOverride]] = None,
        reduce_options: Optional[ReduceDataOptions] = None,
        viz_legend_options: Optional[VizLegendOptions] = None,
    ):
        super().__init__()
        self._title = title
        self._queries = queries
        self._unit = unit
        self._datasource = datasource
        self._panel_type = panel_type
        self._stacking_mode = stacking_mode
        self._orientation = visual_orientation
        self._display_mode = display_mode
        self._scale_distribution = scale_distribution
        self._transformations = transformations
        self._overrides = overrides
        self._reduce_options = reduce_options
        self._viz_legend_options = viz_legend_options
    
    def get_queries(self) -> list[Query]:
        """Return the list of queries associated with this panel."""
        return self._queries

    def get_component_name(self) -> str:
        """Return the name of this section."""
        return self._title

    def construct(self) -> T:
        panel = (
            self._panel_type()
            .title(self._title)
            .unit(self._unit)
            .datasource(self._datasource)
        )
        if self._transformations:
            for transformation in self._transformations:
                panel.with_transformation(transformation)
        if self._overrides:
            for override in self._overrides:
                panel.override_by_query(override.query_ref, [
                    {"id": "custom.axisPlacement", "value": override.axis_placement},
                    {"id": "unit", "value": override.unit},
                    {"id": "custom.axisLabel", "value": override.axis_label}
                ])
        if self._reduce_options:
            panel.reduce_options(self._reduce_options)
        
        if isinstance(panel, BarChartPanel):
            panel.stacking(self._stacking_mode)
            panel.legend(self._viz_legend_options if self._viz_legend_options else VizLegendOptions())
        if isinstance(panel, BarGaugePanel):
            panel.orientation(self._orientation).display_mode(self._display_mode)
        if isinstance(panel, TimeseriesPanel):
            panel.scale_distribution(self._scale_distribution)
        for idx, query in enumerate(self._queries):
            ref_id = ascii_uppercase[idx]
            q = query.query_type()
            if isinstance(q, TempoQuery):
                q.query(query.expr.strip())
            if isinstance(q, (PrometheusQuery, LokiQuery)):
                q.expr(query.expr.strip())
            if isinstance(q, PrometheusQuery):
                q.legend_format(query.legend)
                q.format(query.legend_format)
            q.datasource(query.datasource)
            q.ref_id(ref_id)
            panel.with_target(q)
        return panel


class DashboardSection:
    """A logical section grouping multiple dashboard components."""

    def __init__(self, name: str):
        self._name = name
        self._components: List[DashboardComponent] = []

    def add_component(self, component: DashboardComponent) -> "DashboardSection":
        """Add a component to this section."""
        self._components.append(component)
        return self
    
    def get_components(self) -> List[DashboardComponent]:
        """Return the list of components in this section."""
        return self._components


    def construct(self) -> List[Union[Row, TimeseriesPanel]]:
        """Return a list of built SDK components."""
        return [c.construct() for c in self._components]


class DashboardBuilder(Dashboard):
    """High-level builder to compose Grafana dashboards from sections."""

    def __init__(
        self,
        title: str,
        tags: List[str],
        sections: List[DashboardSection],
        env: str,
        service: str,
        time_range: tuple[str, str] = ("now-1h", "now"),
        refresh: str = "10s",
    ):
        super().__init__(title)
        self.tags(tags)
        self.uid(f"{service}-{env}-dashboard".lower())
        self.refresh(refresh)
        self.timezone(TimeZoneBrowser)
        self.time(*time_range)
        self._sections = sections
        self._variables = defaultdict(object)
        self._built_dashboard = None

    def add_section(self, section: DashboardSection) -> "DashboardBuilder":
        """Add a section to the dashboard."""
        self._sections.append(section)
        return self
    
    def add_dashboard_variable(self, name: str, query: str, multi_select: bool,
                               include_all: bool, data_source: DataSources) -> None:
        """Add a dashboard level variable to use in queries."""
        variable = (QueryVariable(name)
                    .datasource(data_source)
                    .query(query)
                    .multi(multi_select)
                    .include_all(include_all)
                    .allow_custom_value(False))
        self._variables[name] = variable

    def build(self) -> Dashboard:
        """Compile all sections and return an SDK Dashboard object."""

        try:
            self._validate()
        except ValueError as e:
            print(e)
        else:
            if self._variables:
                db_vars = list(self._variables.values())
                self.variables(db_vars)

            for section in self._sections:
                for component in section.construct():
                    if isinstance(component, DashboardRow):
                        self.with_row(component)
                    else:
                        self.with_panel(component)
        self._built_dashboard = super().build()
        return self._built_dashboard
    
    def deploy_to_grafana(self, folder: int) -> None:
        """Deploy the built dashboard to Grafana."""

        api_key = os.getenv("GRAFANA_API_KEY", None)
        if not api_key:
            raise EnvironmentError("GRAFANA_API_KEY environment variable not set.")
        else:
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }

            if not self._built_dashboard:
                self.build()
            
            complete_dashboard = {"dashboard": self._built_dashboard, "folderId": folder, "overwrite": True}
            encoder = JSONEncoder(indent=2, sort_keys=True)
            encoded_dashboard = encoder.encode(complete_dashboard)
            r = requests.post(
                "https://grafana.attainfinance.com/api/dashboards/db",
                headers=headers,
                data=encoded_dashboard,
                timeout=10)
            r.raise_for_status()
       

    def _validate(self) -> None:
        """Validate the dashboard configuration before building"""
        for section in self._sections:
            for component in section.get_components():
                if isinstance(component, DashboardPanel):
                    queries = component.get_queries()
                    if not queries:
                        raise ValueError(f"Panel '{component.get_component_name()}' has no queries defined.")
                    else:
                        dashboard_variable_names = list(self._variables.keys())
                        for query in queries:
                            matches = re.findall(r"(['\"])(\$[^'\"]*)\1", query.expr)
                            matches = [match[1][1:] for match in matches]
                            for match in matches:
                                if match not in dashboard_variable_names:
                                    error_msg = f"ERROR: Query references dashboard variable that is not defined. Panel will return no data.\n" \
                                                f"Ensure the variable name is spelled correctly (case-sensitive) and has been added to the dashboard.\n" \
                                                f"Panel: {component.get_component_name()}\n" \
                                                f"Query: {query.expr.strip()}\n" \
                                                f"Referenced variable: {match}\n" \
                                                f"Defined dashboard variables: {dashboard_variable_names}."
                                    raise ValueError(error_msg)
