
import ckan.lib.helpers as h
import ckanext.hdx_theme.tests.hdx_test_base as hdx_test_base


class TestExplorer(hdx_test_base.HdxBaseTest):

    def test_mobile_redirect(self):
        desktop_agents = [
            'Mozilla/5.0 (X11; Linux x86_64; rv:46.0) Gecko/20100101 Firefox/46.0',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.63 Safari/537.36'
        ]

        mobile_agents = [
            'Mozilla/5.0 (Linux; Android 4.1; Galaxy Nexus Build/JRN84D) AppleWebKit/535.19 (KHTML, like Gecko) Chrome/18.0.1025.166 Mobile Safari/535.19',
            'Mozilla/5.0 (iPhone; U; CPU iPhone OS 5_1_1 like Mac OS X; en) AppleWebKit/534.46.0 (KHTML, like Gecko) CriOS/19.0.1084.60 Mobile/9B206 Safari/7534.48.3',
            # 'Mozilla/5.0 (iPad; U; CPU OS 5_1_1 like Mac OS X; en-us) AppleWebKit/534.46.0 (KHTML, like Gecko) CriOS/19.0.1084.60 Mobile/9B206 Safari/7534.48.3',
            'Mozilla/5.0 (iPhone; CPU iPhone OS 6_0 like Mac OS X) AppleWebKit/536.26 (KHTML, like Gecko) Mobile/10A5376e'
        ]

        url = h.url_for(
            controller='ckanext.hdx_theme.controllers.explorer:ExplorerController',
            action='show'
        )
        for agent in desktop_agents:
            self._check_page_with_agent(url, agent, False)

        for agent in mobile_agents:
            self._check_page_with_agent(url, agent, True)

    def _check_page_with_agent(self, url, agent, mobile):
        page = self.app.get(url, headers={"User-Agent": agent})
        if mobile:
            assert not '<iframe' in str(page.response), 'Map explorer page should not be embedded in iframe for {}'.format(agent)
        else:
            assert '<iframe' in str(page.response), 'Map explorer page should be embedded in iframe for {}'.format(agent)
