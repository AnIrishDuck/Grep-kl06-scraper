#Author José Pintado @jospint
from urllib.request import urlopen
import json
from pathlib import Path
import io

BASE_URL = 'http://data.udir.no/kl06/'
UTF8 = 'utf-8'

def main():
	#Parsing blob with all study plans
	norwayplans = json.load(urlopen(BASE_URL + 'laereplaner.json'))
	#getting information for each study plan
	scrappedplans = []
	for studyplan in norwayplans:
		studyplandetail = get_study_plan_detail(studyplan)
		scrappedstudyplan = {}
		scrappedstudyplan['code'] = studyplandetail['kode']
		scrappedstudyplan['name'] = parse_title(studyplandetail)		
		scrappedstudyplan['main_areas'] = [] if studyplandetail['hovedomraade-kapittel'] is None else [parse_title(area) for area in studyplandetail['hovedomraade-kapittel']['hovedomraader']]
		#getting information for each study plan subject
		scrappedstudyplan['subjects'] = []
		for subject in studyplandetail['kompetansemaal-kapittel']['kompetansemaalsett']:
			scrappedsubject = {}
			scrappedsubject['name'] = parse_title(subject)
			scrappedsubject['main_areas'] = [parse_title(area['hovedomraadeverdier-under-kompetansemaalsett']) for area in subject['hovedomraader-i-kontekst-av-kompetansemaalsett']]
			scrappedsubject['goals'] = [goal['tittel'] for goal in subject['kompetansemaal']]
			scrappedstudyplan['subjects'].append(scrappedsubject)
		scrappedplans.append(scrappedstudyplan);
	print(json.dumps(scrappedplans))

def get_study_plan_detail(studyplan):
	studyplanfilename =  f"{studyplan['kode']}.json"
	studyplandetail = None
	#if we did not save locally the json file, we do it now
	if not Path(studyplanfilename).is_file():	
		studyplandetail = json.load(urlopen(BASE_URL + studyplanfilename))
		with open(studyplanfilename, 'w', encoding=UTF8) as fi:
			json.dump(studyplandetail, fi)
	#else we load it from local folder		
	else:
		with open(studyplanfilename, encoding=UTF8) as fi:
			studyplandetail = json.load(fi)
	return studyplandetail

def parse_title(blobobject):
	#parses title objects in default language (norwegian)
	return None if blobobject['tittel'] is None else next((titleobject for titleobject in blobobject['tittel'] if titleobject['spraak'] == 'default'), {})['verdi']

main()