import pandas as pd
from code.FootballScraper import FootballDataScraper

fds = FootballDataScraper()
fds.get_match_links()
fds.extract_game_pages()
fds.get_match_data(from_file=True)
fds.get_commentary_data()

# Analysis
df_matches = pd.DataFrame.from_dict(fds.matches)
df_team_details = pd.DataFrame.from_dict(fds.team_details).T
df_player_details = pd.DataFrame.from_dict(fds.player_details).T
df_player_stats = pd.DataFrame.from_dict(fds.player_stats)

# Format columns
df_matches = df_matches[(df_matches.attendance.notnull())].astype({'attendance':'int'})
df_player_stats = df_player_stats[(df_player_stats.totalGoals.notnull())].astype({'totalGoals':'int', 'yellowCards': 'int'})


# Venue, Avg Attendance
df_avg_att = pd.Series.to_frame(df_matches.groupby(['venue','home_side_id'])['attendance'].mean())
df_avg_att['attendance'] = df_avg_att['attendance'].apply(lambda term: int(term))
df_avg_att = df_avg_att.sort_values('attendance', ascending=False)
df_avg_att = df_avg_att.reset_index()
df_avg_att = pd.merge(df_avg_att, df_team_details[['id','long_name']], left_on='home_side_id', right_on='id', how='left')
df_avg_att = df_avg_att.rename(columns={"long_name": "home_team"})
df_avg_att = df_avg_att.drop(columns=['id', 'home_side_id'])
df_avg_att.index += 1
print('\nTop 5 Venues by Avg Attendance:')
print('===============================')
print(df_avg_att.head(5),'\n')

# Top goal scorers 
df_top_scorer = pd.Series.to_frame(df_player_stats.groupby(['id'])['totalGoals'].sum())
df_top_scorer = df_top_scorer.sort_values('totalGoals', ascending=False)
df_top_scorer = pd.merge(df_top_scorer, df_player_details[['id','player_name', 'team_id']], on='id', how='left')
df_top_scorer = pd.merge(df_top_scorer, df_team_details[['id','long_name']], left_on='team_id', right_on='id', how='left')[['player_name', 'long_name', 'totalGoals']]
df_top_scorer.index += 1
df_top_scorer = df_top_scorer.rename(columns={"long_name": "team"})
print('\nTop 5 Goal Scorers:')
print('===================')
print(df_top_scorer.head(5),'\n')

# Most Yellow Cards By Player 
df_most_yellow = pd.Series.to_frame(df_player_stats.groupby(['id'])['yellowCards'].sum())
df_most_yellow = df_most_yellow.sort_values('yellowCards', ascending=False)
df_most_yellow = pd.merge(df_most_yellow, df_player_details[['id','player_name', 'team_id']], on='id', how='left')
df_most_yellow = pd.merge(df_most_yellow, df_team_details[['id','long_name']], left_on='team_id', right_on='id', how='left')[['player_name', 'long_name', 'yellowCards']]
df_most_yellow.index += 1
df_most_yellow = df_most_yellow.rename(columns={"long_name": "team"})
print('\n5 Most Yellow Cards By Player:')
print('==============================')
print(df_most_yellow.head(5),'\n')

df_most_yellow = pd.Series.to_frame(df_most_yellow.groupby(['team'])['yellowCards'].sum())
df_most_yellow = df_most_yellow.reset_index()
df_most_yellow = df_most_yellow.sort_values('yellowCards', ascending=False)
df_most_yellow = df_most_yellow.reset_index().drop(columns=['index'])
df_most_yellow.index += 1
print('\n5 Most Yellow Cards By Team:')
print('============================')
print(df_most_yellow.head(10),'\n')