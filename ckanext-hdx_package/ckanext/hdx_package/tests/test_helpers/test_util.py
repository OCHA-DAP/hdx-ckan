import pytest

from ckanext.hdx_package.helpers.util import find_approx_download


class TestFindApproxDownload:
    def test_zero_downloads(self):
        """Test with zero downloads returns 0"""
        assert find_approx_download(0) == 0

    def test_single_digit_downloads(self):
        """Test with single digit downloads returns 0"""
        assert find_approx_download(1) == 0
        assert find_approx_download(5) == 0
        assert find_approx_download(9) == 0

    def test_ten_downloads(self):
        """Test with exactly 10 downloads returns 10"""
        assert find_approx_download(10) == 10

    def test_two_digit_downloads(self):
        """Test with two-digit downloads rounds down to nearest 10"""
        assert find_approx_download(15) == 10
        assert find_approx_download(23) == 20
        assert find_approx_download(49) == 40
        assert find_approx_download(99) == 90

    def test_one_hundred_downloads(self):
        """Test with exactly 100 downloads returns 100"""
        assert find_approx_download(100) == 100

    def test_three_digit_downloads(self):
        """Test with three-digit downloads rounds down to nearest 100"""
        assert find_approx_download(150) == 100
        assert find_approx_download(250) == 200
        assert find_approx_download(999) == 900
        assert find_approx_download(9999) == 9900

    def test_ten_thousand_downloads(self):
        """Test with exactly 10000 downloads returns 10000"""
        assert find_approx_download(10000) == 10000

    def test_large_downloads(self):
        """Test with large downloads rounds down to nearest 1000"""
        assert find_approx_download(15000) == 15000
        assert find_approx_download(15999) == 15000
        assert find_approx_download(99999) == 99000
        assert find_approx_download(123456) == 123000
        assert find_approx_download(1000000) == 1000000

    def test_boundary_values(self):
        """Test boundary values between divider changes"""
        # Just below 10 (divider = None, returns 0)
        assert find_approx_download(9) == 0

        # At 10 (divider = 10)
        assert find_approx_download(10) == 10

        # Just below 100 (divider = 10)
        assert find_approx_download(99) == 90

        # At 100 (divider = 100)
        assert find_approx_download(100) == 100

        # Just below 10000 (divider = 100)
        assert find_approx_download(9999) == 9900

        # At 10000 (divider = 1000)
        assert find_approx_download(10000) == 10000

    def test_negative_downloads(self):
        """Test with negative downloads returns 0"""
        assert find_approx_download(-1) == 0
        assert find_approx_download(-100) == 0

    @pytest.mark.parametrize(
        'exact,expected',
        [
            (0, 0),
            (9, 0),
            (10, 10),
            (15, 10),
            (99, 90),
            (100, 100),
            (150, 100),
            (999, 900),
            (9999, 9900),
            (10000, 10000),
            (15500, 15000),
            (99999, 99000),
        ],
    )
    def test_parametrized_values(self, exact, expected):
        """Test various download values with expected results"""
        assert find_approx_download(exact) == expected
