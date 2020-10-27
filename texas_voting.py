import dash
from dash.dependencies import Input,Output
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# preload all the data so we're not constantly reloading it
full_data = pd.read_excel('texas_data.xlsx', None)
days = range(4,27) # edit this to add a new day

# fix the column names
for sheet in full_data.keys():
    better_cols = ['county', 'registered_voters', 'num_in_person_voters', 
                   'cuml_in_person_voters', 'cuml_percent_in_person', 
                   'cuml_by_mail_voters', 'cuml_all_voters', 
                   'cuml_percent_early_voting', 'trash'] 
    
    full_data[sheet].columns = better_cols
    full_data[sheet].index = full_data[sheet].county

def make_data(county):

    # get the days, in order of course. :)
    sheets = []
    for day in days:
        sheets.append('Oct-' + str(day))
        
    data = []
    for sheet in sheets:
    
        # grab the data for this day
        temp = full_data[sheet]
        
        c_info = temp.where(temp.county == county).dropna()
        
        info = {
            'date': sheet,
            'cuml_by_mail_voters': c_info['cuml_by_mail_voters'].item(),
            'cuml_in_person_voters': c_info['cuml_in_person_voters'].item(),
            'new_inperson_voters': c_info['num_in_person_voters'].item(),
            'registered_voters'  : c_info['registered_voters'].item(),
            'total_voters'       : c_info['cuml_all_voters'].item(),
        }
        
        data.append(info)
        
    # make into a pretty frame
    data = pd.DataFrame(data)

    return data

def travis_pie_chart(county = 'TRAVIS'):
    # for the last day, what's the breakdown of in person versus mail in?
    
    # again, I know I can do this better, leave me alone
    data = make_data(county)
    
    # grab the final day for travis
    last_day = data.iloc[-1]
    
    # grab the right numbers
    by_mail = last_day['cuml_by_mail_voters']
    in_person = last_day['cuml_in_person_voters']
    havent_voted = last_day['registered_voters'] - last_day['total_voters']
    
    labels = ['By Mail', 'In Person', "Haven't Voted"]
    values = [by_mail, in_person, havent_voted]
    colors = ['07689f', '40a8c4', '#ccc']
    
    pie = go.Pie(labels = labels, values = values, marker = {'colors': colors})
    layout = {
        'title': 'What kinds of votes has %s County cast?' % county.title(),
        'width': 800
    }
    
    
    fig = go.Figure(data=[pie], layout=layout)
    
    return fig



def make_multi_county_plot(counties = ['HAYS', 'BEXAR', 'TRAVIS']):
    """Builds a line chart comparing the voters per # of reg voters between
    the given list of counties"""

    lines = []
    widths = [3,3,4]
    colors = ["#a6cee3","#1f78b4","#b2df8a"]
    #colors = ["#a6cee3","#1f78b4","#a2e46c"]
    for county, width, color in zip(counties, widths, colors):
        
        # get the data
        data = make_data(county)
        
        # make a line for the data
        x = data['date']
        y = data['total_voters']/data['registered_voters'] * 100
        line = go.Scatter(x = x, y = y, 
                          name = county,
                          mode = 'lines',
                          line = {'width': width, 'color': color})
        lines.append(line)

    # create a layout
    layout = {
        'title': 'Percentage of Registered Texas Voters Who\'ve Already Voted',
        'yaxis_title': '% of Registered Voters',
        'yaxis': {
            'range': [0,70],
            'linecolor': '#aaa',
            'linewidth': 1,
            'showgrid': True,
            'gridcolor': '#ccc',
            'zeroline': True,
            'showline': True,
        },
        'xaxis': {
            'linecolor': '#aaa',
            'linewidth': 1,
            'zeroline': True,
            'showline': True,
        },
        'plot_bgcolor': 'white',
        'width': 800,
    }

    # put it all together in a nice Figure
    fig = go.Figure(lines, layout)
    return fig





def make_county_options():
    """Quick helper function to make the Dash-friendly list of counties"""
    
    # get the list of counties
    counties = list(full_data['Oct-4']['county'])
    
    # dash-ify
    options = []
    for county in counties:
        option = {'label': county, 'value': county}
        options.append(option)
        
    return options


app = dash.Dash(__name__, external_stylesheets = ['https://cdn.jsdelivr.net/npm/bootstrap@4.5.3/dist/css/bootstrap.min.css'])


app.layout = html.Div([
    html.H1("Hello World!"),
    html.P(["""
        These plots are a quick look into how certain Texas Counties have been voting.
        Data is collected from """, 
        html.A(href="https://earlyvoting.texas-election.com/Elections/getElectionEVDates.do", 
               children="The Texas Secretary of State Website."),
        " This is not meant to be an all encompassing dashboard; just a few plots I'm making for friends."
    ]),
    dcc.Graph(
        id = 'multi-county-plot',
        figure = make_multi_county_plot(),
        style= {'width':800}
    ),
    
    dcc.Dropdown(id = 'choose_county',
                 options = make_county_options(),
                 value = 'TRAVIS'),
    
    dcc.Graph(
        id="travis_pie",
        figure = travis_pie_chart(),
        style= {'width':800}
    ),
], className="container")


@app.callback(
    Output('travis_pie', 'figure'),
    [Input('choose_county', 'value')]
)
def update_pie(county):
    return travis_pie_chart(county)


if __name__ == "__main__":

    app.run_server(debug = False)