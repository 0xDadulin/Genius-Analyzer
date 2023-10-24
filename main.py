import json
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objs as go
from collections import Counter, defaultdict

# Link to Tailwind CSS CDN
external_stylesheets = [
    'https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css'
]

# Load the database
with open('rap_database.json', 'r', encoding='utf-8') as file:
    database = json.load(file)

# Process the data
for artist_name, data in database.items():
    artist_word_frequency = defaultdict(int)

    # Convert word frequency list to dictionary if it's a list
    for song_data in data.values():
        if isinstance(song_data['word_frequency'], list):
            song_data['word_frequency'] = dict(song_data['word_frequency'])

        for word, freq in song_data['word_frequency'].items():
            artist_word_frequency[word] += freq

    database[artist_name]['artist_word_frequency'] = dict(artist_word_frequency)

# Collect all words and their frequency
all_words = defaultdict(lambda: defaultdict(int))
for artist, details in database.items():
    for word, freq in details['artist_word_frequency'].items():
        all_words[word][artist] += freq

database['Wszyscy artyści'] = dict(all_words)

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

# Layout of the app
app.layout = html.Div(children=[
    html.Div(children=[
        html.Label('Wybierz artystę:', className='block text-lg font-semibold mb-2 text-white'),
        dcc.Dropdown(
            id='artist-selection',
            options=[{'label': artist, 'value': artist} for artist in database.keys()],
            value='Wszyscy artyści',
            className='mb-4 border border-yellow-400 rounded shadow p-2'
        )
    ]),

    html.Label('Wpisz słowo do wyszukania:', className='block text-lg font-semibold mb-2 text-white'),
    dcc.Input(
        id='search-field',
        type='text',
        value='Polska',
        placeholder='Wyszukaj słowo...',
        className='p-2 bg-black text-white border border-yellow-400 rounded shadow mb-4'
    ),

    dcc.Graph(id='bar-chart', className='shadow-lg'),

    html.Div(id='statistics', children=[], className='mt-4 text-lg text-white')

], className='p-8 bg-black')


# Callbacks
@app.callback(
    Output('search-field', 'style'),
    [Input('artist-selection', 'value')]
)
def toggle_search_bar(artist_selection):
    """Hide the search bar when a specific artist is selected."""
    if artist_selection == 'Wszyscy artyści':
        return {'display': 'block'}
    else:
        return {'display': 'none'}


@app.callback(
  Output('bar-chart', 'figure'),
  [Input('artist-selection', 'value'),
   Input('search-field', 'value')]
)
def update_figure(artist_selection, search_term):
  """Update the bar chart based on artist selection and search term."""
  search_term = search_term.lower() if search_term else 'ja'

  if artist_selection == 'Wszyscy artyści':
      chart_data = {artist: data['artist_word_frequency'].get(search_term, 0) / (len(data) - 1) for artist, data in database.items() if 'artist_word_frequency' in data}
  else:
      total_songs = len(database[artist_selection]) - 1
      chart_data = {word: freq / total_songs for word, freq in database[artist_selection]['artist_word_frequency'].items()}

  # Display top 30 words
  chart_data = dict(Counter(chart_data).most_common(30))
  figure = go.Figure(data=[go.Bar(x=list(chart_data.keys()), y=list(chart_data.values()))])

  figure.update_layout(
      margin=dict(t=10, b=10, l=10, r=10),
      xaxis_title="Artysta" if artist_selection == 'Wszyscy artyści' else "Słowo",
      yaxis_title="Średnia ilość wystąpień słowa na utwór"
  )

  return figure



@app.callback(
  Output('statistics', 'children'),
  [Input('artist-selection', 'value')]
)
def update_stats(artist_selection):
  """Display statistics for the selected artist."""
  if artist_selection == 'Wszyscy artyści':
      return ""

  word_lengths = [len(word) for word in database[artist_selection]['artist_word_frequency'].keys()]
  average_word_length = sum(word_lengths) / len(word_lengths)

  unique_words_per_song = {song: len(set(song_data['lyrics'].split())) for song, song_data in database[artist_selection].items() if song != 'artist_word_frequency'}
  average_unique_words_per_song = sum(unique_words_per_song.values()) / len(unique_words_per_song)

  unique_word_count = len(database[artist_selection]['artist_word_frequency'])
  total_word_count = sum(database[artist_selection]['artist_word_frequency'].values())
  total_song_count = len(database[artist_selection].keys()) - 1
  average_words_per_song = total_word_count / total_song_count

  stats_content = [
      html.Div(f'Suma wszystkich słów: {total_word_count}', className='p-2'),
      html.Div(f'Unikalne słowa: {unique_word_count}', className='p-2'),
      html.Div(f'Suma utworów artysty: {total_song_count}', className='p-2'),
      html.Div(f'Średnia liczba słów na utwór: {average_words_per_song:.2f}', className='p-2'),
      html.Div(f'Średnia długość słowa: {average_word_length:.2f} liter', className='p-2'),
      html.Div(f'Średnia liczba unikalnych słów na utwór: {average_unique_words_per_song:.2f}', className='p-2')
  ]

  return html.Div(stats_content, className='grid grid-cols-2 gap-4')

if __name__ == '__main__':
    app.run_server(debug=False, port=8000, host='0.0.0.0')