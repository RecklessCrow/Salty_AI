from datetime import datetime

from mongoengine import Document, StringField, IntField, ReferenceField, SequenceField, DateTimeField, BooleanField, \
    NULLIFY


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
        string = f"MatchUp(red={self.red}, blue={self.blue}, winner={self.winner}, timestamp={self.timestamp}"
        if self.red_pot:
            string += f", red_pot={self.red_pot}"
        if self.blue_pot:
            string += f", blue_pot={self.blue_pot}"
        string += ")"
        return string

    def __repr__(self):
        return self.__to_str()

    def __str__(self):
        return self.__to_str()


Fighter.register_delete_rule(MatchUp, 'red', NULLIFY)
Fighter.register_delete_rule(MatchUp, 'blue', NULLIFY)
# MatchUp.register_delete_rule(BalanceHistory, 'match_up', NULLIFY)
