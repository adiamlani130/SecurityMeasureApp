#Import necessary libraries and packages
import boto3
import weatherInformation as weatherInformation 
#Send notification to provided phone number in sandbox with summary of security status
def send_sms(phone_number, message):
   """
   Send a message to a phone number using AWS SNS.
  
   :param phone_number: The recipient's phone number in E.164 format (e.g., +1234567890)
   :param message: The message content to send
   """
   # Create an SNS client
   # Add relevant location information to message
   message+=weatherInformation.getWeatherSummary(True)
   sns = boto3.client('sns')
   #Try to send message, catch error
   try:
       # Send the message
       response = sns.publish(
           PhoneNumber=phone_number,
           Message=message
       )
       print(f"Message sent! Message ID: {response['MessageId']}")
   except Exception as e:
       print(f"Error sending message: {e}")
