
import json
import os
import requests
from pdpyras import APISession, PDClientError

def send_to_opslevel(chunk_size, webhook_secret, payload):
    """ Send JSON to OpsLevel custom check webhook. """
    opslevel_url = 'https://app.opslevel.com/integrations/custom_event/' + webhook_secret
    headers = {
        'Content-Type': 'application/json'
    }
    services = payload['services']

    # split services into chunks based on chunk_size
    chunks = [services[i:i+chunk_size] for i in range(0, len(services), chunk_size)]

    # for each chunk make call to opslevel 
    for i, chunk in enumerate(chunks):
        new_data = {'services': chunk}

        # make call to opslevel webhook
        print(f"Calling OpsLevel Webhook for chunk {i} ... ", end='')
        #print()
        #print(json.dumps(new_data, indent=2))
        #print()

        response = requests.post(opslevel_url, json=new_data, headers=headers)
        #print(f"Status code: {response.status_code}. Message: {response.text}")

        if response.status_code == 202:
            response_data = json.loads(response.text)
            if response_data.get('result') != 'accepted':
                print(f"ERROR: Status code: {response.status_code}. Message: {response.text}")
            else:
                print("OK")
        else:
            if response.status_code == 413:
                # Handle HTTP 413 response
                print(f"ERROR: JSON must be smaller than 4MiB! Please set the environment variable NUMBER_SERVICES to something smaller than {chunk_size}")
                exit(413)
            else:
                # Handle other errors
                print(f"ERROR: Status code: {response.status_code}. Message: {response.text}")
                exit(response.status_code)

def list_services_n_escalation_policies(session):
    """ 
    List all services with their escalation policies and return JSON with a list of services including the service id,
    service name, escalation policy id, escalation policy name, and whether the escalation policy has oncall configured.

    Parameters:
        session (APISession): A pdpyras API session (PagerDuty).

    Returns:
        dict: The JSON response indicating whether the service has on_call configured. For example,
        {
            "services": [
            {
                "id": "PIQLOO7",
                "name": "notification_service",
                "escalation_policy": {
                    "id": "PEG3DYZ",
                    "name": "notification_service-ep",
                    "has_oncall": false
                }
            },
            {
                "id": "PF8QN8G",
                "name": "order_service",
                "escalation_policy": {
                    "id": "PX1WKZ8",
                    "name": "order_escalation",
                    "has_oncall": true
                }
            }
            ]
        }
    """
    try:
        services = session.iter_all('services', params={'include[]': 'escalation_policies'})
        ol_services = []
        for service in services:
            ol_service = {
                'id': service['id'],
                'name': service['name'],
                'escalation_policy': {
                    'id': service['escalation_policy']['id'],
                    'name': service['escalation_policy']['name'],
                    'has_oncall': False
                }
            }

            for rule in service['escalation_policy']['escalation_rules']:
                for target in rule['targets']:
                    if target['type'] == 'schedule_reference':
                        ol_service['escalation_policy']['has_oncall'] = True

            ol_services.append(ol_service)
            #print(json.dumps(service, indent=4))

        return {'services': ol_services}
    except PDClientError as e:
        if e.response.status_code == 401:
            print("Authorization error: Please check your API key.")
            exit(1)
        else:
            print(f"Error accessing API: {e}")
            exit(1)
    except Exception as e:
        print(f"Unexpected error listing services: {str(e)}")
        exit(1)

def main():
    # Check if the PAGERDUTY_API_KEY environment variable is set
    api_key = os.getenv('PAGERDUTY_API_KEY')
    if not api_key:
        print("Error: The 'PAGERDUTY_API_KEY' environment variable is not set!")
        exit(1)

    # Check if the OPSLEVEL_WEBHOOK environment variable is set
    opslevel_key = os.getenv('OPSLEVEL_WEBHOOK_SECRET')
    if not opslevel_key:
        print("Error: The 'OPSLEVEL_WEBHOOK_SECRET' environment variable is not set!")
        exit(1)

    # Check if the NUMBER_SERVICES environment variable is set. If not set to 10000
    number_services = os.getenv('NUMBER_SERVICES')
    if not number_services:
        number_services = 10000
    else:
        number_services = int(number_services)

    # Initialize API session
    session = APISession(api_key)

    # Run the function to list services
    converted_json = list_services_n_escalation_policies(session)
    #print(json.dumps(converted_json, indent=2))

    send_to_opslevel(number_services, opslevel_key, converted_json)

if __name__ == '__main__':
    main()
