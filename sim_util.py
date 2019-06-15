'''
    Util method to plot statistics
'''

import plotly
import plotly.graph_objs as go

def states_figure(data):
    '''
        Returns ploty figure to draw state_log
    '''
    figure =  {'data':  [ {"x":data['time'], "y":data['state_num'],'name':'States'}],
          'layout': {
            'xaxis': {'title': 'time'},
            'yaxis': {'title': 'customers'}
            }         
        }
    return figure

def arr_dep_figure(arrive, depart):
    figure = {'data':  [
            {"x":arrive['time'], "y": arrive['state_num'], 'name':'Arrive'},
            {"x":depart['time'], "y": depart['state_num'],'name':'Depart'},
            ],
          'layout': {
            'xaxis': {'title': 'time'},
            'yaxis': {'title': 'customers'}
            }
         }
    return figure

def states_hist(data):
    data = [go.Histogram(x=data, histnorm='probability' ) ]
    return data