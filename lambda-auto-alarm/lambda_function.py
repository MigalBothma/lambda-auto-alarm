import json
import boto3
import logging
from os import getenv

from actions import getFunctions, getDesiredAlarmState, getAlarms, getCreatedAlarms, createMissingAlarms, compareAlarmStates
from alarm_template import alarmsTemplate

sns_topic_arn = getenv("SNS_TOPIC", None)

logger = logging.getLogger()
log_level = getenv("LOGLEVEL", "INFO")
level = logging.getLevelName(log_level)
logger.setLevel(level)

def lambda_handler(event, context):
    # Define a output for stats
    output = {}
    
    # Get Functions 
    functions = getFunctions()
    
    # Determine the desired state based on the template
    desiredState = getDesiredAlarmState(functions, alarmsTemplate)
    
    # Get the Current Alarms and their states
    currentAlarms = getAlarms()
    
    # Determine which are already created
    currentState = getCreatedAlarms(desiredState, currentAlarms)

    # Compare the current state of created alarms vs desired state
    currentState = compareAlarmStates(currentState, currentAlarms)
    
    # Create the missing alarms
    currentState, created = createMissingAlarms(currentState, sns_topic_arn)
    
    output['functions_count'] = len(functions)
    output['functions'] = functions
    output['desiredState'] = desiredState
    output['currentAlarms'] = currentAlarms
    output['createdAlarms'] = created
    output['currentState'] = currentState

    return output
