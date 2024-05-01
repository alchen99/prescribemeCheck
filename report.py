import json
import os
import requests

from gql import Client, gql
from gql.transport.requests import RequestsHTTPTransport

def categories_query(after_cursor=None):
  return """
query {
  account {
    rubric{
      categories(first:100, after: AFTER) {
        pageInfo {
          endCursor
          hasNextPage
        }
        nodes {
          name
          id
        }
      }
    }
  }
}
""".replace(
        "AFTER", '"{}"'.format(after_cursor) if after_cursor else "null"
    )

def checks_query(after_cursor=None):
  return """
query GetCheckByCategoryId($categoryId: ID!){
  account {
    rubric{
      checks (categoryId: $categoryId, first: 100, after: AFTER) {
        pageInfo {
          endCursor
          hasNextPage
        }
        nodes {
          name
          id
          filter {
            id
          }
        }
      }
    }
  }
}  
  """.replace(
        "AFTER", '"{}"'.format(after_cursor) if after_cursor else "null"
    )

def all_services_query(after_cursor=None):
  return """
query GetAllServiceCheckResults($checkId: ID!) {
  account {
    services(first: 4, after: AFTER) {
      filteredCount
      pageInfo {
        endCursor
        hasNextPage
      }
      nodes{
        maturityReport{
          latestCheckResults(ids: [$checkId]) {
            check {
              name
            }
            service{
              name
              owner {
                name
                contacts {
                  address
                  displayName
                }
              }
            }
            serviceAlias
            status
            message
          }
        }
      }
    }
  }
}
  """.replace(
        "AFTER", '"{}"'.format(after_cursor) if after_cursor else "null"
    )

def filtered_services_query(after_cursor=None):
    return """
query GetFilteredServiceCheckResults($svcFilterId: ID!, $checkId: ID!) {
  account {
    services(first: 100, after: AFTER, filterIdentifier: {id: $svcFilterId}) {
      filteredCount
      pageInfo {
        endCursor
        hasNextPage
      }
      nodes{
        maturityReport{
          latestCheckResults(ids: [$checkId]) {
            check {
              name
            }
            service{
              name
              owner {
                name
                contacts {
                  address
                  displayName
                }
              }
            }
            serviceAlias
            status
            message
          }
        }
      }
    }
  }
}
""".replace(
        "AFTER", '"{}"'.format(after_cursor) if after_cursor else "null"
    )


def main():
  # Get the API token from the environment variable
  api_token = os.getenv('OPSLEVEL_API_TOKEN')
  if not api_token:
    print("Error: OPSLEVEL_API_TOKEN environment variable not set.")
    exit(1)

  # Get the category from the environment variable
  category = os.getenv('OPSLEVEL_RUBRIC_CATEGORY')
  if not category:
    category = "Reliability"

  # Get the check name from the environment variable
  check_name = os.getenv('OPSLEVEL_CHECK_NAME')
  if not check_name:
    check_name = "On-call Rotation Configured"

  # Headers to include in the request
  headers = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    'Authorization': f'Bearer {api_token}'
  }

  transport = RequestsHTTPTransport(
    url="https://api.opslevel.com/graphql/",
    headers=headers,
    use_json=True
  )

  client = Client(transport=transport, fetch_schema_from_transport=True)

  # Find category id for Reliability (default)
  has_next_page = True
  after_cursor = None
  category_id = None

  while has_next_page:
    categories_json = client.execute(gql(categories_query(after_cursor)))
    categories_nodes = categories_json['account']['rubric']['categories']['nodes']

    for category_node in categories_nodes:
      if category in category_node['name']:
        category_id = category_node['id']
        has_next_page = False
        break

    if category_id is None:
      has_next_page = categories_json['account']['rubric']['categories']['pageInfo']['hasNextPage']
      after_cursor = categories_json['account']['rubric']['categories']['pageInfo']['endCursor']

  #print(f"Category id = {category_id}")

  # Find check id for On-call Rotation Configured
  has_next_page = True
  after_cursor = None
  check_id = None
  filter_id = None
  params = {"categoryId": category_id}

  while has_next_page:
    checks_json = client.execute(gql(checks_query(after_cursor)), variable_values=params)
    checks_nodes = checks_json['account']['rubric']['checks']['nodes']

    for checks_node in checks_nodes:
      if check_name in checks_node['name']:
        check_id = checks_node['id']
        if checks_node['filter']:
          filter_id = checks_node['filter']['id']
        has_next_page = False
        break

    if check_id is None:
      has_next_page = checks_json['account']['rubric']['checks']['pageInfo']['hasNextPage']
      after_cursor = checks_json['account']['rubric']['checks']['pageInfo']['endCursor']

  #print(f"Check id = {check_id}")
  #print(f"Service filter id = {filter_id}")
  #print()

  # Find services that match check
  has_next_page = True
  after_cursor = None
  services = []

  print()
  print(f"Report for failed check {check_name} which has a check id of {check_id}")
  print(f"==========================================================================================================================")

  if filter_id is not None:
    params = {"svcFilterId": filter_id, "checkId": check_id}
    while has_next_page:
      services_json = client.execute(gql(filtered_services_query(after_cursor)), variable_values=params)
      services_nodes = services_json['account']['services']['nodes']
      for services_node in services_nodes:
        latestCheckResults = services_node['maturityReport']['latestCheckResults'][0]
        if latestCheckResults['status'] == 'failed':
          print(f"Service name = {latestCheckResults['service']['name']}")
          print(f"Service alias = {latestCheckResults['serviceAlias']}")
          print(f"Service owner name = {latestCheckResults['service']['owner']['name']}")
          for contact in latestCheckResults['service']['owner']['contacts']:
            if contact['displayName'] == 'Email':
              print(f"Service owner email = {contact['address']}")
          print(f"Check status = {latestCheckResults['status']}")
          print(f"Check message = {latestCheckResults['message']}")
          print()

      has_next_page = services_json['account']['services']['pageInfo']['hasNextPage']
      after_cursor = services_json['account']['services']['pageInfo']['endCursor']
  else:
    params = {"checkId": check_id}
    while has_next_page:
      services_json = client.execute(gql(all_services_query(after_cursor)), variable_values=params)
      services_nodes = services_json['account']['services']['nodes']
      for services_node in services_nodes:
        latestCheckResults = services_node['maturityReport']['latestCheckResults'][0]
        if latestCheckResults['status'] == 'failed':
          print(f"Service name = {latestCheckResults['service']['name']}")
          print(f"Service alias = {latestCheckResults['serviceAlias']}")
          print(f"Service owner name = {latestCheckResults['service']['owner']['name']}")
          for contact in latestCheckResults['service']['owner']['contacts']:
            if contact['displayName'] == 'Email':
              print(f"Service owner email = {contact['address']}")
          print(f"Check status = {latestCheckResults['status']}")
          print(f"Check message = {latestCheckResults['message']}")
          print()

      has_next_page = services_json['account']['services']['pageInfo']['hasNextPage']
      after_cursor = services_json['account']['services']['pageInfo']['endCursor']

if __name__ == '__main__':
    main()
