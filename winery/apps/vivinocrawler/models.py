from datetime import datetime
import hashlib

from django.db.models import signals
import mongoengine
from mongoengine import fields


HASHER = hashlib.md5()

class BaseDocument(mongoengine.Document):
    url = fields.StringField(required=True)
    _id = fields.StringField(primary_key=True, required=True)
    created_at = fields.DateTimeField()
    updated_at = fields.DateTimeField()



    def save(self, **kwargs):
        """Save the document in database.
        Sends `pre_save` and `post_save` signals, and sets `created_at` and
        `updated_at` as needed.
        """

        signals.pre_save.send(sender=self.__class__, instance=self)
        before = 'pk' in self and self.pk or None
        if not before:
            # Directly put the round microsecond values
            # so the value on the saved model is the same as in
            # the MongoDB database.
            self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        result = super(BaseDocument, self).save(**kwargs)
        after = 'pk' in self and self.pk or None
        signals.post_save.send(sender=self.__class__, instance=self,
                               created=bool(not before and after))
        return result

    def update(self, **kwargs):
        """Update specific fields of the document in database.
        Also sets `updated_at` as needed.
        """

        if 'set__updated_at' not in kwargs:
            kwargs['set__updated_at'] = datetime.utcnow()
        return super(BaseDocument, self).update(**kwargs)

    def delete(self, **kwargs):
        """Remove the document from the database.
        Sends `pre_delete` and `post_delete` signals.
        """

        signals.pre_delete.send(sender=self.__class__, instance=self)
        super(BaseDocument, self).delete(**kwargs)
        signals.post_delete.send(sender=self.__class__, instance=self)

    def __delitem__(self, name):
        """Implement __delitem__ to make PyLint happy.
        We do not raise NotImplementedError, because this would imply this is
        an abstract function which needs to be implmemented.
        """

        raise RuntimeError('Not supported')

    def __unicode__(self):
        if self.pk:
            return unicode(self.pk)
        return u'document'


class BaseRegion(BaseDocument):
    name = fields.StringField(required=True)
    google_address = fields.StringField(default=lambda: "")
    description = fields.StringField()


class Country(BaseRegion):
    sub_regions_count = fields.IntField()
    wineries_count = fields.IntField()
    wins_count = fields.IntField()


class Region(BaseRegion):
    country = fields.StringField()
    parent_region = fields.StringField()
    sub_regions_count = fields.IntField()
    wineries_count = fields.IntField()
    wins_count = fields.IntField()


class Winery(BaseDocument):
    name = fields.StringField(required=True)
    country = fields.StringField()
    country_id = fields.StringField()
    region = fields.StringField()
    region_id = fields.StringField()
    win_count = fields.IntField()
    rating = fields.FloatField()
    description = fields.StringField()


class Win(BaseDocument):
    name = fields.StringField(required=True)
    year = fields.StringField()
    region = fields.StringField()
    country = fields.StringField()
    rating = fields.FloatField()
    rating_distribution = fields.ListField(
        field=fields.FloatField)
    price = fields.FloatField()
    food = fields.ListField(field=fields.StringField)
    description = fields.StringField()


class Grape(BaseDocument):
    name = fields.StringField(required=True)
    origin_region = fields.StringField()
    origin_country = fields.StringField()
    acidity = fields.FloatField()
    color = fields.FloatField()
    body = fields.FloatField()
