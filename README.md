# OpsLevel Custom Check for PrescribeMe

## Set up OpsLevel

### Create Team and add yourself
* On the left side panel click People->Teams
* In the upper right hand corner click on the blue `+ New Team` button
  * Name = `PrescribeMe SRE Team`
  * Team Members = Add yourself
  * Click blue `Create Team` button in the bottom left
* You will be taken to the `PrescribeMe SRE Team` page
  * Add an Email contact

### Add PagerDuty integration and import services from PagerDuty

#### Add PagerDuty and enable service detection
* On the left side panel click Integrations->Add New Integration->PagerDuty
* In `Service Detection` section enable service detection

#### Import detected services
* On the left side panel click Catalog->Detected Services
* `Accept` all the services that are of interest

#### Add an Owner to all the detected services you accepted
* On the left side panel click Catalog->Services
* Select the service you want to change the owner of and click on it
  * Owner = `PrescribeMe SRE Team`
* Repeat for all the services that were just accepted into the catalog

### Add New Integration and Custom Check to OpsLevel
* On the left side panel click Integrations->Add New Integration
* Enter custom in the `Search by integration name`
* Click on `Custom Event`
  * What system are you integrating with? = `Custom Pagerduty`
* You will be taken to the integrations page for `Custom Pagerduty`. 
  * Make note of Webhook URL Secret.

### Add a custom check
* On the left side panel click Service Maturity->Rubric
* In the upper right hand corner click on the blue `+ Add Check` button
* A Create Check panel will pop up
  * Select category -> Reliability since this is a Pagerduty Custom Check
  * Select level -> Bronze since this is a check all services should have
  * Scroll down to the `Integrations` section and click `Custom Event`
  * Double check the `category` and `level` is set correctly at the top
  * Check Name = `On-call Rotation Configured`
  * Filter = None required but I created one to only apply to the non-sample services in the account
  * Check Owner = `PrescribeMe SRE Team`
  * Integration = `Custom Pagerduty`
  * Service Specifier = `.services[] | .name`
  * Success Condition = `.services[]| select(.name == $ctx.alias) | .escalation_policy.has_oncall`. This is difficult to test when the custom check returns multiple results!
  * Result Message = See app
  * Sample Payload = See app. Run test should use at least 2 entries from the Sample Payload if testing a success criteria for multiple results!
  * Click the blue `Create` button in the bottom right hand corner.

## Custom check
The custom check was written in Python 3. It makes an API call to PagerDuty and looks for a schedule (on-call rotation) in the escalation policy of all the PagerDuty services it finds.

### Running custom check
#### Requirements
* OpsLevel Webhook Secret
* PagerDuty API Key
* Python 3
* pip

```bash
# export environment variables PAGERDUTY_API_KEY and OPSLEVEL_WEBHOOK_SECRET
export PAGERDUTY_API_KEY=YOUR_PAGERDUTY_API_KEY
export OPSLEVEL_WEBHOOK_SECRET=YOUR_OPSLEVEL_WEBHOOK_SECRET

pip install -r requirements.txt
python app.py
```

If everything was set up fine in OpsLevel you should see that the status of the check `On-call Rotation Configured` was updated.

#### In container
**Build container**
```bash
docker-compose build
```
**Run container once**
```bash
# export environment variables PAGERDUTY_API_KEY and OPSLEVEL_WEBHOOK_SECRET
export PAGERDUTY_API_KEY=YOUR_PAGERDUTY_API_KEY
export OPSLEVEL_WEBHOOK_SECRET=YOUR_OPSLEVEL_WEBHOOK_SECRET

#
# Pick one below to run both do the same thing
#
docker-compose up

# OR
docker run --rm -e PAGERDUTY_API_KEY=$PAGERDUTY_API_KEY -e OPSLEVEL_WEBHOOK_SECRET=$OPSLEVEL_WEBHOOK_SECRET check:latest
```

#### On a schedule
* Use cron -
  * Requires an always on Linux/Unix machine/VM with cron installed that has access to both PagerDuty API and OpsLevel API
  * See https://www.baeldung.com/linux/load-env-variables-in-cron-job for how to set up a job that uses environment variables
  * See https://linuxconfig.org/wp-content/uploads/2013/03/crontab.png for crontab format
* Use CI system. Some examples listed below
  * Jenkins job
  * GitHub Actions
  * GitLab pipeline
* Kubernetes CronJob
  * See https://kubernetes.io/docs/tasks/job/automated-tasks-with-cron-jobs/

### Report on custom check
#### Requirements
* OpsLevel API Token
* Python 3
* pip

```bash
# export environment variables OPSLEVEL_API_TOKEN 
export OPSLEVEL_API_TOKEN=YOUR_OPSLEVEL_API_TOKEN

pip install -r requirements.txt
python report.py
```
