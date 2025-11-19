from grafana_foundation_sdk.builders.common import ScaleDistributionConfig
from grafana_foundation_sdk.models import units
from grafana_foundation_sdk.models.dashboard import DynamicConfigValue
from ..dashboard_builder import DashboardPanel, DashboardRow, DashboardSection
from ..common.common import DataSources, Query, PanelOverride, Panels, QueryTypes


class JamsInfrastructureMetricsSection(DashboardSection):
    """A dashboard section for infrastructure metrics."""

    def __init__(self, title: str):
        super().__init__(title)
        self._components = [
            DashboardRow(title),
            DashboardPanel(
                title="Memory Utilization",
                datasource=DataSources.MIMIR,
                unit=units.Percent,
                panel_type=Panels.TIMESERIES,
                queries=[
                    Query(
                        query_type=QueryTypes.PROMETHEUS,
                        expr=r"""
                            system_memory_utilization{{host_name=~'$Hostname', state!="free"}} * 100
                        """,
                        datasource=DataSources.MIMIR,
                        legend="{{host_name}}",
                    )
                ],
            ),
            DashboardPanel(
                title="CPU Utilization And Load",
                datasource=DataSources.MIMIR,
                panel_type=Panels.TIMESERIES,
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
                        query_type=QueryTypes.PROMETHEUS,
                        expr=r"""
                            100 *
                            sum by(host_name) (
                            system_cpu_utilization{{host_name=~'$Hostname', state!="idle"}}
                            )
                            / ignoring(state)
                            sum by(host_name) (
                            system_cpu_utilization{{host_name=~'$Hostname'}}
                            )
                        """,
                        datasource=DataSources.MIMIR,
                        legend="{{host_name}} - Utilization",
                    ),
                    Query(
                        query_type=QueryTypes.PROMETHEUS,
                        expr=r"""
                            100 *
                            sum(system_cpu_load_average_1m{{host_name=~'$Hostname'}}) by (host_name)
                            /
                            count(
                            count by (host_name, cpu)
                            (system_cpu_utilization{{host_name=~'$Hostname'}})
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
                panel_type=Panels.TIMESERIES,
                unit=units.MegabytesPerSecond,
                scale_distribution=ScaleDistributionConfig().log(log=2.0).type("log"),
                queries=[
                    Query(
                        query_type=QueryTypes.PROMETHEUS,
                        expr=r"""
                            rate(system_network_io{{host_name=~'$Hostname', direction="receive", device!="Loopback Pseudo-Interface 1"}}[5m]) / 1024 / 1024
                        """,
                        datasource=DataSources.MIMIR,
                        legend="{{host_name}}",
                    )
                ],
            ),
            DashboardPanel(
                title="Network Bytes Out",
                datasource=DataSources.MIMIR,
                panel_type=Panels.TIMESERIES,
                unit=units.MegabytesPerSecond,
                scale_distribution=ScaleDistributionConfig().log(log=2.0).type("log"),
                queries=[
                    Query(
                        query_type=QueryTypes.PROMETHEUS,
                        expr=r"""
                            rate(system_network_io{{host_name=~'$Hostname', direction="transmit", device!="Loopback Pseudo-Interface 1"}}[5m]) / 1024 / 1024
                        """,
                        datasource=DataSources.MIMIR,
                        legend="{{host_name}}",
                    )
                ],
            ),
            DashboardPanel(
                title="Disk I/O Read",
                datasource=DataSources.MIMIR,
                panel_type=Panels.TIMESERIES,
                unit=units.MegabytesPerSecond,
                scale_distribution=ScaleDistributionConfig().log(log=2.0).type("log"),
                queries=[
                    Query(
                        query_type=QueryTypes.PROMETHEUS,
                        expr=r"""
                            avg by (host_name, device) (
                            rate(system_disk_io{{host_name=~'$Hostname', direction="read"}}[5m])
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
                panel_type=Panels.TIMESERIES,
                unit=units.MegabytesPerSecond,
                scale_distribution=ScaleDistributionConfig().log(log=2.0).type("log"),
                queries=[
                    Query(
                        query_type=QueryTypes.PROMETHEUS,
                        expr=r"""
                            avg by (host_name, device) (
                            rate(system_disk_io{{host_name=~'$Hostname', direction="write"}}[5m])
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
                panel_type=Panels.TIMESERIES,
                unit=units.Seconds,
                scale_distribution=ScaleDistributionConfig().log(log=2.0).type("log"),
                queries=[
                    Query(
                        query_type=QueryTypes.PROMETHEUS,
                        expr=r"""
                            rate(system_disk_operation_time{{host_name=~'$Hostname'}}[5m])
                        """,
                        datasource=DataSources.MIMIR,
                        legend="{{device}} - {{host_name}}",
                    )
                ],
            ),
        ]

class JamsMetricsSection(DashboardSection):
    """A dashboard section for JAMS metrics."""
    
    def __init__(self, title: str, folder: str):
        super().__init__(title)
        self._folder = folder
        self._components = [
            DashboardRow(title),
            DashboardPanel(
                title="Exit Severity (JAMS)",
                datasource=DataSources.MIMIR,
                panel_type=Panels.BARGAUGE,
                visual_orientation="horizontal",
                queries=[
                    Query(
                        query_type=QueryTypes.PROMETHEUS,
                        expr=rf'sum by(exit_severity) (sum_over_time(jams_exit_severity_total{{folder="{self._folder}"}}[$__range]))',
                        datasource=DataSources.MIMIR
                    )
                ],
                overrides=[
                    PanelOverride(
                        field_to_override="Error",
                        values=[
                            DynamicConfigValue(
                                id_val="color",
                                value={"mode": "fixed", "fixedColor": "red"}
                            )
                        ]
                    ),
                    PanelOverride(
                        field_to_override="Warning",
                        values=[
                            DynamicConfigValue(
                                id_val="color",
                                value={"mode": "fixed", "fixedColor": "yellow"}
                            )
                        ]
                    ),
                    PanelOverride(
                        field_to_override="Success",
                        values=[
                            DynamicConfigValue(
                                id_val="color",
                                value={"mode": "fixed", "fixedColor": "green"}
                            )
                        ]
                    ),
                    PanelOverride(
                        field_to_override="Unknown",
                        values=[
                            DynamicConfigValue(
                                id_val="color",
                                value={"mode": "fixed", "fixedColor": "white"}
                            )
                        ]
                    ),
                ],
                unit=units.Number
            )
        ]