import boto3
#remember to configure aws, pip install boto3, add the info
def send_sms(phone_number, message):
    """
    Send a message to a phone number using AWS SNS.
    
    :param phone_number: The recipient's phone number in E.164 format (e.g., +1234567890)
    :param message: The message content to send
    """
    # Create an SNS client
    sns = boto3.client('sns')

    try:
        # Send the message
        response = sns.publish(
            PhoneNumber=phone_number,
            Message=message
        )
        print(f"Message sent! Message ID: {response['MessageId']}")
    except Exception as e:
        print(f"Error sending message: {e}")

# Example usage
if __name__ == "__main__":
    phone_number = "+1234567890"  # Replace with your phone number
    message = "This is a test message from AWS SNS"
    
    send_sms(phone_number, message)
