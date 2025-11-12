"""
Dashboard configuration for Canada Branch Network Monitoring.
"""

from grafana_foundation_sdk.builders.prometheus import Dataquery as PrometheusQuery
from grafana_foundation_sdk.builders.heatmap import Panel as HeatmapPanel
from grafana_foundation_sdk.builders.histogram import Panel as HistogramPanel
from ..dashboard_builder import DashboardPanel, DashboardSection, DashboardRow
from ..common.common import Query, DataSources


class NetworkDashboardHeatmapSection(DashboardSection):
    """The section containing panels for the Network Dashboard."""

    def __init__(self, title: str):
        super().__init__(title)
        self._components = [
            DashboardRow(title=title),
            DashboardPanel(
                title="Ping RTT - Switch",
                datasource=DataSources.MIMIR,
                queries=[
                    Query(
                        query_type=PrometheusQuery,
                        expr=r'sort(sum by(le) (ping_rtt_bucket{le!="+Inf", device_name="switch"}))',
                        datasource=DataSources.MIMIR,
                        legend_format="heatmap",
                    )
                ],
                panel_type=HeatmapPanel,
            ),
            DashboardPanel(
                title="Ping RTT - vEdge",
                datasource=DataSources.MIMIR,
                queries=[
                    Query(
                        query_type=PrometheusQuery,
                        expr=r'sort(sum by(le) (ping_rtt_bucket{le!="+Inf", device_name="vedge"}))',
                        datasource=DataSources.MIMIR,
                        legend_format="heatmap",
                    )
                ],
                panel_type=HeatmapPanel,
            )
        ]

class NetworkDashboardHistogramSection(DashboardSection):
    """Ping statistics histogram section for the Network Dashboard. """
    def __init__(self, title: str):
        super().__init__(title)
        self._components = [
            DashboardRow(title=title),
            DashboardPanel(
                title="Ping RTT - Switch",
                datasource=DataSources.MIMIR,
                queries=[
                    Query(
                        query_type=PrometheusQuery,
                        expr=r'sort(sum by (le) (ping_rtt_bucket{device_name="switch"}))',
                        datasource=DataSources.MIMIR,
                        legend_format="heatmap",
                    )
                ],
                panel_type=HistogramPanel
            ),
            DashboardPanel(
                title="Ping RTT - vEdge",
                datasource=DataSources.MIMIR,
                queries=[
                    Query(
                        query_type=PrometheusQuery,
                        expr=r'sort(sum by (le) (ping_rtt_bucket{device_name="vedge"}))',
                        datasource=DataSources.MIMIR,
                        legend_format="heatmap",
                    )
                ],
                panel_type=HistogramPanel
            )
        ]
