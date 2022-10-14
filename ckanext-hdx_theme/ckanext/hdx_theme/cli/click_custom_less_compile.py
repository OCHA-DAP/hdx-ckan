import click
import logging

log = logging.getLogger(__name__)


@click.command(short_help='Compile all custom less themes')
def custom_less_compile():
    '''
    Compile all custom less themes
    '''
    import ckan.model as model
    import ckanext.hdx_org_group.helpers.organization_helper as org_helper

    log.info("Recompiling all custom less themes is DEPRECATED, not doing anything!")

    # org_helper.recompile_everything({'model': model, 'session': model.Session,
    #                                  'user': 'hdx', 'ignore_auth': True})

    log.info("Done")
