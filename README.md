# lambda-auto-alarm
Lambda Function that automatically deploys Cloudwatch Alarms to all functions within the account.

Features:
- Auto Provisions CW Alarms For (MaxItems 1000) Lambda functions 
- Tracks alarms by getting alarms + storing state and comparing to desired state.
- Will upsert the CW Alarm if template differs from desired state.
