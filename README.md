# Grafana Dashboards As Code (DAC) Implementation

This module utilizes the [Grafana Foundations SDK](https://github.com/grafana/grafana-foundation-sdk/tree/next%2Bcog-v0.0.x) to
create dashboards using Python. This allows us to easily create and manage all dashboards in one place.

## Folder Structure:
```
automated_dashboards/
│
├── common/
│   └── common.py
│
├── dashboards/
│   └── all_dashboards.py
│
├── helpers/
│   └── default_dashboard.py
│
└── dashboard_builder.py
```

## How it works:
Dashboards are composed of logical sections. Each section can be composed of one Row and one or more Panels. Each panel can have one or more 
queries associated with each panel.

## Creating A Dashboard From The Default Settings
We have a `Service Dashboard Template` inside of `helpers` that creates the default dashboard. To 
create one, you can do the following. Below is an example of a production service dashboard.
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
    dash.build()
    dash.deploy_to_grafana(folder=129) # DAC Service Dashboards folder ID
    print(f"{service} | {env} dashboard deployed successfully.")
except EnvironmentError as e:
    print(f"Failed to deploy {service} dashboard: {e}")
```
You can add custom panels to a section. In this example we're going to add a TimeSeries panel with a Mimir (Prometheus) query
to the `LogsSection` imported from `helpers/default_dashboard.py`
```python
from automated_dashboards.dashboard_builder import DashboardPanel
from automated_dashboards.commom.common import DataSources
from automated_dashboards.dashboard_builder import DashboardBuilder
from automated_dashboards.helpers.default_dashboard import LogsSection
from grafana_foundation_sdk.builders.prometheus import Dataquery as PrometheusQuery
from grafana_foundation_sdk.builders.timeseries import Panel as TimeseriesPanel

LogsSection.add_component(
    DashboardPanel(
        title="New Panel",
        datasource=DataSources.MIMIR,
        queries=[
            Query(
                query_type=PrometheusQuery,
                expr=f"""sum(increase(http_server_request_duration_count{{service_name="my_service"}}[5m]))""",
                datasource=DataSources.MIMIR,
            )
        ],
        panel_type=TimeseriesPanel,
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

dash.build()
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
This module will check for dashboard variables in queries and ensure that varaible is defined. If it is not a `ValueError` will be thrown.
