import simpy
import random
import pandas as pd
import csv
import dash
from flask import Flask
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go
import pandas as pd
import os
import pickle
import copy
import datetime as dt
import math
from flask_caching import Cache
import time

import requests
first = 1
# COUNTERS
counter_balk = 0
counter_arrive = 0
counter_served = 0
counter_in_system = 0
states_map = dict()

collect_serv_time = list()
collect_arrival_time = list()
collect_in_system = list()
collect_wait_time = list()


'''
CACHE_CONFIG = {
    # try 'filesystem' if you don't want to setup redis
    'CACHE_TYPE': 'filesystem',
    'CACHE_DIR': 'cache-directory',
    #'CACHE_REDIS_URL': os.environ.get('REDIS_URL', 'localhost:6379')
}
cache = Cache()
cache.init_app(app.server, config=CACHE_CONFIG)
'''
def source(env, _lambda, _mu, _alpha):
    i = 0
    while True:
        i += 1
        name = 'customer' + str(i)
        c = customer(env, _mu, _alpha, name)
        env.process(c)  # add process to go
        arrive_time = random.expovariate(_lambda)
        collect_arrival_time.append(arrive_time)
        yield env.timeout(arrive_time)


def customer(env, _mu, _alpha, name):
    '''
    Customer arrives, waits for service or goes away
    '''
    global counter_served, counter_arrive, counter_balk, counter_in_system, state_log, arrive_log, depart_log
    arrive = env.now
    # вести лог чуваков в датафрейме
    if random.random() > _alpha:
        #print('%7.4f %s: Here I balked' % (arrive, name))
        counter_balk += 1
        return
    else:
        counter_arrive += 1
        counter_in_system += 1
        state_log = state_log.append({'time': env.now, 'state_num': counter_in_system}, ignore_index=True)
        arrive_log = arrive_log.append({'time': env.now, 'state_num': counter_arrive}, ignore_index=True)
        #print('%7.4f %s: Here I arrived' % (arrive, name))

    with serv.request() as req:

        yield req  # wait
        wait = env.now - arrive
        collect_wait_time.append(wait)
        #print('%7.4f: %s Waited for %6.3f. Start service' % (env.now, name, wait))
        serve_time = random.expovariate(_mu)
        collect_serv_time.append(serve_time)
        #print('%7.4f: %s Service time is %6.3f. Start service' % (env.now, name, serve_time))
        # serve_time = 30
        yield env.timeout(serve_time)

        counter_served += 1
        counter_in_system -= 1
        state_log = state_log.append({'time': env.now, 'state_num': counter_in_system}, ignore_index=True)
        depart_log = depart_log.append({'time': env.now, 'state_num': counter_served}, ignore_index=True)
        #print('%7.4f %s: Finished' % (env.now, name))

#@cache.memoize()
def simulate(_lambda, _mu, _alpha, until=50):
    global counter_served, counter_arrive, counter_balk, counter_in_system, state_log, arrive_log, depart_log, collect_in_system

    c = ['time', 'state_num']
    state_log = pd.DataFrame(columns=c)
    arrive_log = pd.DataFrame(columns=c)
    depart_log = pd.DataFrame(columns=c)
    #print(until, customers)
    run(_lambda, _mu, _alpha, until)

    stat = {
        'state_log': state_log,
        'arrive_log': arrive_log,
        'depart_log': depart_log,
        'served_num': counter_served,
        'arrived_num': counter_arrive,
        'balked_num': counter_balk,
        'mean_wait_time': sum(collect_wait_time) / len(collect_wait_time),
        'mean_serv_time': sum(collect_serv_time) / len(collect_serv_time),
        'mean_arrive_time': sum(collect_arrival_time) / len(collect_arrival_time)
    }

    print("Counter away {}".format(counter_balk))
    print("Counter arrive {}".format(counter_arrive))
    print("Counter counter_served {}".format(counter_served))
    print("Counter counter_in_system {}".format(counter_in_system))
    print('Serve mean time is {}'.format(sum(collect_serv_time) / len(collect_serv_time)))
    print('Arrive mean time is {}'.format(sum(collect_arrival_time) / len(collect_arrival_time)))
    print('Wait mean time is {}'.format(sum(collect_wait_time) / len(collect_wait_time)))
    # print(state_log)
    # print(arrive_log)
    # print(depart_log)
    #print(len(collect_wait_time))
    global states_map
    states_map = stat
    #return stat

def run(_lambda, _mu, _alpha, until):
    global env, serv
    global counter_served, counter_arrive, counter_balk, counter_in_system, state_log, arrive_log,\
        depart_log, collect_in_system, collect_serv_time, collect_arrival_time, collect_wait_time
    counter_balk = 0
    counter_arrive = 0
    counter_served = 0
    counter_in_system = 0

    collect_serv_time = list()
    collect_arrival_time = list()
    collect_in_system = list()
    collect_wait_time = list()

    env = simpy.Environment()
    serv = simpy.Resource(env, capacity=1)
    env.process(source(env, _lambda, _mu, _alpha))
    env.run(until=until)

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

colors = {
    'background': '#111111',
    'text': '#7FDBFF'
}

app.layout = html.Div(style={'backgroundColor': colors['background'], }, children=[
    html.H1(id = 'header',
        children='Stochastic lab',
        style={
            'textAlign': 'center',
            'color': colors['text']
        }
    ),

    html.Div(children='Model N4: M|M|1 with balking', style={
        'textAlign': 'center',
        'color': colors['text']
    }),
    html.Div([
        html.H3('Customers in queue',
        style={
            'textAlign': 'left',
            'color': colors['text'],
            'marginLeft': 10
        }),
        dcc.Graph(
            id='states_logs'
        )]),
    html.Div([
        html.Div([
            html.H3('Served/Balked',
            style={
            'textAlign': 'left',
            'color': colors['text'],
            'marginLeft': 10
            }),
            dcc.Graph(
                id='pie-graph'
            )
        ], className="six columns"),
        html.Div(
                 [
                     html.Table(id = 'table', style={'color': colors['text'], 'marginTop': 50}),
                    html.Div([
                            html.Div([
                                        dcc.Input(
                                            id='lambda',
                                            placeholder='Enter a lambda...',
                                            type='text',
                                            value='3'
                                        ),
                                        dcc.Input(
                                            id='mu',
                                            placeholder='Enter a mu...',
                                            type='text',
                                            value='1'
                                        ),
                                        dcc.Input(
                                            id='alpha',
                                            placeholder='Enter a alpha...',
                                            type='text',
                                            value='0.7'
                                        )
                                  ]),
                            html.Div([
                                    dcc.Input(
                                        id='time_limit',
                                        placeholder='Enter a time limit...',
                                        type='text',
                                        value='500'
                                    ),
                                    html.Button('Update', id='button', style={'color': colors['text']}),
                                    html.H6('', id='hello_there')
                                    ], style={'marginTop': 5})
                            ], style={'marginTop': 50})
                ], className="six columns")
    ], className="row"),
    html.Div(id='signal', style={'display': 'none', 'backgroundColor': colors['background']})

])
#mapbox_access_token = 'pk.eyJ1IjoiamFja2x1byIsImEiOiJjajNlcnh3MzEwMHZtMzNueGw3NWw5ZXF5In0.fk8k06T96Ml9CLGgKmk81w'
@app.callback(Output('table','children'),
              [Input('button', 'n_clicks')],
              [State('lambda', 'value'),
               State('mu', 'value'),
               State('alpha', 'value'),
               State('time_limit', 'value')])
def update_table(n_clicks, lambda_, mu, alpha, time_limit):
    simulate(float(lambda_), float(mu), float(alpha), until=int(time_limit))
    global states_map
    arrived = states_map['arrived_num']
    served = states_map['served_num']
    balked = states_map['balked_num']
    serve_mean_time = states_map['mean_serv_time']
    arrive_mean_time = states_map['mean_arrive_time']
    wait_mean_time = states_map['mean_wait_time']
    return [html.Tr([html.Td('Arrived'), html.Td(served + balked)]),
            html.Tr([html.Td('Served'), html.Td(served)]),
            html.Tr([html.Td('Away'), html.Td(balked)]),
            html.Tr([html.Td('Serve mean time'), html.Td(serve_mean_time)]),
            html.Tr([html.Td('Arrive mean time'), html.Td(arrive_mean_time)]),
            html.Tr([html.Td('Wait mean time'), html.Td(wait_mean_time)])]

@app.callback(Output('pie-graph','figure'),
              [Input('button', 'n_clicks')])
def update_pie_graph(n_clicks):
    time.sleep(5)
    global states_map
    served = states_map['served_num']
    balked = states_map['balked_num']
    figure = {
        'data': [
            {
                'labels': ['Served', 'Balked'],
                'values': [served, balked],
                'hoverinfo': "label+value+percent",
                'textinfo': "label+percent",
                'type': 'pie',
            },
        ],
        'layout': {
            'plot_bgcolor': colors['background'],
            'paper_bgcolor': colors['background'],
            'margin': {
                'l': 50,
                'r': 50,
                'b': 50,
                't': 50
            },
            'legend': {'x': 1, 'y': 0}
        }}
    return figure

@app.callback(Output('states_logs','figure'),
              [Input('button', 'n_clicks')])
def update_logs_graph(n_clicks):
    time.sleep(5)
    global states_map
    states_logs = states_map['state_log']
    print(states_logs)
    figure = {
        'data': [
            {'x': states_logs['time'], 'y': states_logs['state_num'], 'type': 'line', 'name': 'SF'},
        ],
        'layout': {
            'plot_bgcolor': colors['background'],
            'paper_bgcolor': colors['background'],
            'font': {
                'color': colors['text']
            }
        }
    }
    return figure

if __name__ == '__main__':
    app.run_server(debug=True)