import click
import ckanext.hdx_pages.model as pages_model


@click.command(short_help='Initialize the pages database table')
def initdb():
    pages_model.create_table()

@click.command(short_help='Clean the pages database table')
def cleandb():
    pages_model.delete_table()

@click.command(short_help='Drop the pages database table')
def droptabledb():
    pages_model.drop_table()
