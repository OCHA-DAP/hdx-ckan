from typing import Optional, Dict

from ckanext.hdx_package.tests.conftest import S3_BUCKET_NAME

def fetch_s3_object(conn, resource_id: str, file_name: str) -> Optional[Dict]:
    key = 'resources/{}/{}'.format(resource_id, file_name)
    try:
        s3_obj = conn.Object(S3_BUCKET_NAME, key).get()
        return s3_obj
    except Exception as e:
        return None
