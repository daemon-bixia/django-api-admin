from django.urls import reverse


class MailHandler:
    def __init__(self):
        self.messages = []

    async def handle_DATA(self, server, session, envelope):
        self.messages.append(envelope)
        return '250 OK'


def login(client, user):
    """
    Logs the client out, and logs in again with the given user 
    """
    # Send a current_session GET request to get the csrftoken cookie
    url = reverse('headless:browser:account:current_session')
    client.get(url)

    # Extract the cookie from the client and add it to the next request's headers
    csrf_token = client.cookies.get('csrftoken')._value

    # Send a current_session DELETE request to logout
    url = reverse('headless:browser:account:current_session')
    client.delete(url, headers={'X-CSRFToken': csrf_token})

    # Send the login request
    url = reverse('headless:browser:account:login')
    client.post(
        url,
        data={'email': user.email, 'password': 'password'},
        headers={'X-CSRFToken': csrf_token},
        format="json"
    )
