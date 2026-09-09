from ckanext.hdx_search.controller_logic.search_logic import ArchivedUrlHelper


class TestArchivedUrlHelperOnArchivedPage:
    """Tests for ArchivedUrlHelper.on_archived_page"""

    def test_false_by_default_with_no_live_param(self):
        helper = ArchivedUrlHelper(10, 5, '/dataset', [])
        assert helper.on_archived_page is False

    def test_true_via_default_on_archived_page_fallback(self):
        helper = ArchivedUrlHelper(10, 5, '/dataset', [], default_on_archived_page=True)
        assert helper.on_archived_page is True

    def test_true_via_live_ext_archived_param(self):
        helper = ArchivedUrlHelper(10, 5, '/dataset', [('ext_archived', '1')])
        assert helper.on_archived_page is True

    def test_live_param_true_even_when_default_is_false(self):
        helper = ArchivedUrlHelper(10, 5, '/dataset', [('ext_archived', '1')],
                                    default_on_archived_page=False)
        assert helper.on_archived_page is True

    def test_live_param_and_default_both_true(self):
        helper = ArchivedUrlHelper(10, 5, '/dataset', [('ext_archived', '1')],
                                    default_on_archived_page=True)
        assert helper.on_archived_page is True


class TestArchivedUrlHelperUnarchivedDisabledAndUrl:
    """Tests for ArchivedUrlHelper.unarchived_disabled / unarchived_url"""

    def test_locked_disables_regardless_of_zero_count(self):
        helper = ArchivedUrlHelper(0, 5, '/dataset', [], default_on_archived_page=True)
        assert helper.unarchived_disabled is True
        assert helper.unarchived_url is None

    def test_locked_disables_regardless_of_positive_count(self):
        helper = ArchivedUrlHelper(100, 5, '/dataset', [], default_on_archived_page=True)
        assert helper.unarchived_disabled is True
        assert helper.unarchived_url is None

    def test_zero_count_disables_when_not_locked(self):
        helper = ArchivedUrlHelper(0, 5, '/dataset', [], default_on_archived_page=False)
        assert helper.unarchived_disabled is True
        assert helper.unarchived_url is None

    def test_enabled_when_not_locked_and_count_positive(self):
        helper = ArchivedUrlHelper(10, 5, '/dataset', [])
        assert helper.unarchived_disabled is False
        assert helper.unarchived_url == '/dataset?'

    def test_unarchived_url_preserves_other_params_and_drops_ext_archived(self):
        helper = ArchivedUrlHelper(10, 5, '/dataset',
                                    [('ext_archived', '1'), ('organization', 'who')])
        url = helper.unarchived_url
        assert url is not None
        assert 'organization=who' in url
        assert 'ext_archived' not in url


class TestArchivedUrlHelperArchivedDisabledAndUrl:
    """Tests for ArchivedUrlHelper.archived_disabled / archived_url"""

    def test_disabled_and_none_when_zero_archived(self):
        helper = ArchivedUrlHelper(10, 0, '/dataset', [])
        assert helper.archived_disabled is True
        assert helper.archived_url is None

    def test_enabled_when_archived_positive(self):
        helper = ArchivedUrlHelper(10, 5, '/dataset', [])
        assert helper.archived_disabled is False
        url = helper.archived_url
        assert url is not None
        assert 'ext_archived=1' in url

    def test_archived_side_unaffected_by_default_on_archived_page(self):
        locked = ArchivedUrlHelper(10, 5, '/dataset', [], default_on_archived_page=True)
        unlocked = ArchivedUrlHelper(10, 5, '/dataset', [], default_on_archived_page=False)
        assert locked.archived_disabled is False
        assert unlocked.archived_disabled is False
        assert locked.archived_url is not None
        assert unlocked.archived_url is not None


class TestArchivedUrlHelperShowLinks:
    """Tests for show_archived_link / show_unarchived_link"""

    def test_show_archived_link_false_when_already_on_archived_page(self):
        helper = ArchivedUrlHelper(10, 5, '/dataset', [('ext_archived', '1')])
        assert helper.show_archived_link is False

    def test_show_archived_link_false_when_zero_archived(self):
        helper = ArchivedUrlHelper(10, 0, '/dataset', [])
        assert helper.show_archived_link is False

    def test_show_archived_link_true_when_on_unarchived_page_and_archived_available(self):
        helper = ArchivedUrlHelper(10, 5, '/dataset', [])
        assert helper.show_archived_link is True

    def test_show_unarchived_link_false_when_locked(self):
        helper = ArchivedUrlHelper(10, 5, '/dataset', [('ext_archived', '1')],
                                    default_on_archived_page=True)
        assert helper.show_unarchived_link is False

    def test_show_unarchived_link_false_when_not_on_archived_page(self):
        helper = ArchivedUrlHelper(10, 5, '/dataset', [])
        assert helper.show_unarchived_link is False

    def test_show_unarchived_link_false_when_zero_unarchived(self):
        helper = ArchivedUrlHelper(0, 5, '/dataset', [('ext_archived', '1')])
        assert helper.show_unarchived_link is False

    def test_show_unarchived_link_true_when_on_archived_page_and_unarchived_available(self):
        helper = ArchivedUrlHelper(10, 5, '/dataset', [('ext_archived', '1')])
        assert helper.show_unarchived_link is True


class TestArchivedUrlHelperRedirectIfNeeded:
    """Tests for redirect_if_needed"""

    def test_no_redirect_when_on_archived_page(self):
        helper = ArchivedUrlHelper(0, 5, '/dataset', [], default_on_archived_page=True)
        assert helper.redirect_if_needed() is None

    def test_no_redirect_when_unarchived_has_results(self):
        helper = ArchivedUrlHelper(10, 5, '/dataset', [])
        assert helper.redirect_if_needed() is None

    def test_no_redirect_when_no_archived_results(self):
        helper = ArchivedUrlHelper(0, 0, '/dataset', [])
        assert helper.redirect_if_needed() is None

    def test_redirects_to_archived_when_unarchived_empty_and_archived_available(self):
        helper = ArchivedUrlHelper(0, 5, '/dataset', [])
        result = helper.redirect_if_needed()
        assert result is not None
