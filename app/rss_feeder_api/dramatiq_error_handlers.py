import dramatiq

@dramatiq.actor
def feed_update_failure(message_data, exception_data):
    # TODO notify user via notification/socket/publis to kafka etc...
    print(f"Message {message_data['message_id']} failed:")
    print(f"  * type: {exception_data['type']}")
    print(f"  * message: {exception_data['message']!r}")
