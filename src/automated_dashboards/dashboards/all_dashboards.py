from automated_dashboards.common.common import DataSources, DeploymentEnv
from automated_dashboards.dashboard_builder import DashboardBuilder
from automated_dashboards.helpers.default_dashboard import (
    ServiceSummarySection,
    EndpointsSection,
    InfrastructureMetricsSection,
    RuntimeMetricsSection,
    TracesSection,
    LogsSection,
)
from automated_dashboards.helpers.network_dash_default import (
    NetworkDashboardHistogramSection, 
    NetworkDashboardHeatmapSection
)
from requests import HTTPError

# Service Dashboards Deployment
services = [
    "creo",
    "webanalytics",
    "SummitApi",
    "affiliateleads",
    "Cashmoney",
    "lenddirect",
    "hotelcardifornia",
    "tiger-authentication",
    "voltaire",
]
envs = ["prod", "nonprod"]

print("Starting deployment of service dashboards...")
for service in services:
    for env in envs:
        if env == "prod":
            dash = DashboardBuilder(
                title=f"{service} | {env} | Service Dashboard",
                tags=[service, env, "DAC"],
                env=env,
                service=service,
                sections=[
                    ServiceSummarySection(
                        title="Service Summary",
                        service_name=service,
                        env=DeploymentEnv.PROD,
                    ),
                    EndpointsSection(
                        title="Endpoints", service_name=service, env=DeploymentEnv.PROD
                    ),
                    InfrastructureMetricsSection(title="Host Metrics"),
                    RuntimeMetricsSection(
                        title="Runtime Metrics",
                        service_name=service,
                        env=DeploymentEnv.PROD,
                    ),
                    TracesSection(
                        title="Traces",
                        service_name=service,
                        env=DeploymentEnv.TEMPO_PROD,
                    ),
                    LogsSection(
                        title="Logs", service_name=service, env=DeploymentEnv.PROD
                    ),
                ],
            )
            dash.add_dashboard_variable(
                name="Hostname",
                query=rf'label_values(http_server_request_duration_count{{service_name="{service}", {DeploymentEnv.PROD}}}, host_name)',
                multi_select=True,
                include_all=True,
                data_source=DataSources.MIMIR,
            )
        else:
            dash = DashboardBuilder(
                title=f"{service} | {env} | Service Dashboard",
                tags=[service, env, "DAC"],
                env=env,
                service=service,
                sections=[
                    ServiceSummarySection(
                        title="Service Summary",
                        service_name=service,
                        env=DeploymentEnv.NONPROD,
                    ),
                    EndpointsSection(
                        title="Endpoints",
                        service_name=service,
                        env=DeploymentEnv.NONPROD,
                    ),
                    InfrastructureMetricsSection(title="Host Metrics"),
                    RuntimeMetricsSection(
                        title="Runtime Metrics",
                        service_name=service,
                        env=DeploymentEnv.NONPROD,
                    ),
                    TracesSection(
                        title="Traces",
                        service_name=service,
                        env=DeploymentEnv.TEMPO_NONPROD,
                    ),
                    LogsSection(
                        title="Logs", service_name=service, env=DeploymentEnv.NONPROD
                    ),
                ],
            )
            dash.add_dashboard_variable(
                name="Hostname",
                query=rf'label_values(http_server_request_duration_count{{service_name="{service}", {DeploymentEnv.NONPROD}}}, host_name)',
                multi_select=True,
                include_all=True,
                data_source=DataSources.MIMIR,
            )

        try:
            dash.build_and_deploy(folder_id=129)
        except (EnvironmentError, HTTPError, ValueError) as e:
            print(f"Failed to deploy {service} | {env} dashboard.\n{e}")

print("All service dashboards deployed successfully.")
print("-" * 80)

# Deploy Canada Branch Network Monitoring Dashboard
network_dash = DashboardBuilder(
    title="Canada Branch Network Monitoring",
    tags=["snmp", "canada", "DAC"],
    service="snmp-monitoring",
    env="production",
    sections=[
        NetworkDashboardHeatmapSection(title="Network Monitoring Heatmaps"),
        NetworkDashboardHistogramSection(title="Ping Statistics Histograms"),
    ]
)

try:
    print("Deploying Canada Branch Network Monitoring dashboard...")
    network_dash.build_and_deploy()
except (EnvironmentError, HTTPError, ValueError) as e:
    print(f"Failed to deploy Canada Branch Network Monitoring dashboard.\n{e}")
print("Canada Branch Network Monitoring dashboard deployed successfully.")
print("-" * 80)
