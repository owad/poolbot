from base import BaseReaction


class ChannelJoinReaction(BaseReaction):

    url_path = 'api/player'

    def match_request(self, message):
        return message.get('subtype') == 'channel_join'

    def process_request(self, message):
        user_id = self._find_subtype_mentions(message)[0]
        user_details = self.poolbot.client.api_call('users.info', user=user_id)

        # add the user to the users list if not already
        if user_id not in self.poolbot.users:
            response = self.poolbot.session.post(
                self._generate_url(),
                data={
                    'name': user_details['user']['name'],
                    'slack_id': user_details['user']['id']
                }
            )

        return 'Welcome to the baze {name}!'.format(
            name=user_details['user']['name']
        )
