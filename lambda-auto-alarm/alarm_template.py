alarmsTemplate = [
    {
        'Dimensions': [],
        'Namespace': 'AWS/Lambda',
        'MetricName': 'Errors',
        'ComparisonOperator' : 'GreaterThanThreshold',
        'Period': '5m',
        'Statistic': 'Average',
        'Threshold': 2
    },
    {
        'Dimensions': [],
        'Namespace': 'AWS/Lambda',
        'MetricName': 'Throttles',
        'ComparisonOperator' : 'GreaterThanThreshold',
        'Period': '5m',
        'Statistic': 'Average',
        'Threshold': 2
    }
]
