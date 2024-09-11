''' 
Generates a csv file from Zendesk support ticket data, formatted for Nomic Atlas

user defined columns can be updated to include any ticket and associated user and organization data
'''

from zdesk import Zendesk
import pandas as pd
import json

zendesk_url = ""
zendesk_email = ""
zendesk_api_key = ""

export_filename = 'zendesk_ticket_data.csv'

# columns to include in export after processing ZD ticket data
column_filter = ['url', 
	'id', 
	'created_at', 
	'type', 
	'subject', 
	'description', 
	'requester_email', 
	'submitter_email', 
	'assignee_email'
	]

zendesk = Zendesk(
	zendesk_url, 
	zdesk_email=zendesk_email, 
	zdesk_api=zendesk_api_key
	)

def get_zd_ticket_data():

	# handles pagination, returns list of responses from tickets endpoint
	tickets_raw_responses = zendesk.tickets_list(get_all_pages=True, complete_response=True)
	tickets = []
	for r in tickets_raw_responses:
		for ticket in r.get('content').get('tickets'):
			tickets.append(ticket)
	
	return tickets
	

def get_zd_users():

	users_raw_responses = zendesk.users_list(get_all_pages=True, complete_response=True)
	users = []
	for r in users_raw_responses:
		for user in r.get('content').get('users'):
			users.append(user)
	
	# create dict with user id as key for lookups
	users_dict = {u["id"]:u for u in users}

	return users_dict

def get_zd_organizations():

	organizations_raw_responses = zendesk.organizations_list(get_all_pages=True, complete_response=True)
	organizations = []
	for r in organizations_raw_responses:
		for organization in r.get('content').get('organizations'):
			organizations.append(organization)

	# create dict with org id as key for lookups
	organization_dict = {o["id"]:o for o in organizations}

	return organization_dict

def process_zd_ticket_data(ticket_data, user_data, organization_data):
	
	# look up user and org values and add columns to ticket data

	for ticket in ticket_data:

		requester_id = ticket.get('requester_id')
		if requester_id:
			user = user_data.get(requester_id)
			ticket['requester_email'] = user.get('email')

		submitter_id = ticket.get('submitter_id')
		if submitter_id:
			user = user_data.get(submitter_id)
			ticket['submitter_email'] = user.get('email')

		assignee_id = ticket.get('assignee_id')
		if assignee_id:
			user = user_data.get(assignee_id)
			ticket['assignee_email'] = user.get('email')

		organization_id = ticket.get('organization_id')
		if organization_id:
			org = organization_data.get(organization_id)
			ticket['organization_name'] = org.get('name')

	return ticket_data

def filter_zd_ticket_data(processed_ticket_data):
	# apply user-defined filter to processed ticket data

	prepared_tickets = []
	for ticket in processed_ticket_data:
		prepared_ticket = {}
		for cf in column_filter:
			prepared_ticket[cf] = ticket.get(cf)
		prepared_tickets.append(prepared_ticket)
	return prepared_tickets

def export_zd_data(filtered_ticket_data):
	# convert to csv
	tickets_json = json.dumps(filtered_ticket_data)

	df = pd.read_json(tickets_json)

	df.to_csv(export_filename, encoding='utf-8', index=False)

# todo: option to limit ticket data returned, e.g. start, end .. 
ticket_data = get_zd_ticket_data()

if(ticket_data):
	user_data = get_zd_users()
	org_data = get_zd_organizations()
	processed_ticket_data = process_zd_ticket_data(
		ticket_data, 
		user_data, 
		org_data
		)
	filtered_ticket_data = filter_zd_ticket_data(processed_ticket_data)
	export_zd_data(filtered_ticket_data)