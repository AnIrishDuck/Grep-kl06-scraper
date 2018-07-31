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
	guids = set()
	def unique(guid):
		if guid in guids: print(guid)
		guids.add(guid)
		return guid

	def make_guid(*args): return '-'.join(args)
	#getting information for each study plan
	outcomes = []
	for studyplan in norwayplans:
		studyplandetail = get_study_plan_detail(studyplan)
		scrappedstudyplan = {}
		plan_guid = '0:' + studyplandetail['kode']
		scrappedstudyplan['guid'] = unique(plan_guid)
		scrappedstudyplan['name'] = parse_title(studyplandetail)		
		outcomes.append(scrappedstudyplan)
		for subject in studyplandetail['kompetansemaal-kapittel']['kompetansemaalsett']:
			scrappedsubject = {}
			subject_guid = make_guid(plan_guid, subject['kode'])
			scrappedsubject['guid'] = unique(subject_guid)
			scrappedsubject['name'] = parse_title(subject)
			scrappedsubject['parent_guids'] = plan_guid
			outcomes.append(scrappedsubject)
			for area in subject["hovedomraader-i-kontekst-av-kompetansemaalsett"]:
				sub = area['hovedomraadeverdier-under-kompetansemaalsett']
				if area.get('kode'):
					outcomes.append({
						'guid': unique(make_guid(subject_guid, area['kode'])),
						'title': parse_title(sub),
						'parent_guids': subject_guid
					})
			outcomes.extend({
				"guid": unique(make_guid(subject_guid, goal['kode'])),
				"title": goal['tittel'],
				"parent_guids": make_guid(subject_guid, goal['tilhoerer-hovedomraade']['kode'])
			} for goal in subject['kompetansemaal'] if goal.get('tilhoerer-hovedomraade'))
	print(json.dumps(outcomes))

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
