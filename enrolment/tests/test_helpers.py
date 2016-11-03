import http
from unittest.mock import patch

from requests import Response
from requests.exceptions import HTTPError, ConnectionError, SSLError, Timeout

from django import forms

from enrolment import helpers


def mock_validator_one(value):
    raise forms.ValidationError('error one')


def mock_validator_two(value):
    raise forms.ValidationError('error two')


class MockForm(forms.Form):
    field = forms.CharField(
        validators=[mock_validator_one, mock_validator_two],
    )


class MockHaltingValidatorForm(forms.Form):
    field = forms.CharField(
        validators=helpers.halt_validation_on_failure(
            mock_validator_one, mock_validator_two,
        )
    )


def test_validator_raises_all():
    form = MockForm({'field': 'value'})
    assert form.is_valid() is False
    assert 'error one' in form.errors['field']
    assert 'error two' in form.errors['field']


def test_halt_validation_on_failure_raises_first():
    form = MockHaltingValidatorForm({'field': 'value'})
    assert form.is_valid() is False
    assert 'error one' in form.errors['field']
    assert 'error two' not in form.errors['field']


@patch.object(helpers.api_client.company, 'retrieve_companies_house_profile',)
def test_get_company_name_handles_exception(
        mock_retrieve_companies_house_profile, caplog):
    exceptions = [HTTPError, ConnectionError, SSLError, Timeout]
    for exception in exceptions:
        mock_retrieve_companies_house_profile.side_effect = exception('!')
        response = helpers.get_company_name('01234567')
        log = caplog.records[0]
        assert response is None
        assert log.levelname == 'ERROR'
        assert log.msg == 'Unable to get name for "01234567".'


@patch.object(helpers.api_client.company, 'retrieve_companies_house_profile',)
def test_get_company_name_handles_bad_status(
        mock_retrieve_companies_house_profile, caplog):

    mock_response = Response()
    mock_response.status_code = http.client.BAD_REQUEST
    mock_retrieve_companies_house_profile.return_value = mock_response

    name = helpers.get_company_name('01234567')
    log = caplog.records[0]

    mock_retrieve_companies_house_profile.assert_called_once_with('01234567')
    assert name is None
    assert log.levelname == 'ERROR'
    assert log.msg == 'Unable to get name for "01234567". Status "400".'


@patch.object(helpers.api_client.company, 'retrieve_companies_house_profile',)
def test_get_company_name_handles_good_status(
        mock_retrieve_companies_house_profile, caplog):

    mock_response = Response()
    mock_response.status_code = http.client.OK
    mock_response.json = lambda: {'company_name': 'Extreme Corp'}
    mock_retrieve_companies_house_profile.return_value = mock_response

    name = helpers.get_company_name('01234567')

    mock_retrieve_companies_house_profile.assert_called_once_with('01234567')
    assert name == 'Extreme Corp'


@patch.object(helpers.api_client.user, 'retrieve_profile')
def test_user_has_company(mock_retrieve_user_profile):
    mock_response = Response()
    mock_response.status_code = http.client.OK
    mock_response.json = lambda: {'company': 'Extreme Corp'}
    mock_retrieve_user_profile.return_value = mock_response

    user_has_company = helpers.user_has_company(sso_user_id=1)

    assert user_has_company is True


@patch.object(helpers.api_client.user, 'retrieve_profile')
def test_user_has_company_404(mock_retrieve_user_profile):
    mock_response = Response()
    mock_response.status_code = http.client.NOT_FOUND
    mock_retrieve_user_profile.return_value = mock_response

    user_has_company = helpers.user_has_company(sso_user_id=1)

    assert user_has_company is False


def test_get_employees_label():
    assert helpers.get_employees_label('1001-10000') == '1,001-10,000'


def test_get_sectors_labels():
    values = ['AGRICULTURE_HORTICULTURE_AND_FISHERIES', 'AEROSPACE']
    expected = ['Agriculture, Horticulture and Fisheries', 'Aerospace']
    assert helpers.get_sectors_labels(values) == expected


def test_get_employees_label_none():
    assert helpers.get_employees_label('') == ''


def test_get_sectors_labels_none():
    assert helpers.get_sectors_labels([]) == []


@patch.object(helpers, 'get_ip', return_value=None)
def test_is_request_international_IP_not_exposed_in_request(mock_get_ip, rf):
    request = rf.get('/')

    actual = helpers.is_request_international(request)

    mock_get_ip.assert_called_once_with(request)
    assert actual is False


@patch.object(helpers, 'get_ip', return_value='127.0.0.1')
def test_is_request_international_IP_not_in_database(mock_get_ip, rf):
    request = rf.get('/')

    actual = helpers.is_request_international(request)

    mock_get_ip.assert_called_once_with(request)
    assert actual is False


def test_is_request_international_IP_from_international_users(rf):
    request = rf.get('/')
    for ip in ['2.0.0.0', '3.0.0.0', '2.144.0.0']:
        with patch.object(helpers, 'get_ip', return_value=ip):
            assert helpers.is_request_international(request) is True


@patch.object(helpers, 'get_ip', return_value='90.254.120.205')
def test_is_request_international_IP_from_domestic_user(rf):
    request = rf.get('/')

    assert helpers.is_request_international(request) is False
