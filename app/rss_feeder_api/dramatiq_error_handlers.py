import dramatiq

@dramatiq.actor
def print_error(message_data, exception_data):
    print(f"Message {message_data['message_id']} failed:")
    print(f"  * type: {exception_data['type']}")
    print(f"  * message: {exception_data['message']!r}")
