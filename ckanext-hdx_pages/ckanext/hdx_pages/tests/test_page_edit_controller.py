"""
Created on March 19, 2019

@author: Dan


"""

import logging as logging

import ckan.logic as logic
import ckan.model as model
import pytest
from ckan.lib.helpers import url_for

from ckanext.hdx_dataviz.tests import LOCATION, SYSADMIN, USER

_get_action = logic.get_action
NotAuthorized = logic.NotAuthorized

log = logging.getLogger(__name__)

page_elnino = {
    "name": "elnino",
    "title": "El Nino",
    "description": "El Nino Lorem Ipsum is simply dummy text of the printing and typesetting industry. Lorem Ipsum has been the industry's standard dummy text ever since the 1500s, when an unknown printer took a galley of type and scrambled it to make a type specimen book.",
    "type": "event",
    "status": "ongoing",
    "groups": [LOCATION],
    "state": "active",
    "extras": '{"show_title": "on"}',
    "sections": '[{"data_url": "https://data.humdata.org/dataset/wfp-and-fao-overview-of-countries-affected-by-the-2015-16-el-nino/resource/de96f6a5-9f1f-4702-842c-4082d807b1c1/view/08f78cd6-89bb-427c-8dce-0f6548d2ab21", "type": "map", "description": null, "max_height": "350px", "section_title": "El Nino Affected Countries"}, {"data_url": "https://data.humdata.org/search?q=el%20nino", "type": "data_list", "description": null, "max_height": null, "section_title": "Data"}]',
}


@pytest.mark.usefixtures(
    "keep_db_tables_on_clean", "clean_db", "clean_index", "setup_user_data"
)
class TestHDXControllerPage(object):
    @staticmethod
    def _get_page_post_param():
        return {
            "name": "elninoupdate",
            "title": "Updated El Nino Lorem Ipsum",
            "description": "El Nino Lorem Ipsum is simply dummy text of the printing and typesetting industry. Lorem Ipsum has been the industry's standard dummy text ever since the 1500s, when an unknown printer took a galley of type and scrambled it to make a type specimen book.",
            "type": "dashboards",
            "status": "archived",
            "state": "active",
            "save_custom_page": "active",
            "hdx_counter": "2",
            "groups": [LOCATION],
            "field_section_0_data_url": "https://data.humdata.org/dataset/wfp-and-fao-overview-of-countries-affected-by-the-2015-16-el-nino/resource/de96f6a5-9f1f-4702-842c-4082d807b1c1/view/08f78cd6-89bb-427c-8dce-0f6548d2ab21",
            "field_section_0_max_height": "350px",
            "field_section_0_section_title": "El Nino Affected Countries",
            "field_section_0_type": "map",
            "field_section_1_data_url": "https://data.humdata.local/search?q=el%20nino",
            "field_section_1_section_title": "Data",
            "field_section_1_type": "data_list",
        }

    # @pytest.mark.skipif(six.PY3, reason=u"The hdx_theme plugin is not available on PY3 yet")
    def test_page_edit(self, app):
        context = {"model": model, "session": model.Session, "user": USER}
        context_sysadmin = {
            "model": model,
            "session": model.Session,
            "user": SYSADMIN,
        }

        page_dict = _get_action("page_create")(context_sysadmin, page_elnino)
        assert page_dict
        assert "El Pico" not in page_dict.get("title")
        assert "Lorem Ipsum is simply dummy text" in page_dict.get(
            "description"
        )
        assert (
            "show_title" in page_dict.get("extras")
            and page_dict.get("extras").get("show_title") == "on"
        )

        # user = model.User.by_name(USER)

        post_params = self._get_page_post_param()

        url = url_for("hdx_custom_page.edit", id=page_dict.get("id"))
        try:
            res = app.post(
                url, data=post_params, extra_environ={"REMOTE_USER": USER}
            )
            assert "404 Not Found".lower() in res.status.lower()
            assert (
                "Sorry, the page you are looking for could not be found."
                in res.body
            )
            assert (
                "Please check the URL or login to HDX if you know that you have a permission to see this page."
                in res.body
            )
        except AssertionError:
            assert False
        except Exception:
            assert False

        model.User.by_name(SYSADMIN)

        try:
            res = app.post(
                url_for("hdx_custom_page.edit", id=page_dict.get("id")),
                data=post_params,
                environ_overrides={"REMOTE_USER": SYSADMIN},
                follow_redirects=False,
            )
            assert True
        except Exception:
            assert False
        assert "302 FOUND" in res.status

        post_params["tag_string"] = "some_new_tag"
        try:
            res = app.post(
                url_for("hdx_custom_page.edit", id=page_dict.get("id")),
                data=post_params,
                environ_overrides={"REMOTE_USER": SYSADMIN},
                follow_redirects=False,
            )
            assert "Tag some_new_tag not found" in res.body
        except Exception:
            assert False
        assert "200 OK" in res.status
        del post_params["tag_string"]

        elnino = _get_action("page_show")(context, {"id": page_dict.get("id")})
        assert elnino
        assert "Updated El Nino Lorem Ipsum" in elnino.get("title")
        assert "elninoupdate" in elnino.get("name")
        assert "archived" == elnino.get("status")

        del post_params["name"]
        try:
            res = app.post(
                url_for("hdx_custom_page.edit", id=page_elnino.get("name")),
                data=post_params,
                environ_overrides={"REMOTE_USER": SYSADMIN},
                follow_redirects=False,
            )
        except Exception:
            assert True
