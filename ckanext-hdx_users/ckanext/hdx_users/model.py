import datetime
import logging

import sqlalchemy.orm as orm
from sqlalchemy.schema import Table, Column, UniqueConstraint, ForeignKey, CreateTable
import sqlalchemy.types as types
import vdm.sqlalchemy

import ckan.model as model
from ckan.model.domain_object import DomainObject
# import ckan.model.domain_object as domain_object

from ckan.model import meta, extension, core, user
import ckan.model.types as _types

mapper = orm.mapper
log = logging.getLogger(__name__)
# DomainObject = domain_object.DomainObject

HDX_ONBOARDING_USER_REGISTERED = 'hdx_onboarding_user_registered'
HDX_ONBOARDING_USER_VALIDATED = 'hdx_onboarding_user_validated'
HDX_ONBOARDING_DETAILS = 'hdx_onboarding_details'
HDX_ONBOARDING_FIRST_LOGIN = 'hdx_onboarding_first_login'
HDX_ONBOARDING_FOLLOWS = 'hdx_onboarding_follows'
HDX_ONBOARDING_ORG = 'hdx_onboarding_org'
HDX_ONBOARDING_FRIENDS = 'hdx_onboarding_friends'
HDX_LOGIN = 'hdx_login'
HDX_LOGOUT = 'hdx_logout'
HDX_FIRST_LOGIN = "hdx_first_login"

USER_STATUSES = [
    HDX_ONBOARDING_USER_REGISTERED,
    HDX_ONBOARDING_USER_VALIDATED,
    HDX_ONBOARDING_DETAILS,
    HDX_ONBOARDING_FIRST_LOGIN,
    HDX_ONBOARDING_FOLLOWS,
    HDX_ONBOARDING_ORG,
    HDX_ONBOARDING_FRIENDS
]


class ValidationToken(DomainObject):
    '''
    Tokens for validating email addresses upon user creation
    '''

    def __init__(self, user_id, token, valid):
        self.user_id = user_id
        self.token = token
        self.valid = valid

    @classmethod
    def get(self, user_id):
        query = meta.Session.query(ValidationToken)
        return query.filter_by(user_id=user_id).first()

    @classmethod
    def get_by_token(self, token):
        query = meta.Session.query(ValidationToken)
        return query.filter_by(token=token).first()

    @classmethod
    def check_existence(self):
        return validation_token_table.exists()


validation_token_table = Table('validation_tokens', meta.metadata,
                               Column('id', types.UnicodeText, primary_key=True, default=_types.make_uuid),
                               Column('user_id', types.UnicodeText, ForeignKey('user.id')),
                               Column('token', types.UnicodeText),
                               Column('valid', types.Boolean)
                               )

mapper(ValidationToken, validation_token_table, extension=[extension.PluginMapperExtension(), ])


def setup():
    '''
    Create our tables!
    '''
    print 'User Model setup...'
    if model.user_table.exists() and not validation_token_table.exists():
        print CreateTable(validation_token_table)
        validation_token_table.create()
        print 'DONE validation_token_table.create()'
    print 'DONE User Model setup...'


def delete_tables():
    '''
    Delete data from some extra tables to prevent IntegrityError between tests.
    '''

    if validation_token_table.exists():
        validation_token_table.delete()
        log.debug('Validation Token table deleted')
