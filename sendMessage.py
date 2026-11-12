#Import necessary libraries and packages
import boto3
import config
import weatherInformation


#Send notification to provided phone number in sandbox with summary of security status
def send_sms(phone_number, message):
    """
    Send a message to a phone number using AWS SNS.

    :param phone_number: The recipient's phone number in E.164 format (e.g., +1234567890)
    :param message: The message content to send
    :return: True if SNS accepted the message
    """
    if not phone_number:
        print("ALERT_PHONE_NUMBER is not set; not sending SMS")
        return False
    # Add relevant weather information to message; a weather outage must not block the alert
    try:
        message += "\n" + weatherInformation.getWeatherSummary(True)
    except Exception as e:
        print(f"Could not add weather to message: {e}")
    #Try to send message, catch error
    try:
        sns = boto3.client('sns', region_name=config.AWS_REGION)
        response = sns.publish(
            PhoneNumber=phone_number,
            Message=message,
        )
        print(f"Message sent! Message ID: {response['MessageId']}")
        return True
    except Exception as e:
        print(f"Error sending message: {e}")
        return False
