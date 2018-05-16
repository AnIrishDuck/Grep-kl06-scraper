#Grep kl06 scraper. Author José Pintado @jospint
from urllib.request import urlopen
import json
from pathlib import Path

BASE_URL = 'http://data.udir.no/kl06/'

def main():
	#Parsing blob with all study plans
	norwayplans = json.load(urlopen(BASE_URL + 'laereplaner.json'))

	relevantdata = []

	#getting information for each study plan
	for studyplan in norwayplans:
		studyplandetail = get_study_plan_detail(studyplan)

		studyplanresume = {}

		#study plan code
		studyplanresume['code'] = studyplandetail['kode']

		#study plan name
		studyplanresume['name'] = parse_title(studyplandetail)
		
		#study plan main areas
		studyplanresume['main_areas'] = []
		purposearray = [] if studyplandetail['hovedomraade-kapittel'] == None else studyplandetail['hovedomraade-kapittel']['hovedomraader']
		for purposeobject in purposearray:
			studyplanresume['main_areas'].append(parse_title(purposeobject))

		#getting information for each study plan subject
		studyplanresume['subject'] = []
		for competencegoal in studyplandetail['kompetansemaal-kapittel']['kompetansemaalsett']:
			competencegoalresume = {}

			#subject name
			competencegoalresume['name'] = parse_title(competencegoal)

			#main areas covered by subject
			competencegoalresume['main_areas_under_competences'] = []
			for areaundercompetencegoal in competencegoal['hovedomraader-i-kontekst-av-kompetansemaalsett']:
				competencegoalresume['main_areas_under_competences'].append(parse_title(areaundercompetencegoal['hovedomraadeverdier-under-kompetansemaalsett']))

			#goals
			competencegoalresume['goals'] = []
			for competencesubgoal in competencegoal['kompetansemaal']:
				competencegoalresume['goals'].append(competencesubgoal['tittel'])

			studyplanresume['subject'].append(competencegoalresume)

		relevantdata.append(studyplanresume);
	print(json.dumps(relevantdata))

def get_study_plan_detail(studyplan):
	studyplancode = studyplan['kode']
	studyplanfile = Path(f"./{studyplancode}.json")
	studyplandetail = None
	#if we did not save locally the json file, we do it now
	if not studyplanfile.is_file():	
		studyplandetail = json.load(urlopen(BASE_URL + f'{studyplancode}.json'))
		with open(f'{studyplancode}.json', 'w') as fi:
			json.dump(studyplandetail, fi)
	#else we load it from local folder		
	else:
		with open(f'{studyplancode}.json') as fi:
			studyplandetail = json.load(fi)
	return studyplandetail

def parse_title(blobobject):
	#parses title objects
	return parse_value_object(blobobject, 'tittel')

def parse_value_object(blobobject, key):
	#parses object to obtain value in default language (default, norwergian)
	blobobjecttitle =blobobject[key]
	titleobject = None if blobobjecttitle == None else next((x for x in blobobjecttitle if x['spraak'] == 'default'), None)
	return None if titleobject == None else titleobject['verdi']

main()
