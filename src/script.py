#Author José Pintado @jospint
from urllib.request import urlopen
import json
from pathlib import Path
import io
import csv

BASE_URL = 'http://data.udir.no/kl06/'
UTF8 = 'utf-8'

def main():
	#Parsing blob with all study plans
	norwayplans = json.load(urlopen(BASE_URL + 'laereplaner.json'))
	guids = set()
	def unique(guid):
		assert guid not in guids
		guids.add(guid)
		return guid

	def exists(guid):
		assert guid in guids
		return guid

	def make_guid(*args): return '-'.join(args)
	#getting information for each study plan
	outcomes = []
	for studyplan in norwayplans:
		studyplandetail = get_study_plan_detail(studyplan)
		scrappedstudyplan = {}
		plan_guid = '0-' + studyplandetail['kode']
		scrappedstudyplan['vendor_guid'] = unique(plan_guid)
		scrappedstudyplan['object_type'] = 'group'
		scrappedstudyplan['title'] = parse_title(studyplandetail)
		outcomes.append(scrappedstudyplan)
		subjects = studyplandetail['kompetansemaal-kapittel']['kompetansemaalsett']
		for subject in subjects:
			subject_guid = make_guid(plan_guid, subject['kode'])
			if len(subjects) > 1:
				scrappedsubject = {}
				scrappedsubject['vendor_guid'] = unique(subject_guid)
				scrappedsubject['object_type'] = 'group'
				scrappedsubject['title'] = parse_title(subject)[:255]
				scrappedsubject['parent_guids'] = exists(plan_guid)
				outcomes.append(scrappedsubject)
				parent = subject_guid
			else:
				parent = plan_guid

			for area in subject["hovedomraader-i-kontekst-av-kompetansemaalsett"]:
				sub = area['hovedomraadeverdier-under-kompetansemaalsett']
				area_guid = make_guid(subject_guid, area['kode'])
				outcomes.append({
					'vendor_guid': unique(area_guid),
					'object_type': 'group',
					'title': parse_title(sub)[:255],
					'parent_guids': exists(parent)
				})

			for goal in subject['kompetansemaal']:
				if goal.get('tilhoerer-hovedomraade'):
					goal_parent = make_guid(subject_guid, goal['tilhoerer-hovedomraade']['kode'])
				else:
					goal_parent = parent

				outcomes.append({
					"vendor_guid": unique(make_guid(subject_guid, goal['kode'])),
					'object_type': 'outcome',
					"title": goal['tittel'][:255],
					"parent_guids": exists(goal_parent)
				})

	print(json.dumps(outcomes))

	writer = csv.writer(open('outcomes.csv', 'w', newline=''))
	headers = ['vendor_guid', 'object_type', 'title', 'parent_guids']
	writer.writerow(headers)
	for outcome in outcomes:
		writer.writerow([outcome.get(h) for h in headers])


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
