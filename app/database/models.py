from datetime import datetime

from mongoengine import Document, StringField, IntField, ReferenceField, SequenceField, DateTimeField, FloatField, \
    BooleanField, NULLIFY


class Fighter(Document):
    token = SequenceField(primary_key=True)
    name = StringField(required=True)

    def __to_str(self):
        return f"Fighter(token={self.token}, name={self.name})"

    def __repr__(self):
        return self.__to_str()

    def __str__(self):
        return self.__to_str()


class MatchUp(Document):
    red = ReferenceField(Fighter)
    blue = ReferenceField(Fighter)
    red_pot = IntField(default=None)
    blue_pot = IntField(default=None)
    winner = StringField(required=True, choices=['red', 'blue'])
    is_tournament = BooleanField(required=True, default=False)
    timestamp = DateTimeField(default=datetime.utcnow)

    def __to_str(self):
        return f"MatchUp(red={self.red}, blue={self.blue}, winner={self.winner}, timestamp={self.timestamp})"

    def __repr__(self):
        return self.__to_str()

    def __str__(self):
        return self.__to_str()


class BetInfo(Document):
    match_up = ReferenceField(MatchUp)
    team_bet_on = StringField(required=True, choices=['red', 'blue'])
    model = StringField(required=True)
    red_confidence = FloatField(required=True, min_value=0, max_value=1)
    blue_confidence = FloatField(required=True, min_value=0, max_value=1)

    def __to_str(self):
        return (f"BetInfo(match_up={self.match_up}, team_bet_on={self.team_bet_on}, amount_bet={self.amount_bet}, "
                f"model={self.model}, red_confidence={self.red_confidence}, blue_confidence={self.blue_confidence})")

    def __repr__(self):
        return self.__to_str()

    def __str__(self):
        return self.__to_str()


Fighter.register_delete_rule(MatchUp, 'red', NULLIFY)
Fighter.register_delete_rule(MatchUp, 'blue', NULLIFY)
MatchUp.register_delete_rule(BetInfo, 'match_up', NULLIFY)
