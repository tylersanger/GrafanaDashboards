# Grafana Dashboards As Code (DAC) Implementation

This module utilizes the [Grafana Foundations SDK](https://github.com/grafana/grafana-foundation-sdk/tree/next%2Bcog-v0.0.x) to
create dashboards using Python. This allows us to easily create and manage all dashboards in one place.

## Folder Structure:
```
automated_dashboards/
│
├── common/ # Common items dashboards can be configured with.
│   
│
├── dashboards/ # Built dashboards reside here
│   
│
├── helpers/ # Default dashboard configurations reside here
│   
│
└── dashboard_builder.py
```

## How it works:
Dashboards are composed of logical sections. Each section can be composed of one Row and one or more Panels. Each panel can have one or more 
queries associated with each panel.

## Creating A Dashboard From The Default Settings
We have a `Service Dashboard Template` inside of `helpers` that creates the default service dashboard. The default dashboard uses
a dashboard variable called `Hostname` to dynamically pull host metrics for each service. To create the default dashboard with the defined
dashboard variable, you can do the following:
```python
# service = your_service
# env = 'prod'
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

try:
    dash.build_and_deploy(folder_id=129) # You can specify a folder ID if known or leave blank and get prompted for it.
    print(f"{service} | {env} dashboard deployed successfully.")
except EnvironmentError as e:
    print(f"Failed to deploy {service} dashboard: {e}")
```
You can add custom panels to a section. In this example we're going to add a TimeSeries panel with a Mimir (Prometheus) query
to the `LogsSection` imported from `helpers/default_dashboard.py`
```python
from automated_dashboards.dashboard_builder import DashboardPanel
from automated_dashboards.commom.common import DataSources, Panels, QueryTypes
from automated_dashboards.dashboard_builder import DashboardBuilder
from automated_dashboards.helpers.default_dashboard import LogsSection

LogsSection.add_component(
    DashboardPanel(
        title="New Panel",
        datasource=DataSources.MIMIR,
        queries=[
            Query(
                query_type=QueryTypes.PROMETHEUS,
                expr=f"""sum(increase(http_server_request_duration_count{{service_name="my_service"}}[5m]))""",
                datasource=DataSources.MIMIR,
            )
        ],
        panel_type=Panels.TIMESERIES,
    )
)

dash = DashboardBuilder(
    title=f"My new logs section dashboard",
    tags=[service, env, "DAC"],
    env=env,
    service=service,
    sections=[
        LogsSection
    ]
)

dash.build_and_deploy()
```
## Adding Dashboard Variables:
Dashboard variables can be used in queries to dynamically change a queries parameters. Dashboard variables are prefixed with a
`$` and must match the variable name exactly. For instance, if you defined a dashboard variable of `Hostname` then to reference
this in a query, you would need to use `$Hostname`. Example of adding a `Hostname` dashboard variable:
```python
dash.add_dashboard_variable(
    name="Hostname",
    query=rf'label_values(http_server_request_duration_count{{service_name="{service}", {DeploymentEnv.PROD}}}, host_name)',
    multi_select=True,
    include_all=True,
    data_source=DataSources.MIMIR
)
```
Example of a Query utilizing the `Hostname` variable defined above:
```python
...
Query(
    query_type=QueryTypes.PROMETHEUS,
    expr=r"""
        system_memory_utilization{host_name=~'$Hostname', state!="free"} * 100
    """,
    datasource=DataSources.MIMIR,
    legend="{{host_name}}",
)
...
```
This module will check for dashboard variables in queries and ensure that varaible is defined. If it is not a `ValueError` will be thrown.