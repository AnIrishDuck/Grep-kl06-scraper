#Author José Pintado @jospint
from urllib.request import urlopen
import json
from pathlib import Path
import io
import csv
import string

BASE_URL = 'http://data.udir.no/kl06/'
UTF8 = 'utf-8'

def main():
	#Parsing blob with all study plans
	norwayplans = json.load(urlopen(BASE_URL + 'laereplaner'))
	guids = set()
	def unique(guid):
		assert guid not in guids
		guids.add(guid)
		return guid

	def exists(guid):
		assert guid in guids
		return guid

	def make_guid(*args): return '-'.join(args)

	# making supplemental groups
	def make_toplevel(letter):
		guid = f"0-top-{letter}"
		return (
			letter,
			{
				'vendor_guid': unique(guid),
				'object_type': 'group',
				'title': letter,
			}
		)

	#getting information for each study plan
	alphabet = dict(make_toplevel(letter) for letter in string.ascii_uppercase)
	top_guids = dict((v, o['vendor_guid']) for v, o in alphabet.items())
	outcomes = list(alphabet.values())
	for studyplan in norwayplans:
		studyplandetail = get_study_plan_detail(studyplan)
		scrappedstudyplan = {}
		code = studyplandetail['kode']
		plan_guid = '0-' + code
		active = 'active' if len(studyplandetail['erstattes-av']) > 0 else 'deleted'
		scrappedstudyplan['vendor_guid'] = unique(plan_guid)
		scrappedstudyplan['workflow_state'] = active
		scrappedstudyplan['object_type'] = 'group'
		scrappedstudyplan['title'] = code + ' - ' + parse_title(studyplandetail)[:255]
		scrappedstudyplan['parent_guids'] = exists(top_guids[code[0]])
		outcomes.append(scrappedstudyplan)
		subjects = studyplandetail['kompetansemaal-kapittel']['kompetansemaalsett']
		for subject in subjects:
			subject_guid = make_guid(plan_guid, subject['kode'])
			if len(subjects) > 1:
				scrappedsubject = {}
				scrappedsubject['vendor_guid'] = unique(subject_guid)
				scrappedsubject['workflow_state'] = active
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
					'workflow_state': active,
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
					"workflow_state": active,
					'object_type': 'outcome',
					"title": goal['tittel'][:255],
					"parent_guids": exists(goal_parent)
				})

	print(json.dumps(outcomes))

	numbers = list(reversed([str(n) for n in range(1,7)]))
	defaults = list(v for pair in zip(numbers, numbers) for v in pair)
	writer = csv.writer(open('outcomes.csv', 'w', newline=''))
	headers = ['vendor_guid', 'object_type', 'title', 'parent_guids', 'ratings']
	writer.writerow(headers)
	for outcome in outcomes:
		ratings = defaults if outcome['object_type'] == 'outcome' else []
		writer.writerow([outcome.get(h) for h in headers[:-1]] + ratings)


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
