from automated_dashboards.common.common import DataSources, DeploymentEnv
from automated_dashboards.dashboard_builder import DashboardBuilder
from automated_dashboards.helpers.default_dashboard import (
    ServiceSummarySection,
    EndpointsSection,
    InfrastructureMetricsSection,
    RuntimeMetricsSection,
    TracesSection,
    LogsSection
)
services = ["creo", "webanalytics", "SummitApi", "affiliateleads", "Cashmoney", "lenddirect", "hotelcardifornia",
             "tiger-authentication", "voltaire"]
envs = ["prod", "nonprod"]

for service in services:
    for env in envs:
        if env == "prod":
            dash = DashboardBuilder(
                title=f"{service} | {env} | Service Dashboard",
                tags=[service, env, "DAC"],
                env=env,
                service=service,
                sections=[
                    ServiceSummarySection(title="Service Summary", service_name=service, env=DeploymentEnv.PROD),
                    EndpointsSection(title="Endpoints", service_name=service, env=DeploymentEnv.PROD),
                    InfrastructureMetricsSection(title="Host Metrics"),
                    RuntimeMetricsSection(title="Runtime Metrics", service_name=service, env=DeploymentEnv.PROD),
                    TracesSection(title="Traces", service_name=service, env=DeploymentEnv.TEMPO_PROD),
                    LogsSection(title="Logs", service_name=service, env=DeploymentEnv.PROD)
                ],
            )
            dash.add_dashboard_variable(
                name="Hostname",
                query=rf'label_values(http_server_request_duration_count{{service_name="{service}", {DeploymentEnv.PROD}}}, host_name)',
                multi_select=True,
                include_all=True,
                data_source=DataSources.MIMIR
            )
        else:
            dash = DashboardBuilder(
                title=f"{service} | {env} | Service Dashboard",
                tags=[service, env, "DAC"],
                env=env,
                service=service,
                sections=[
                    ServiceSummarySection(title="Service Summary", service_name=service, env=DeploymentEnv.NONPROD),
                    EndpointsSection(title="Endpoints", service_name=service, env=DeploymentEnv.NONPROD),
                    InfrastructureMetricsSection(title="Host Metrics"),
                    RuntimeMetricsSection(title="Runtime Metrics", service_name=service, env=DeploymentEnv.NONPROD),
                    TracesSection(title="Traces", service_name=service, env=DeploymentEnv.TEMPO_NONPROD),
                    LogsSection(title="Logs", service_name=service, env=DeploymentEnv.NONPROD)
                ],
            )
            dash.add_dashboard_variable(
                name="Hostname",
                query=rf'label_values(http_server_request_duration_count{{service_name="{service}", {DeploymentEnv.NONPROD}}}, host_name)',
                multi_select=True,
                include_all=True,
                data_source=DataSources.MIMIR
            )

        try:
            dash.build()
            dash.deploy_to_grafana(folder=129) # DAC Service Dashboards folder ID
            print(f"{service} | {env} dashboard deployed successfully.")
        except EnvironmentError as e:
            print(f"Failed to deploy Creo dashboard: {e}")
