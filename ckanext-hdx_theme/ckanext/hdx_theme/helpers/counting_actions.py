import sqlalchemy
import ckan.model as model

def count_user_orgs(user_id):
    q = sqlalchemy.text(''' SELECT count(*) FROM "user" u JOIN  member m ON u.id = m.table_id 
        JOIN "group" g ON m.group_id = g.id
        WHERE u.id='{user_id}'
            AND g.type='organization'
            AND m.state='active'
            AND g.state='active';'''.format(user_id=user_id))
            
    result = model.Session.connection().execute(q, entity_id=id).scalar()
    return result

def count_user_grps(user_id):
    q = sqlalchemy.text(''' SELECT count(*) FROM "user" u JOIN  member m ON u.id = m.table_id 
        JOIN "group" g ON m.group_id = g.id
        WHERE u.id='{user_id}'
            AND g.type='group'
            AND m.state='active' 
            AND g.state='active';'''.format(user_id=user_id))
            
    result = model.Session.connection().execute(q, entity_id=id).scalar()
    return result

def count_user_datasets(user_id):
    q = sqlalchemy.text('''select count(*) from package
        where creator_user_id = '{user_id}';'''.format(user_id=user_id))
   
    result = model.Session.connection().execute(q, entity_id=id).scalar()
    return result