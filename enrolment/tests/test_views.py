import http
import requests
from unittest.mock import patch, Mock

import pytest

from django.core.urlresolvers import reverse

from enrolment import forms, helpers, validators
from enrolment.views import (
    api_client,
    CompanyEmailConfirmationView,
    EnrolmentView,
    EnrolmentInstructionsView,
    InternationalLandingView,
)
from sso.utils import SSOUser


valid_supplier_data_step = {
    'enrolment_view-current_step': EnrolmentView.SUPPLIER,
    EnrolmentView.SUPPLIER + '-mobile_number': '07507405138',
    EnrolmentView.SUPPLIER + '-mobile_confirmed': '07507405138',
    EnrolmentView.SUPPLIER + '-terms_agreed': True,
}

valid_sms_verify_step = {
    'enrolment_view-current_step': EnrolmentView.SMS_VERIFY,
    EnrolmentView.SMS_VERIFY + '-sms_code': '123456',
}


@pytest.fixture
def sso_user():
    return SSOUser(
        id=1,
        email='jim@example.com',
    )


def process_request(self, request):
    request.sso_user = sso_user()


def process_request_anon(self, request):
    request.sso_user = None


@pytest.fixture
def buyer_form_data():
    return {
        'full_name': 'Jim Example',
        'email_address': 'jim@example.com',
        'sector': 'AEROSPACE',
        'terms': True
    }


@pytest.fixture
def buyer_request(rf, client, buyer_form_data):
    request = rf.post('/', buyer_form_data)
    request.session = client.session
    return request


@pytest.fixture
def anon_request(rf, client):
    request = rf.get('/')
    request.sso_user = None
    request.session = client.session
    return request


@pytest.fixture
def company_request(rf, client, sso_user):
    request = rf.get('/')
    request.sso_user = sso_user
    request.session = client.session
    return request


@pytest.fixture
def sso_request(company_request, sso_user):
    request = company_request
    request.sso_user = sso_user
    return request


@pytest.fixture
def api_response_200(*args, **kwargs):
    response = requests.Response()
    response.status_code = http.client.OK
    return response


@pytest.fixture
def api_response_400(*args, **kwargs):
    response = requests.Response()
    response.status_code = http.client.BAD_REQUEST
    return response


@pytest.fixture
def api_response_send_verification_sms_200(api_response_200):
    response = api_response_200
    response.json = lambda: {'sms_code': '12345'}
    return response


@pytest.fixture
def api_response_company_profile_no_sectors_200(api_response_200):
    response = api_response_200
    payload = {
        'website': 'http://example.com',
        'description': 'Ecommerce website',
        'number': 123456,
        'sectors': None,
        'logo': 'nice.jpg',
        'name': 'Great company',
        'keywords': 'word1 word2',
        'employees': '501-1000',
        'date_of_creation': '2015-03-02',
    }
    response.json = lambda: payload
    return response


@pytest.fixture
def api_response_company_profile_no_date_of_creation_200(api_response_200):
    response = api_response_200
    payload = {
        'website': 'http://example.com',
        'description': 'Ecommerce website',
        'number': 123456,
        'sectors': None,
        'logo': 'nice.jpg',
        'name': 'Great company',
        'keywords': 'word1 word2',
        'employees': '501-1000',
        'date_of_creation': None,
    }
    response.json = lambda: payload
    return response


def test_email_confirm_missing_confirmation_code(rf, sso_user):
    view = CompanyEmailConfirmationView.as_view()
    request = rf.get(reverse('confirm-company-email'))
    request.sso_user = sso_user
    response = view(request)
    assert response.status_code == http.client.OK
    assert response.template_name == (
        CompanyEmailConfirmationView.failure_template
    )


@patch.object(api_client.registration, 'confirm_email', return_value=False)
def test_email_confirm_invalid_confirmation_code(mock_confirm_email, rf):
    view = CompanyEmailConfirmationView.as_view()
    request = rf.get(reverse(
        'confirm-company-email'), {'code': 123}
    )
    response = view(request)
    assert mock_confirm_email.called_with(123)
    assert response.status_code == http.client.OK
    assert response.template_name == (
        CompanyEmailConfirmationView.failure_template
    )


@patch.object(api_client.registration, 'confirm_email', return_value=True)
def test_email_confirm_valid_confirmation_code(mock_confirm_email, rf):
    view = CompanyEmailConfirmationView.as_view()
    request = rf.get(reverse(
        'confirm-company-email'), {'code': 123}
    )
    response = view(request)
    assert mock_confirm_email.called_with(123)
    assert response.status_code == http.client.FOUND
    assert response.get('Location') == reverse('company-detail')


def test_enrolment_instructions_view_handles_no_sso_user(anon_request):
    response = EnrolmentInstructionsView.as_view()(anon_request)

    assert response.template_name == [EnrolmentInstructionsView.template_name]
    assert response.status_code == http.client.OK


@patch('enrolment.helpers.has_verified_company', return_value=True)
def test_enrolment_instructions_view_handles_sso_user_with_company(
    mock_has_verified_company, sso_request, sso_user
):
    response = EnrolmentInstructionsView.as_view()(sso_request)

    mock_has_verified_company.assert_called_once_with(sso_user.id)
    assert response.status_code == http.client.FOUND
    assert response.get('Location') == reverse('company-detail')


@patch.object(helpers, 'has_verified_company', return_value=False)
def test_enrolment_instructions_view_handles_sso_user_without_company(
    mock_has_verified_company, sso_user, sso_request
):
    response = EnrolmentInstructionsView.as_view()(sso_request)

    assert response.template_name == [EnrolmentInstructionsView.template_name]
    assert response.status_code == http.client.OK


@patch('enrolment.helpers.has_verified_company', Mock(return_value=False))
@patch('sso.middleware.SSOUserMiddleware.process_request', process_request)
@patch.object(forms, 'get_supplier_form_initial_data',
              Mock(return_value={'referrer': 'google'}))
def test_enrolment_view_includes_referrer(client):
    url = reverse('register', kwargs={'step': EnrolmentView.SUPPLIER})

    response = client.get(url)

    assert response.context_data['form'].initial['referrer'] == 'google'


@patch('enrolment.helpers.has_verified_company', Mock(return_value=False))
@patch('sso.middleware.SSOUserMiddleware.process_request', process_request)
def test_enrolment_email_view_includes_email(client):
    url = reverse('register', kwargs={'step': EnrolmentView.EMAIL})

    response = client.get(url)

    email = response._request.sso_user.email
    expected = forms.get_email_form_initial_data(email)
    assert response.context_data['form'].initial == expected


@patch('enrolment.helpers.has_verified_company', Mock(return_value=True))
@patch.object(EnrolmentView, 'get_all_cleaned_data', return_value={})
@patch.object(forms, 'serialize_enrolment_forms')
@patch.object(api_client.registration, 'send_form')
def test_enrolment_form_complete_api_client_call(mock_send_form,
                                                 mock_serialize_forms,
                                                 sso_request):
    view = EnrolmentView()
    view.request = sso_request
    mock_serialize_forms.return_value = data = {'field': 'value'}
    view.done()
    mock_send_form.assert_called_once_with(data)


@patch('enrolment.helpers.has_verified_company', Mock(return_value=True))
@patch.object(EnrolmentView, 'serialize_form_data', Mock(return_value={}))
@patch.object(api_client.registration, 'send_form', api_response_200)
def test_enrolment_form_complete_api_client_success(sso_request):
    view = EnrolmentView()
    view.request = sso_request
    response = view.done()
    assert response.template_name == EnrolmentView.success_template


@patch('enrolment.helpers.has_verified_company', Mock(return_value=True))
@patch.object(EnrolmentView, 'serialize_form_data', Mock(return_value={}))
@patch.object(api_client.registration, 'send_form', api_response_400)
def test_enrolment_form_complete_api_client_fail(company_request):
    view = EnrolmentView()
    view.request = company_request
    response = view.done()
    assert response.template_name == EnrolmentView.failure_template


@patch.object(helpers, 'get_company_name_from_session',
              Mock(return_value='Example corp'))
@patch('enrolment.helpers.has_verified_company', Mock(return_value=False))
@patch('sso.middleware.SSOUserMiddleware.process_request', process_request)
def test_enrolment_views_use_correct_template(client):
    view_class = EnrolmentView
    for step_name, form in view_class.form_list:
        response = client.get(reverse('register', kwargs={'step': step_name}))

        assert response.template_name == [view_class.templates[step_name]]


@patch('enrolment.helpers.has_verified_company', Mock(return_value=False))
@patch('sso.middleware.SSOUserMiddleware.process_request', process_request)
@patch.object(helpers, 'get_sms_session_code',
              Mock(return_value=helpers.encrypt_sms_code(123)))
def test_enrolment_view_passes_sms_code_to_form(client):
    url = reverse('register', kwargs={'step': EnrolmentView.SMS_VERIFY})
    response = client.get(url)

    encoded_sms_code = response.context_data['form'].encoded_sms_code
    assert helpers.check_encrypted_sms_cookie(123, encoded_sms_code)


@patch('enrolment.helpers.has_verified_company', return_value=True)
@patch('sso.middleware.SSOUserMiddleware.process_request', process_request)
def test_enrolment_logged_in_has_company_redirects(
    mock_has_verified_company, client, sso_user
):
    url = reverse('register', kwargs={'step': EnrolmentView.COMPANY})
    response = client.get(url)

    assert response.status_code == http.client.FOUND
    assert response.get('Location') == reverse('company-detail')
    mock_has_verified_company.assert_called_once_with(sso_user.id)


@patch('enrolment.helpers.has_verified_company', return_value=False)
@patch('sso.middleware.SSOUserMiddleware.process_request',
       process_request_anon)
def test_enrolment_logged_out_has_company_redirects(
    mock_has_verified_company, client
):
    step = EnrolmentView.COMPANY
    url = reverse('register', kwargs={'step': step})
    response = client.get(url)

    assert response.status_code == http.client.FOUND
    assert response.get('Location') == (
         'http://sso.trade.great.dev:8004/accounts/signup/'
         '?next=http%3A//testserver/register/' + step
    )
    mock_has_verified_company.assert_not_called()


@patch('enrolment.helpers.has_verified_company', Mock(return_value=False))
@patch.object(validators.api_client.supplier, 'validate_mobile_number', Mock())
@patch.object(api_client.registration, 'send_verification_sms')
@patch('sso.middleware.SSOUserMiddleware.process_request', process_request)
def test_enrolment_calls_api(
    mock_api_call, client, api_response_send_verification_sms_200
):
    mock_api_call.return_value = api_response_send_verification_sms_200
    step = EnrolmentView.SUPPLIER
    url = reverse('register', kwargs={'step': step})
    client.get(url)
    response = client.post(url, valid_supplier_data_step)

    assert response.status_code == http.client.FOUND
    mock_api_call.assert_called_once_with(
        phone_number=valid_supplier_data_step[step + '-mobile_number']
    )


@patch('enrolment.helpers.has_verified_company', Mock(return_value=False))
@patch.object(validators.api_client.supplier, 'validate_mobile_number', Mock())
@patch.object(api_client.registration, 'send_verification_sms')
@patch('sso.middleware.SSOUserMiddleware.process_request', process_request)
def test_enrolment_handles_good_response(
    mock_api_call, api_response_send_verification_sms_200, client
):

    mock_api_call.return_value = api_response_send_verification_sms_200
    url = reverse('register', kwargs={'step': EnrolmentView.SUPPLIER})
    client.get(url)
    response = client.post(url, valid_supplier_data_step)

    actual = helpers.get_sms_session_code(client.session)

    assert response.status_code == http.client.FOUND
    assert helpers.check_encrypted_sms_cookie('12345', actual)


@patch('enrolment.helpers.has_verified_company', Mock(return_value=False))
@patch.object(validators.api_client.supplier, 'validate_mobile_number', Mock())
@patch.object(api_client.registration, 'send_verification_sms',
              api_response_400)
@patch('sso.middleware.SSOUserMiddleware.process_request', process_request)
def test_enrolment_handles_bad_response(client):
    step = EnrolmentView.SUPPLIER
    with pytest.raises(requests.exceptions.HTTPError):
        url = reverse('register', kwargs={'step': step})
        client.get(url)
        response = client.post(url, valid_supplier_data_step)

        assert response.status_code == http.client.INTERNAL_SERVER_ERROR


@patch.object(api_client.buyer, 'send_form')
def test_international_landing_view_submit(
    mock_send_form, buyer_request, buyer_form_data
):
    response = InternationalLandingView.as_view()(buyer_request)

    assert response.template_name == InternationalLandingView.success_template
    mock_send_form.assert_called_once_with(
        forms.serialize_international_buyer_forms(buyer_form_data)
    )
