"""
This is the 'golden path' default dashboard configuration.
"""

from grafana_foundation_sdk.builders.common import (
    ScaleDistributionConfig,
    ReduceDataOptions,
    VizLegendOptions,
)
from grafana_foundation_sdk.builders.prometheus import Dataquery as PrometheusQuery
from grafana_foundation_sdk.builders.tempo import TempoQuery
from grafana_foundation_sdk.builders.loki import Dataquery as LokiQuery
from grafana_foundation_sdk.builders.timeseries import Panel as TimeseriesPanel
from grafana_foundation_sdk.builders.barchart import Panel as BarChartPanel
from grafana_foundation_sdk.builders.bargauge import Panel as BarGaugePanel
from grafana_foundation_sdk.builders.table import Panel as TablePanel
from grafana_foundation_sdk.models.dashboard import DataTransformerConfig, DynamicConfigValue
from grafana_foundation_sdk.models import units
from ..dashboard_builder import DashboardPanel, DashboardRow, DashboardSection
from ..common.common import Query, DataSources, PanelOverride, DeploymentEnv


class ServiceSummarySection(DashboardSection):
    """A dashboard section summarizing service metrics."""

    def __init__(self, title: str, service_name: str, env: DeploymentEnv):
        super().__init__(title)
        self._env = env
        self._components = [
            DashboardRow(title),
            DashboardPanel(
                title="Requests",
                datasource=DataSources.MIMIR,
                queries=[
                    Query(
                        query_type=PrometheusQuery,
                        expr=f"""sum(increase(http_server_request_duration_count{{{self._env}, service_name="{service_name}"}}[5m]))""",
                        datasource=DataSources.MIMIR,
                    )
                ],
                panel_type=TimeseriesPanel,
            ),
            DashboardPanel(
                title="Error Rate | 401's",
                datasource=DataSources.MIMIR,
                queries=[
                    Query(
                        query_type=PrometheusQuery,
                        expr=f"""sum by(http_response_status_code) (increase(http_server_request_duration_count{{{self._env}, service_name="{service_name}", http_response_status_code=~"401"}}[5m]))""",
                        datasource=DataSources.MIMIR,
                    )
                ],
                panel_type=BarChartPanel,
            ),
            DashboardPanel(
                title="Time Spent",
                datasource=DataSources.MIMIR,
                panel_type=BarChartPanel,
                viz_legend_options=VizLegendOptions()
                .show_legend(True)
                .placement("bottom"),
                queries=[
                    Query(
                        query_type=PrometheusQuery,
                        expr=rf"""
                            sum by (server_address) (
                                rate(http_client_request_duration_sum{{
                                    {self._env},
                                    server_address!~"127.0.0.1|localhost|169\\.[0-9]+\\.[0-9]+\\.[0-9]+",
                                    service_name="{service_name}"
                                }}[5m])
                            )
                            /
                            scalar(
                                sum by () (
                                    rate(http_client_request_duration_sum{{
                                        {self._env},
                                        server_address!~"127.0.0.1|localhost|169\\.[0-9]+\\.[0-9]+\\.[0-9]+",
                                        service_name="{service_name}"
                                    }}[5m])
                                )
                            )
                            """,
                        datasource=DataSources.MIMIR,
                        legend="{{server_address}}",
                    )
                ],
                unit=units.PercentUnit,
                stacking_mode="percent",
            ),
            DashboardPanel(
                title="Error Rate | 4xx, 5xx | Excluding 401's",
                datasource=DataSources.MIMIR,
                queries=[
                    Query(
                        query_type=PrometheusQuery,
                        expr=rf"""sum by(http_response_status_code) (increase(http_server_request_duration_count{{{self._env},
                                service_name="{service_name}", http_response_status_code!~"2..|3..|1..|401"}}[5m]))
                                """,
                        datasource=DataSources.MIMIR,
                    )
                ],
                panel_type=BarGaugePanel,
                visual_orientation="horizontal",
                display_mode="lcd",
            ),
            DashboardPanel(
                title="Pxx Latency",
                datasource=DataSources.MIMIR,
                scale_distribution=ScaleDistributionConfig().log(log=2.0).type("log"),
                queries=[
                    Query(
                        query_type=PrometheusQuery,
                        expr=rf"""
                        histogram_quantile(0.75,
                        sum by (le, service_name) (
                            increase(http_server_request_duration_bucket{{{self._env}, service_name='{service_name}'}}[5m])
                        )
                        )
                        """,
                        datasource=DataSources.MIMIR,
                        legend="{{service_name}} - P75",
                    ),
                    Query(
                        query_type=PrometheusQuery,
                        expr=rf"""
                        histogram_quantile(0.95,
                        sum by (le, service_name) (
                            increase(http_server_request_duration_bucket{{{self._env}, service_name='{service_name}'}}[5m])
                        )
                        )
                        """,
                        datasource=DataSources.MIMIR,
                        legend="{{service_name}} - P95",
                    ),
                    Query(
                        query_type=PrometheusQuery,
                        expr=rf"""
                        histogram_quantile(0.50,
                        sum by (le, service_name) (
                            increase(http_server_request_duration_bucket{{{self._env}, service_name='{service_name}'}}[5m])
                        )
                        )
                        """,
                        datasource=DataSources.MIMIR,
                        legend="{{service_name}} - P50",
                    ),
                    Query(
                        query_type=PrometheusQuery,
                        expr=rf"""
                        histogram_quantile(0.90,
                        sum by (le, service_name) (
                            increase(http_server_request_duration_bucket{{{self._env}, service_name='{service_name}'}}[5m])
                        )
                        )
                        """,
                        datasource=DataSources.MIMIR,
                        legend="{{service_name}} - P90",
                    ),
                ],
                panel_type=TimeseriesPanel,
                unit=units.Seconds,
            ),
        ]


class EndpointsSection(DashboardSection):
    """A dashboard section for endpoint-specific metrics."""

    def __init__(self, title: str, service_name: str, env: DeploymentEnv):
        super().__init__(title)
        self._env = env
        self._components = [
            DashboardRow(title),
            DashboardPanel(
                title="Requests",
                datasource=DataSources.MIMIR,
                queries=[
                    Query(
                        query_type=PrometheusQuery,
                        expr=rf"""
                            sum by (http_route) (
                                increase(http_server_request_duration_count{{service_name='{service_name}', {self._env}, http_route!=""}}[5m])
                            )
                            """,
                        datasource=DataSources.MIMIR,
                    )
                ],
                panel_type=TimeseriesPanel,
            ),
            DashboardPanel(
                title="P95 Latency",
                unit=units.Seconds,
                scale_distribution=ScaleDistributionConfig().log(log=2.0).type("log"),
                datasource=DataSources.MIMIR,
                queries=[
                    Query(
                        query_type=PrometheusQuery,
                        expr=rf"""
                            histogram_quantile(
                                0.95,
                                sum by(http_route,le) (
                                    increase(http_server_request_duration_bucket{{service_name='{service_name}', {self._env}, http_route!=""}}[5m])
                                )
                            )
                            """,
                        datasource=DataSources.MIMIR,
                    )
                ],
                panel_type=TimeseriesPanel,
            ),
            DashboardPanel(
                title="Requests Count By Route",
                datasource=DataSources.MIMIR,
                visual_orientation="horizontal",
                display_mode="lcd",
                panel_type=BarGaugePanel,
                reduce_options=ReduceDataOptions()
                .values(True)
                .calcs(["sum"])
                .fields(r"/^Value \(sum\)$/"),
                queries=[
                    Query(
                        query_type=PrometheusQuery,
                        expr=rf"""
                            sum by (http_route) (
                                increase(http_server_request_duration_count{{service_name='{service_name}', {self._env}, http_route!=""}}[5m])
                            )
                        """,
                        datasource=DataSources.MIMIR,
                        legend_format="table",
                    )
                ],
                transformations=[
                    DataTransformerConfig(
                        id_val="groupBy",
                        options={
                            "fields": {
                                "Value": {
                                    "aggregations": ["sum"],
                                    "operation": "aggregate",
                                },
                                "http_route": {
                                    "aggregations": ["sum"],
                                    "operation": "groupby",
                                },
                            }
                        },
                    ),
                    DataTransformerConfig(
                        id_val="sortBy",
                        options={
                            "fields": {},
                            "sort": [{"desc": True, "field": "Value (sum)"}],
                        },
                    ),
                ],
            ),
            DashboardPanel(
                title="Requests Time Spent By Route",
                datasource=DataSources.MIMIR,
                panel_type=BarGaugePanel,
                display_mode="lcd",
                visual_orientation="horizontal",
                unit=units.Milliseconds,
                reduce_options=ReduceDataOptions()
                .values(True)
                .calcs(["sum"])
                .fields(r"/^Value \(sum\)$/"),
                queries=[
                    Query(
                        query_type=PrometheusQuery,
                        expr=rf"""
                            sum by (http_route) (
                                increase(http_server_request_duration_sum{{service_name='{service_name}', {self._env}, http_route!=""}}[5m])
                            )
                        """,
                        datasource=DataSources.MIMIR,
                        legend_format="table",
                    )
                ],
                transformations=[
                    DataTransformerConfig(
                        id_val="groupBy",
                        options={
                            "fields": {
                                "Value": {
                                    "aggregations": ["sum"],
                                    "operation": "aggregate",
                                },
                                "http_route": {
                                    "aggregations": ["sum"],
                                    "operation": "groupby",
                                },
                            }
                        },
                    ),
                    DataTransformerConfig(
                        id_val="sortBy",
                        options={
                            "fields": {},
                            "sort": [{"desc": True, "field": "Value (sum)"}],
                        },
                    ),
                ],
            ),
        ]


class InfrastructureMetricsSection(DashboardSection):
    """A dashboard section for infrastructure metrics."""

    def __init__(self, title: str):
        super().__init__(title)
        self._components = [
            DashboardRow(title),
            DashboardPanel(
                title="Memory Utilization",
                datasource=DataSources.MIMIR,
                unit="percent",
                panel_type=TimeseriesPanel,
                queries=[
                    Query(
                        query_type=PrometheusQuery,
                        expr=r"""
                            system_memory_utilization{host_name=~'$Hostname', state!="free"} * 100
                        """,
                        datasource=DataSources.MIMIR,
                        legend="{{host_name}}",
                    )
                ],
            ),
            DashboardPanel(
                title="CPU Utilization And Load",
                datasource=DataSources.MIMIR,
                panel_type=TimeseriesPanel,
                overrides=[
                    PanelOverride(
                        query_ref_override="A",
                        values=[
                            DynamicConfigValue(
                                id_val="custom.axisPlacement",
                                value="left",
                            ),
                            DynamicConfigValue(
                                id_val="unit",
                                value=units.Percent
                            ),
                            DynamicConfigValue(
                                id_val="custom.axisLabel",
                                value="CPU Utilization",
                            )
                        ]
                    ),
                    PanelOverride(
                        query_ref_override="B",
                        values=[
                            DynamicConfigValue(
                                id_val="custom.axisPlacement",
                                value="right",
                            ),
                            DynamicConfigValue(
                                id_val="unit",
                                value=units.Percent
                            ),
                            DynamicConfigValue(
                                id_val="custom.axisLabel",
                                value="CPU Load %",
                            )
                        ]
                    )
                ],
                unit=units.Percent,
                queries=[
                    Query(
                        query_type=PrometheusQuery,
                        expr=r"""
                            100 *
                            sum by(host_name) (
                            system_cpu_utilization{host_name=~"$Hostname", state!="idle"}
                            )
                            / ignoring(state)
                            sum by(host_name) (
                            system_cpu_utilization{host_name=~"$Hostname"}
                            )
                        """,
                        datasource=DataSources.MIMIR,
                        legend="{{host_name}} - Utilization",
                    ),
                    Query(
                        query_type=PrometheusQuery,
                        expr=r"""
                            100 *
                            sum(system_cpu_load_average_1m{host_name=~"$Hostname"}) by (host_name)
                            /
                            count(
                            count by (host_name, cpu)
                            (system_cpu_utilization{host_name=~"$Hostname"})
                            ) by (host_name)
                        """,
                        datasource=DataSources.MIMIR,
                        legend="{{host_name}} - Load",
                    ),
                ],
            ),
            DashboardPanel(
                title="Network Bytes In",
                datasource=DataSources.MIMIR,
                panel_type=TimeseriesPanel,
                unit=units.MegabytesPerSecond,
                scale_distribution=ScaleDistributionConfig().log(log=2.0).type("log"),
                queries=[
                    Query(
                        query_type=PrometheusQuery,
                        expr=r"""
                            rate(system_network_io{host_name=~'$Hostname', direction="receive", device!="Loopback Pseudo-Interface 1"}[5m]) / 1024 / 1024
                        """,
                        datasource=DataSources.MIMIR,
                        legend="{{host_name}}",
                    )
                ],
            ),
            DashboardPanel(
                title="Network Bytes Out",
                datasource=DataSources.MIMIR,
                panel_type=TimeseriesPanel,
                unit=units.MegabytesPerSecond,
                scale_distribution=ScaleDistributionConfig().log(log=2.0).type("log"),
                queries=[
                    Query(
                        query_type=PrometheusQuery,
                        expr=r"""
                            rate(system_network_io{host_name=~'$Hostname', direction="transmit", device!="Loopback Pseudo-Interface 1"}[5m]) / 1024 / 1024
                        """,
                        datasource=DataSources.MIMIR,
                        legend="{{host_name}}",
                    )
                ],
            ),
            DashboardPanel(
                title="Disk I/O Read",
                datasource=DataSources.MIMIR,
                panel_type=TimeseriesPanel,
                unit=units.MegabytesPerSecond,
                scale_distribution=ScaleDistributionConfig().log(log=2.0).type("log"),
                queries=[
                    Query(
                        query_type=PrometheusQuery,
                        expr=r"""
                            avg by (host_name, device) (
                            rate(system_disk_io{host_name=~"$Hostname", direction="read"}[5m])
                            ) / 1024 / 1024
                        """,
                        datasource=DataSources.MIMIR,
                        legend="{{device}} - {{host_name}}",
                    )
                ],
            ),
            DashboardPanel(
                title="Disk I/O Write",
                datasource=DataSources.MIMIR,
                panel_type=TimeseriesPanel,
                unit=units.MegabytesPerSecond,
                scale_distribution=ScaleDistributionConfig().log(log=2.0).type("log"),
                queries=[
                    Query(
                        query_type=PrometheusQuery,
                        expr=r"""
                            avg by (host_name, device) (
                            rate(system_disk_io{host_name=~"$Hostname", direction="write"}[5m])
                            ) / 1024 / 1024
                        """,
                        datasource=DataSources.MIMIR,
                        legend="{{device}} - {{host_name}}",
                    )
                ],
            ),
            DashboardPanel(
                title="Disk I/O Time",
                datasource=DataSources.MIMIR,
                panel_type=TimeseriesPanel,
                unit=units.Seconds,
                scale_distribution=ScaleDistributionConfig().log(log=2.0).type("log"),
                queries=[
                    Query(
                        query_type=PrometheusQuery,
                        expr=r"""
                            rate(system_disk_operation_time{host_name=~'$Hostname'}[5m])
                        """,
                        datasource=DataSources.MIMIR,
                        legend="{{device}} - {{host_name}}",
                    )
                ],
            ),
        ]


class RuntimeMetricsSection(DashboardSection):
    """A dashboard section for runtime metrics."""

    def __init__(self, title: str, service_name: str, env: DeploymentEnv):
        super().__init__(title)
        self._service_name = service_name
        self._env = env
        self._components = [
            DashboardRow(title),
            DashboardPanel(
                title="Thread Count",
                datasource=DataSources.MIMIR,
                panel_type=TimeseriesPanel,
                queries=[
                    Query(
                        query_type=PrometheusQuery,
                        expr=rf"""
                                sum by(host_name) (process_runtime_dotnet_thread_pool_threads_count{{service_name="{self._service_name}", {self._env}}})
                            """,
                        datasource=DataSources.MIMIR,
                        legend="{{host_name}}",
                    )
                ],
            ),
            DashboardPanel(
                title="Thread Contention",
                datasource=DataSources.MIMIR,
                panel_type=TimeseriesPanel,
                queries=[
                    Query(
                        query_type=PrometheusQuery,
                        expr=rf"""
                                sum by (host_name) (
                                increase(process_runtime_dotnet_monitor_lock_contention_count{{service_name="{self._service_name}", {self._env}}}[5m])
)
                            """,
                        datasource=DataSources.MIMIR,
                        legend="{{host_name}}",
                    )
                ],
            ),
        ]


class TracesSection(DashboardSection):
    """A dashboard section to display service traces"""

    def __init__(self, title: str, service_name: str, env: DeploymentEnv):
        super().__init__(title)
        self._service_name = service_name
        self._env = env
        self._components = [
            DashboardRow(title),
            DashboardPanel(
                title="Traces",
                datasource=DataSources.TEMPO,
                panel_type=TablePanel,
                queries=[
                    Query(
                        query_type=TempoQuery,
                        expr=rf"""
                            {{resource.service.name="{self._service_name}" && resource.{self._env}}}
                        """,
                        datasource=DataSources.TEMPO,
                    )
                ],
            ),
        ]


class LogsSection(DashboardSection):
    """A dashboard section to display service logs"""

    def __init__(self, title: str, service_name: str, env: DeploymentEnv):
        super().__init__(title)
        self._service_name = service_name
        self._env = env
        self._components = [
            DashboardRow(title),
            DashboardPanel(
                title="Logs",
                datasource=DataSources.LOKI,
                panel_type=TablePanel,
                queries=[
                    Query(
                        query_type=LokiQuery,
                        expr=rf"""
                            {{{self._env}, service_name="{self._service_name}"}}
                        """,
                        datasource=DataSources.LOKI,
                    )
                ],
            ),
        ]
