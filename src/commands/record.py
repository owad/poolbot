import random

from .base import BaseCommand


class RecordCommand(BaseCommand):
    """Records the result of a match."""

    command_term = 'record'
    url_path = 'api/match/'
    victory_nouns = (
        'beat',
        'battered',
        'defeated',
        'destroyed',
        'crushed',
        'clobbered',
        'crushed',
        'defeated',
        'disgraced',
        'emasculated',
        'grilled',
        'embarrassed',
        'humiliated',
        'grannied',
        'hammered',
        'obliterated',
        'pounded',
        'trounced',
        'thrashed',
        'slayed',
        'smashed',
        'spangled',
        'walloped',
    )
    help_message = (
        'Record the outcome of a game between two players with the command '
        '`@poolbot record beat <opponent>`.'
    )

    def process_request(self, message):
        """The author is always the winner."""
        try:
            defeated_player = self._find_user_mentions(message)[0]
        except IndexError:
            return 'Sorry, I was unable to find an opponent in that message...'

        lower_text = message['text'].lower()
        if not any(noun in lower_text for noun in self.victory_nouns):
            return (
                'Sorry, I am unable to determine the result. Record a win by '
                'posting a message like `record beat @opponent`. You can '
                'replace `beat` with any word from the following list:\n'
                '`{victory_nouns}`'.format(
                    victory_nouns = ', '.join(noun for noun in self.victory_nouns)
                )
            )

        original_elo_winner = self.get_elo(message['user'])
        original_elo_loser = self.get_elo(defeated_player)

        response = self.poolbot.session.post(
            self._generate_url(),
            data={
                'winner': message['user'],
                'loser': defeated_player,
                'channel': message['channel'],
                'granny': 'grannied' in lower_text,
            }
        )

        if response.status_code == 201:

            # also check if we need to update an active challenge, so
            # fetch the challenge instance for the room
            response = self.poolbot.session.get(
                self.poolbot.generate_url('api/challenge'),
                params={
                    'channel': message['channel'],
                }
            )
            if response.status_code == 200:
                # see if the two players match
                data = response.json()
                if len(data):
                    challenge_players = (
                        data[0]['initiator'],
                        data[0]['challenger']
                    )
                    if message['user'] in challenge_players and defeated_player in challenge_players:
                        # bingo - update the players now the result is recorded
                        challenge_pk = data[0]['id']
                        response = self.poolbot.session.patch(
                            self.poolbot.generate_url(
                                'api/challenge/{challenge_pk}/'.format(
                                    challenge_pk=challenge_pk
                                )
                            ),
                            data={
                                'initiator': '',
                                'challenger': ''
                            }
                        )

            updated_elo_winner = self.get_elo(message['user'])
            updated_elo_loser = self.get_elo(defeated_player)

            delta_elo_winner = updated_elo_winner - original_elo_winner
            delta_elo_loser = updated_elo_loser - original_elo_loser

            return 'Victory recorded for {winner}[E {oew} ({ow}{dew})] against {loser}[E {oel} ({ol}{del})] ! :{emoji}:'.format(
                winner=self.poolbot.get_username(message['user']),
                emoji=self.get_emojis(),
                loser=defeated_player,
                oew=original_elo_winner,
                dew=delta_elo_winner,
                oel=original_elo_loser,
                del=delta_elo_loser,
                ow=("-" if delta_elo_winner < 0 else "+"),
                ol=("-" if delta_elo_loser < 0 else "+")
            )
        else:
            return 'Sorry, I was unable to record that result.'
        # TODO generate some funny phrase to celebrate the victory
        # eg highlight an unbetean run, or X consequtive lose etc

    def get_elo(self, player):
        response = self.poolbot.session.get(
            self.poolbot.generate_url('/api/player/{player}'.format(player=player))
        )
        if response.status_code == 200:
            data = response.json()
            elo = int(data['elo'])
            return elo
        else
            return 0

    def get_emojis(self):
        """Returns a random emojis to append to the victory reply."""
        emojis = self.poolbot.config['record_emojis']
        return random.choice(emojis)
