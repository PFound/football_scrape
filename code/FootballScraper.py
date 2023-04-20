# Import required libraries
import requests, os, configparser, json, logging, pytz, glob, re
from bs4 import BeautifulSoup
from datetime import date, timedelta, datetime
from argparse import Namespace

# Import local libraries
from code. progressBar import progress_bar

# Setup and ingest config file and apply to namespace
config = configparser.ConfigParser()
config.read(f'code/footballscraper.config')
config = Namespace(**config['config'])

# Setup Logger for debugging
logging.basicConfig(filename=f'{config.log_fld}fbs.log', filemode='w', format='%(name)s - %(levelname)s - %(asctime)s - %(message)s', level=logging.DEBUG)


def logtofile(func):
    """
    A decorator function that logs the start and end of the execution of the decorated function.
        Args:       func (function): The function to be decorated.
        Returns:    function: The decorated function that logs its execution.
    """
    def log(*args,**kwargs):
        """
        The inner function that adds logging functionality to the decorated function.
        Args:       *args: The positional arguments passed to the decorated function.
                    **kwargs: The keyword arguments passed to the decorated function.
        Returns:    The result of the decorated function.
        """
        logging.info(f'START: {func.__name__}')
        result = func(*args, **kwargs)
        logging.info(f'END: {func.__name__}')
        return result
    return log

class FootballDataScraper():
    """
    A class to scrape football match data from the web and save locally in JSON format. 
    """
    def __init__(self):
        """
        Initializes the FootballScraper class with the given configuration.    
        """
        logging.info('FootballDataScraper initiated')
        self.season_str_dt = datetime.strptime(config.season_start_dt,'%Y-%m-%d')
        self.season_end_dt = datetime.strptime(config.season_end_dt,'%Y-%m-%d')
        self.dates = self._build_season_date_list(self.season_str_dt, self.season_end_dt)
        self.match_links = None
        self.matches = None
        self.team_stats = None
        self.team_details = None
        self.player_details = None
        self.player_stats = None
        self.commentary = None

    @logtofile
    def _build_season_date_list(self, start, end):
        """
        Generates a list of dates for the football season.
        
        Parameters
        ----------
        start : datetime.date
            The start date of the football season.
        end : datetime.date
            The end date of the football season.
            
        Returns
        -------
        list
            A list of dictionaries containing 'strdate', 'date', and 'game_week' keys.
        """
        
        dates = []
        game_week = 0
        while start <= end:
            game_week += 1 if start.weekday() == 0 else 0
            dates.append({'strdate':start.strftime('%Y%m%d'),'date':start.strftime('%Y-%m-%d'), 'game_week':game_week})
            start += timedelta(days=1)
        return dates
    
    @logtofile
    def get_match_links(self, from_file=True):
        """
        Retrieves match links either from a file or by scraping the website.
        
        Parameters
        ----------
        from_file : bool, optional
            If True, reads match links from a file (default is True).
            If False, scrapes match links from the website.
            
        Returns
        -------
        None
            Sets the match_links attribute of the FootballDataScraper object.
        """
        if from_file:
            try:
                logging.info(f'Getting match links from file')
                starttime = datetime.now()
                progress = progress_bar(0, 1, starttime)
                with open(f'{config.data_fld}' + 'match_links.csv', 'r') as f:
                    match_links = f.read().split('\n')
                progress = progress_bar(1, 1, starttime)
                logging.info(f'{progress}')
            except FileNotFoundError:
                err_string = 'Please re run with FootballDataScraper.get_match_links(from_file=False)'
                print(f'ERROR: {err_string}')
                logging.error(err_string)
                match_links = None
        else:
            date_count = len(self.dates)
            start_time = datetime.now()
            match_links = []

            for i, date_str in enumerate(self.dates):
                date_str = date_str['strdate']
                url = (config.base_url + config.url).replace(config.date_placeholder, date_str)
                soup = BeautifulSoup(requests.get(url).content, 'html.parser')

                for l in soup.find_all("a", class_="AnchorLink at"):
                    href = l.get('href')
                    if f'{config.base_url}{href}' not in match_links:
                        match_links.append(f'{config.base_url}{href}')
                        href = href.replace('match','commentary')
                        match_links.append(f'{config.base_url}{href}')

                progress = progress_bar(i+1, date_count, start_time)

            logging.info(f'{progress}')

            # Save match_links to file, to save time in rerunning when needed.
            with open(f'{config.data_fld}' + 'match_links.csv', 'w') as f:
                f.write('\n'.join(match_links))
        self.match_links = match_links

    @logtofile
    def extract_game_pages(self, only_missing_files = True, refresh = False):
        """
        Downloads and saves HTML files of game pages from a list of URLs stored in self.match_links.
        
        Args:
            only_missing_files (bool, optional): If True, only downloads and saves HTML files for URLs
                that don't already exist in the destination folder. Defaults to True.
            refresh (bool, optional): If True, downloads and saves HTML files for all URLs, regardless
                of whether they already exist in the destination folder. Defaults to False.

        Example:
            extract_game_pages(only_missing_files=True, refresh=False)
        """
        link_count = len(self.match_links)
        start_time = datetime.now()

        for i, link in enumerate(self.match_links):
            tag = 'match' if 'match' in link else 'commentary'
            filename = f'{config.games_fld}{tag}_{link[-6:]}.html'

            if only_missing_files and refresh is False:
                if os.path.isfile(filename) == False:
                    response = requests.get(link).text
                    with open(filename, 'w') as f:
                        f.write(response)
            else:
                response = requests.get(link).text
                with open(filename, 'w') as f:
                    f.write(response)

            progress = progress_bar(i+1, link_count, start_time)
        logging.info(f'{progress}')

    def _convert_to_london_time(self, timestamp):
        dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))  # Convert the "Z" to "+00:00" for timezone offset
        london_tz = pytz.timezone("Europe/London")
        dt_london = dt.astimezone(london_tz)

        formatted_time_london = dt_london.strftime("%Y-%m-%d %H:%M")
        return formatted_time_london

    @logtofile
    def get_match_data(self, from_file = True):
        """
        Retrieves match data from either pre-existing JSON files or from HTML files, and stores the data in dictionaries.

        Args:
            from_file (bool, optional): If True, reads existing JSON files to fetch data. If False, reads HTML files to extract data. Default is True.

        This function fetches the following data:
            1. Matches
            2. Team Details
            3. Team Stats
            4. Player Details
            5. Player Stats

        The data is stored in the following dictionaries:
            - self.matches
            - self.player_details
            - self.player_stats
            - self.team_details
            - self.teams_stats

        When from_file is set to False, the function also writes the data to JSON files.
        """ 
        if from_file:
            logging.info(f'Getting match data from file')
            start_time = datetime.now()
            progress = progress_bar(0, 5, start_time)
            with open(f'{config.output_fld}matches.json', 'r') as f:
                self.matches = json.load(f)
            progress = progress_bar(1, 5, start_time)
            with open(f'{config.output_fld}player_details.json', 'r') as f:
                self.player_details = json.load(f)
            progress = progress_bar(2, 5, start_time)
            with open(f'{config.output_fld}player_stats.json', 'r') as f:
                self.player_stats = json.load(f)
            progress = progress_bar(3, 5, start_time)
            with open(f'{config.output_fld}team_details.json', 'r') as f:
                self.team_details = json.load(f)
            progress = progress_bar(4, 5, start_time)
            with open(f'{config.output_fld}team_stats.json', 'r') as f:
                self.team_stats = json.load(f)
            progress = progress_bar(5, 5, start_time)
            logging.info(f'{progress}')
        else:
            match_files = glob.glob(f'{config.games_fld}/match_*.html')
            
            # dictionarys to store data
            matches = []
            team_stats = []
            team_details = {}
            player_details = {}
            player_stats = []

            sides = ['home', 'away']
            match_files_count = len(match_files)
            start_time = datetime.now()

            for i, match_file in enumerate(match_files):
                with open(match_file) as fp:
                    match = {}
                    team = {}
                    player = {}
                    
                    soup = BeautifulSoup(fp, 'html.parser')
                    
                    match_id = 'M' + re.findall('.match_(\d+)\.html', match_file)[0]
                    match['id'] = match_id
                    match['venue'] = soup.find('li',{'class': "venue"}).div.text.replace('VENUE: ','')
                    match['date_time'] = self._convert_to_london_time(soup.find('li', {'class':'subdued'}).div.span.get('data-date'))
                    match['address'] = soup.find('div',{'class': "address"}).span.text
                    if soup.find(string=re.compile('ATTENDANCE')) != None:
                        match['attendance'] = soup.find(string=re.compile('ATTENDANCE')).replace(',','').replace('ATTENDANCE: ','')
                    if soup.find(string=re.compile('REFEREE')) != None:
                        match['referee'] = soup.find(string=re.compile('REFEREE')).text.replace(',','').replace('REFEREE: ','').strip()
                    match['status'] = soup.find('div',{'class': "game-status"}).find('span',{'class': "game-time"}).text 

                    for side in sides: #home or away
                        wrong_side = [x for x in sides if x != side ][0]# Home and Away mixed up on website

                        game_details = soup.find('div', {'class':'competitors'}).find('div', {'class':re.compile(f'team {wrong_side}')})
                        team_id = game_details.find('a', {'class':re.compile(f'team-name')}).get('data-clubhouse-uid').replace('s:600~t:','T')
                        if team_id not in team_details.keys():
                            team_details[team_id] = {}
                            team_details[team_id]['id'] = team_id
                            team_details[team_id]['long_name'] = game_details.find('span', {'class':'long-name'}).text
                            team_details[team_id]['short_name'] = game_details.find('span', {'class':'short-name'}).text
                            team_details[team_id]['abbrev'] = game_details.find('span', {'class':'abbrev'}).text
                            team_details[team_id]['page_url'] = game_details.find('a', {'class':f'team-name'}).get('href')

                        match[f'{side}_side_id'] = team_id

                        #Stats
                        if match['status'] == 'FT':
                            
                            team['id'] = team_id
                            team['match_id'] = match_id
                            team['side'] = side
                            team['score'] = soup.find('span',{'data-home-away': {side}, 'data-stat': "score"}).text.replace('\n','').replace('\t','')

                            match[f'{side}_score'] = team['score']

                            team['fouls_committed'] = soup.find('td',{'data-home-away': side, "data-stat":"foulsCommitted"}).text
                            team['yellow_cards'] = soup.find('td',{'data-home-away': side, "data-stat":"yellowCards"}).text
                            team['red_cards'] = soup.find('td',{'data-home-away': side, "data-stat":"redCards"}).text
                            team['offsides'] = soup.find('td',{'data-home-away': side, "data-stat":"offsides"}).text
                            team['corners'] = soup.find('td',{'data-home-away': side, "data-stat":"wonCorners"}).text
                            team['saves'] = soup.find('td',{'data-home-away': side, "data-stat":"saves"}).text
                            team['possession'] = soup.find('span',{'data-home-away': side, "data-stat":"possessionPct"}).text.replace('%','')
                            shots_summary = soup.find('span',{'data-home-away': side, "data-stat":"shotsSummary"}).text
                            team['shots_on_target'] = int(re.findall('\((\d+)\)', shots_summary)[0])
                            team['shots_off_target'] = int(re.findall('^\d+', shots_summary)[0]) - team['shots_on_target']

                            if side == 'home':
                                athletes = soup.find('div',{'class':'content-tab','style':'display: block;'})
                            else:
                                athletes = soup.find('div',{'class':'content-tab','style':'display: none;'})
                            athletes = athletes.find_all('div', {'class':'accordion-item'})

                            starting_lineup = 0
                            prev_player = ''

                            for athlete in athletes:
                                player = {}

                                player_id = athlete.get('data-id')
                                player['id'] = 'P'+player_id
                                
                                player_no = athlete.find('span',{'style':re.compile('.*display:inline-block.*')})
                                player_name = athlete.find('a',{'data-player-uid':re.compile(f'.*'+player_id)}).text.strip()

                                if player['id'] not in player_details.keys():
                                    player_details[player['id']] = {}
                                    player_details[player['id']]['id'] = player['id']
                                    player_details[player['id']]['team_id'] = team_id
                                    player_details[player['id']]['player_link'] = athlete.find('a',{'data-player-uid':re.compile(f'.*'+player_id)}).get('href')
                                    player_details[player['id']]['player_name'] = player_name
                                    player_details[player['id']]['player_no'] = player_no
                                
                                starting_lineup = starting_lineup + 0 if player_no is None else starting_lineup + 1
                                

                                is_sub = True if player_no is None or starting_lineup >11 else False
                                player['is_sub'] = is_sub
                                player['played'] = True if starting_lineup <=11 else False
                                
                                if is_sub:
                                    player['subbed_for'] = prev_player if is_sub else 'None'
                                    player['subbed_time'] = athlete.find('span',{'class':'icon-soccer-substitution-before'}).text if is_sub and starting_lineup <=11 else 'None'
                                
                                player['player_no'] = athlete.find(string=re.compile('.* .*')).text.strip() if player_no is None else player_no.text
                                player_details[player['id']]['player_no'] = player['player_no']
                                for data_stat in athlete.find_all('span', {'data-stat':re.compile('.*')}):
                                    player[data_stat.get('data-stat')] =  data_stat.text

                                prev_player = player_name

                                player_stats.append(player)
                        team_stats.append(team)
                matches.append(match)
                progress = progress_bar(i+1, match_files_count, start_time)
                logging.info(f'{progress}')
            self.matches = matches
            self.player_details = player_details
            self.player_stats = player_stats
            self.team_details = team_details
            self.teams_stats = team_stats

            data_dict = {'matches':matches, 'team_details':team_details, 'team_stats':team_stats, 'player_details':player_details, 'player_stats':player_stats}
            for key, data in data_dict.items():
                with open (f'{config.output_fld}{key}.json', 'w') as f:
                    json.dump(data,f)

    @logtofile
    def get_commentary_data(self, from_file = True):
        """
        Retrieves match commentary data from either pre-existing JSON files or from HTML files, and stores the data in a dictionary.

        Args:
            from_file (bool, optional): If True, reads existing JSON files to fetch data. If False, reads HTML files to extract data. Default is True.

        This function fetches the following data:
            1. Match ID
            2. Commentary (order, type, timestamp, description)

        The data is stored in the following dictionary:
            - self.commentary

        When from_file is set to False, the function also writes the data to a JSON file (commentary.json).
        """
        if from_file:
            logging.info(f'Getting match data from file')
            start_time = datetime.now()
            progress = progress_bar(0, 1, start_time)
            with open(f'{config.output_fld}commentary.json', 'r') as f:
                self.commentary = json.load(f)
            progress = progress_bar(1, 1, start_time)
            logging.info(f'{progress}')
        else:
            commentary_files = glob.glob(f'{config.games_fld}/commentary_*.html')
            matches = []

            commentary_files_count = len(commentary_files)
            start_time = datetime.now()

            for i, commentary_file in enumerate(commentary_files):
                match = {}
                with open(commentary_file) as fp:
                    soup = BeautifulSoup(fp, 'html.parser')

                    match['id'] = re.findall('.commentary_(\d+)\.html', commentary_file)[0]
                    comments = []
                    for comment in soup.find_all('tr',{'data-id': re.compile('comment-*')}):
                        entrie = {}
                        entrie['order'] = re.findall('.*-(\d+)',comment.get('data-id'))[0]
                        entrie['type'] = comment.get('data-type')
                        entrie['timestamp'] = comment.find('td', {'class':'time-stamp'}).text.replace("'",'').replace('-','0')
                        entrie['description'] = comment.find('td', {'class':'game-details'}).text.strip()
                        comments.append(entrie)
                    match['comments'] = comments
                matches.append(match)

                self.commentary = matches

                progress = progress_bar(i+1, commentary_files_count, start_time)
            logging.info(f'{progress}')

            with open (f'{config.output_fld}commentary.json', 'w') as f:
                    json.dump(matches,f)
