from datetime import datetime

from django.db.models import signals
import mongoengine
from mongoengine import fields

from winery.apps.crawling.extractors.vivino.util import url2id
from winery.apps.crawling.extractors.vivino.settings import MONGODB_CONFIG

mongoengine.connect(
    db=MONGODB_CONFIG['db'],
    username=MONGODB_CONFIG['user'],
    password=MONGODB_CONFIG['password'],
    host=MONGODB_CONFIG['host'],
    port=MONGODB_CONFIG['port']
)


class BaseDocument(mongoengine.Document):
    url = fields.StringField(required=True)
    _id = fields.StringField(primary_key=True, required=True)
    created_at = fields.DateTimeField()
    updated_at = fields.DateTimeField()

    meta = {
        'abstract': True,
        'allow_inheritance': True,
    }

    def save(self, **kwargs):
        """Save the document in database.
        Sends `pre_save` and `post_save` signals, and sets `created_at` and
        `updated_at` as needed.
        Use md5 hash as document key.
        """

        signals.pre_save.send(sender=self.__class__, instance=self)
        before = 'pk' in self and self.pk or None
        if not before:
            # Directly put the round microsecond values
            # so the value on the saved model is the same as in
            # the MongoDB database.
            self.created_at = datetime.utcnow()
            self._id = url2id(self.url)
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

    meta = {
        'abstract': True,
        'allow_inheritance': True,
    }

    name = fields.StringField(required=True)
    geo_query = fields.StringField(default=lambda: "")
    description = fields.StringField(default=lambda: "")


class Country(BaseRegion):
    pass


class Region(BaseRegion):
    country_name = fields.StringField()
    country_id = fields.StringField()
    parent_name = fields.StringField()
    parent_id = fields.StringField()
    ancestor_region_names = fields.StringField()
    ancestor_region_ids = fields.StringField()
    niveau = fields.IntField(default=lambda: -1)


class Winery(BaseDocument):
    name = fields.StringField(required=True)
    country_name = fields.StringField()
    country_id = fields.StringField()
    region_name = fields.StringField()
    region_id = fields.StringField()
    rating_value = fields.FloatField()
    rating_count = fields.FloatField()
    address = fields.StringField()
    websites = fields.ListField(fields.StringField())
    description = fields.StringField()


class Win(BaseDocument):
    name = fields.StringField(required=True)
    year = fields.StringField()
    country_name = fields.StringField()
    country_id = fields.StringField()
    region_name = fields.StringField()
    region_id = fields.StringField()
    rating_value = fields.FloatField()
    rating_count = fields.FloatField()
    price = fields.FloatField()
    foods = fields.ListField(fields.StringField())
    region_style = fields.StringField()
    region_style_url = fields.StringField()
    region_style_description = fields.StringField()
    grape_names = fields.ListField(fields.StringField())
    grape_ids = fields.ListField(fields.StringField())
    description = fields.StringField()


class Grape(BaseDocument):
    name = fields.StringField(required=True)
    description = fields.StringField()
    acidity = fields.FloatField()
    color = fields.FloatField()
    body = fields.FloatField()
