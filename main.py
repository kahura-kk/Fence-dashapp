"""
This app creates a simple sidebar layout using inline style arguments and the
dbc.Nav component.

dcc.Location is used to track the current location, and a callback uses the
current location to render the appropriate page content. The active prop of
each NavLink is set automatically according to the current pathname. To use
this feature you must install dash-bootstrap-components >= 0.11.0.

For more details on building multi-page Dash applications, check out the Dash
documentation: https://dash.plot.ly/urls
"""
import dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import dash_enterprise_auth as auth
import dash_daq as daq
import random
from influxdb import InfluxDBClient
import pandas as pd
import plotly
import plotly.graph_objs as go

db_client = InfluxDBClient(host='127.0.0.1', port="8086")

db_client.switch_database('fence_dekut')

result = db_client.query('select last("voltage") from "fence_dekut"')
voltage = list(result.get_points())[0]['last']

result = db_client.query('select last("current") from "fence_dekut"')
current = list(result.get_points())[0]['last']

app = dash.Dash(external_stylesheets=[dbc.themes.BOOTSTRAP],
                meta_tags=[
                    {"name": "viewport", "content": "width=device-width, initial-scale=1"}])

# the style arguments for the sidebar. We use position:fixed and a fixed width
SIDEBAR_STYLE = {
    "position": "fixed",
    "top": 0,
    "left": 0,
    "bottom": 0,
    "width": "16rem",
    "padding": "2rem 1rem",
    "background-color": "#f8f9fa",
}

# the styles for the main content position it to the right of the sidebar and
# add some padding.
CONTENT_STYLE = {
    "margin-right": "18rem",
    "margin-right": "2rem",
    "padding": "2rem 1rem",
}

navbar = dbc.NavbarSimple(
    children=[
        dbc.NavItem(dbc.NavLink("Home", href="/")),
        dbc.NavItem(dbc.NavLink("Dashboard", href="/page-1"))

    ],
    brand="Fence app",
    brand_href="#",
    color="green",
    dark=True,
)
gauge1 = html.Div([
    daq.Gauge(
        id='my-gauge',
        label="VOLTAGE",
        value=voltage,
        units="kV",
        showCurrentValue=True,
        color={"gradient": True, "ranges": {"red": [0, 4], "yellow": [4, 6], "green": [6, 10], }}
    ),
])

gauge2 = html.Div([
    daq.Gauge(
        id='my-gauge1',
        label="CURRENT",
        min=0,
        max=50,
        value=current,
        units="A",
        showCurrentValue=True,
        color={"gradient": True, "ranges": {"green": [0, 4], "yellow": [4, 10], "red": [10, 50], }}

    ),
])



graph1 = dcc.Graph(id='graph1', animate=True)

dashb =html.Div ([
    dbc.Container([
        dbc.Row([
            dbc.Col([gauge1], xs=12, sm=12, md=12, lg=5, xl=5),
            dbc.Col([gauge2], xs=12, sm=12, md=12, lg=5, xl=5, )  # style={'backgroundColor':'white'}
        ]),

        dbc.Row([
            dbc.Col([
                html.P('Select parameter'),
                dcc.Checklist(id='check1', value=['volt'],
                              options=[{'label': 'volt', 'value': 'volt'},
                                       {'label': 'current', 'value': 'current'}],
                              labelClassName='mr-4')
            ]),
            # dbc.Col([graph1],xs=12,sm=12,md=12)
        ]),

    ], fluid=True, style={'backgroundColor': '#ebe7eb'}),
    graph1])

content = html.Div(id="page-content")

app.layout = html.Div([dcc.Location(id="url"), navbar, content,
                       dcc.Interval(
                           id='interval_comp',
                           interval=4000,
                           n_intervals=0)
                       ])


@app.callback(Output('my-gauge', 'value'), Input('interval_comp', 'n_intervals'))
def update_voltage(n):
    result = db_client.query('select last("voltage") from "fence_dekut"')
    voltage = list(result.get_points())[0]['last']
    print(voltage)
    return voltage


@app.callback(Output('my-gauge1', 'value'), Input('interval_comp', 'n_intervals'))
def update_current(n):
    result = db_client.query('select last("current") from "fence_dekut"')
    current = list(result.get_points())[0]['last']
    print(current)
    return current


@app.callback(Output('graph1', 'figure'), Input('interval_comp', 'n_intervals'), Input('check1', 'value'))
def update_graph(n, check):
    print(check)
    result = db_client.query('select * from "fence_dekut" where time > now() - 1h')
    result_list = list(result.get_points())
    # turn to pandas dataframe
    df = pd.DataFrame(result_list)
    # make time a datetime object
    df[['time']] = df[['time']].apply(pd.to_datetime)
    if check[0] == 'volt':
        data = plotly.graph_objs.Scatter(
            x=df['time'],
            y=df['voltage'],
            name='Scatter',
            mode='lines+markers'
        )
        X = df['time']
        Y = df['voltage']
        titley = 'Voltage(kV)'

    elif check[0] == 'current':
        data = plotly.graph_objs.Scatter(
            x=df['time'],
            y=df['current'],
            name='Scatter',
            mode='lines+markers'
        )
        X = df['time']
        Y = df['current']
        titley = 'Current(A)'

    return {'data': [data],
            'layout': go.Layout(xaxis=dict(range=[min(X), max(X)], title='time'),
                                yaxis=dict(range=[min(Y), max(Y)], title=titley))}


@app.callback(Output("page-content", "children"), [Input("url", "pathname")])
def render_page_content(pathname):
    if pathname == "/":
        return (html.P("home page "))
    elif pathname == "/page-1":
        return dashb
    # If the user tries to reach a different page, return a 404 message
    else:
        return dbc.Jumbotron(
            [
                html.H1("404: Not found", className="text-danger"),
                html.Hr(),
                html.P(f"The pathname {pathname} was not recognised..."),
            ]
        )


if __name__ == "__main__":
    app.run_server()