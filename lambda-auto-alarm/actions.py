import boto3
import json
import logging
from os import getenv

logger = logging.getLogger()
log_level = getenv("LOGLEVEL", "INFO")
level = logging.getLevelName(log_level)
logger.setLevel(level)

def getFunctions():
    lambda_client = boto3.client('lambda')
    functions= []
    paginator = lambda_client.get_paginator('list_functions')
    for page in paginator.paginate(PaginationConfig={'MaxItems': 1000}):
        for function in page['Functions']:
            functions.append(function)
    return functions

def getDesiredAlarmState(functions, alarmsTemplate):
    output = {}
    for function in functions:
        if function['FunctionName'] not in output:
            output[function['FunctionName']] = {}
        for alarm in alarmsTemplate:
            alarmName = f'{function["FunctionName"]}-{alarm["Namespace"]}-{alarm["MetricName"]}-{alarm["Period"]}-{alarm["Statistic"]}-{alarm["ComparisonOperator"]}'
            output[function['FunctionName']][alarmName] = {}
            output[function['FunctionName']][alarmName]['enabled'] = 0
            output[function['FunctionName']][alarmName]['template'] = alarm
    return output

def getAlarms():
    cw_client = boto3.client('cloudwatch')
    alarms = {}
    paginator = cw_client.get_paginator('describe_alarms')
    for page in paginator.paginate(PaginationConfig={'MaxItems': 1000}):
        for alarm in page['MetricAlarms']:
            alarmState={
                "MetricName": alarm['MetricName'],
                "Namespace": alarm['Namespace'],
                "Statistic": alarm['Statistic'],
                "Dimensions": alarm['Dimensions'],
                "Period": alarm['Period'],
                "EvaluationPeriods": alarm['EvaluationPeriods'],
                "Threshold": alarm['Threshold'],
                "ComparisonOperator": alarm['ComparisonOperator'],
                "AlarmArn": alarm['AlarmArn']
            }
            alarms[alarm['AlarmName']] = alarmState
    return alarms

def getCreatedAlarms(desiredState, currentAlarms):
    output = desiredState
    for function in desiredState:
        for alarm in desiredState[function]:
            if alarm in currentAlarms:
                output[function][alarm]['enabled'] = 1
    return output

def compareAlarmStates(currentState, currentAlarms):
    for function in currentState:
        for alarm in currentState[function]:
            if currentState[function][alarm]['enabled'] == 1:
                desired_period = convert_to_seconds(currentState[function][alarm]['template']['Period'])
                desired_alarm_state = currentState[function][alarm]['template']
                desired_alarm_state['Period'] = desired_period
                current_alarm_state = currentAlarms[alarm]
                
                if current_alarm_state['Period'] != desired_alarm_state['Period'] or current_alarm_state['Threshold'] != desired_alarm_state['Threshold']:
                    logger.info(f'State change detected on {current_alarm_state["AlarmArn"]}')
                    currentState[function][alarm]['enabled'] = 0
    return currentState

def createMissingAlarms(currentState,sns_topic_arn):
    created = []
    _currentState = currentState
    for function in currentState:
        for alarm in currentState[function]:
            if currentState[function][alarm]['enabled'] == 0 :
                template = currentState[function][alarm]['template']
                createAlarm(
                    AlarmName= alarm,
                    MetricName= template['MetricName'],
                    ComparisonOperator= template['ComparisonOperator'],
                    Period= template['Period'],
                    Threshold= template['Threshold'],
                    Statistic= template['Statistic'],
                    Namespace= template['Namespace'],
                    Dimensions= template['Dimensions'],
                    sns_topic_arn= sns_topic_arn
                )
                _currentState[function][alarm]['enabled'] = 1
                created.append(alarm)
    return _currentState, created

def convert_to_seconds(s):
    if type(s) == int or type(s) == float:
        return s
    try:
        seconds_per_unit = {"s": 1, "m": 60, "h": 3600, "d": 86400, "w": 604800}
        return int(s[:-1]) * seconds_per_unit[s[-1]]
    except Exception as e:
        # If any other exceptions which we didn't expect are raised
        # then fail and log the exception message.
        logger.error('Error converting threshold string {} to seconds!'.format(s, e))
        raise

def createAlarm(AlarmName, MetricName, ComparisonOperator, Period, Threshold, Statistic, Namespace, Dimensions, sns_topic_arn):
    AlarmDescription = 'Alarm created by lambda function lambda-auto-alarm'

    try:
        Period = convert_to_seconds(Period)
    except Exception as e:
        # If any other exceptions which we didn't expect are raised
        # then fail and log the exception message.
        logger.error(
            'Error converting Period specified {} to seconds for Alarm {}!: {}'.format(Period, AlarmName, e))

    Threshold = float(Threshold)
    try:
        cw_client = boto3.client('cloudwatch')

        alarm = {
            'AlarmName': AlarmName,
            'AlarmDescription': AlarmDescription,
            'MetricName': MetricName,
            'Namespace': Namespace,
            'Dimensions': Dimensions,
            'Period': Period,
            'EvaluationPeriods': 1,
            'Threshold': Threshold,
            'ComparisonOperator': ComparisonOperator,
            'Statistic': Statistic
        }

        if sns_topic_arn is not None:
            alarm['AlarmActions'] = [sns_topic_arn]

        cw_client.put_metric_alarm(**alarm)

        logger.info('Created alarm {}'.format(AlarmName))

    except Exception as e:
        # If any other exceptions which we didn't expect are raised
        # then fail and log the exception message.
        logger.error(
            'Error creating alarm {}!: {}'.format(AlarmName, e))
