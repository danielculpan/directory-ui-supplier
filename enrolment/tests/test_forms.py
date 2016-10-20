from unittest.mock import Mock

from directory_validators import enrolment

from enrolment import constants, forms


def create_mock_file():
    return Mock(size=1)


def test_company_form_rejects_missing_data():
    form = forms.CompanyForm(data={})
    assert form.is_valid() is False
    assert 'company_number' in form.errors


def test_company_form_rejects_too_long_company_number():
    form = forms.CompanyForm(data={
        'company_number': '012456789',
    })
    assert form.is_valid() is False
    assert 'company_number' in form.errors


def test_company_form_rejects_too_short_company_number():
    form = forms.CompanyForm(data={
        'company_number': '0124567',
    })
    assert form.is_valid() is False
    assert 'company_number' in form.errors


def test_company_form_accepts_valid_data():
    form = forms.CompanyForm(data={
        'company_number': '01245678',
    })
    assert form.is_valid() is True


def test_aims_form_accepts_valid_data():
    form = forms.AimsForm(data={
        'aim_one': constants.AIMS[1][0],
        'aim_two': constants.AIMS[2][0],
    })
    assert form.is_valid()


def test_aims_form_rejects_no_aims():
    form = forms.AimsForm(data={
        'aim_one': '',
        'aim_two': '',
    })
    assert form.is_valid() is False


def test_user_form_email_validators():
    field = forms.UserForm.base_fields['email']
    assert enrolment.email_domain_free in field.validators
    assert enrolment.email_domain_disposable in field.validators


def test_user_form_rejects_missing_data():
    form = forms.UserForm(data={})
    assert 'name' in form.errors
    assert 'password' in form.errors
    assert 'terms_agreed' in form.errors
    assert 'email' in form.errors


def test_user_form_rejects_invalid_email_addresses():
    form = forms.UserForm(data={
        'email': 'johnATjones.com',
    })
    assert form.is_valid() is False
    assert 'email' in form.errors


def test_user_form_accepts_valid_data():
    form = forms.UserForm(data={
        'name': 'John Johnson',
        'password': 'hunter2',
        'terms_agreed': 1,
        'email': 'john@jones.com',
    })
    assert form.is_valid()


def test_company_profile_form_requires_name():
    form = forms.CompanyBasicInfoForm(data={})

    valid = form.is_valid()

    assert valid is False
    assert 'company_name' in form.errors
    assert len(form.errors['company_name']) == 1
    assert form.errors['company_name'][0] == 'This field is required.'


def test_company_profile_form_requires_description():
    form = forms.CompanyBasicInfoForm(data={})

    valid = form.is_valid()

    assert valid is False
    assert 'description' in form.errors
    assert len(form.errors['description']) == 1
    assert form.errors['description'][0] == 'This field is required.'


def test_company_profile_form_requires_website():
    form = forms.CompanyBasicInfoForm(data={})

    valid = form.is_valid()

    assert valid is False
    assert 'website' in form.errors
    assert len(form.errors['website']) == 1
    assert form.errors['website'][0] == 'This field is required.'


def test_company_profile_form_rejects_invalid_website():
    form = forms.CompanyBasicInfoForm(data={'website': 'google'})

    valid = form.is_valid()

    assert valid is False
    assert 'website' in form.errors
    assert len(form.errors['website']) == 1
    assert form.errors['website'][0] == 'Enter a valid URL.'


def test_company_profile_form_accepts_valid_data():
    logo = create_mock_file()
    data = {'company_name': 'Amazon UK',
            'website': 'http://amazon.co.uk',
            'description': 'Ecommerce'}
    form = forms.CompanyBasicInfoForm(data=data, files={'logo': logo})

    valid = form.is_valid()

    assert valid is True
    assert form.cleaned_data == {
        'company_name': 'Amazon UK',
        'website': 'http://amazon.co.uk',
        'description': 'Ecommerce',
        'logo': logo,
    }


def test_company_profile_logo_validator():
    field = forms.CompanyBasicInfoForm.base_fields['logo']
    assert enrolment.logo_filesize in field.validators


def test_serialize_enrolment_forms():
    actual = forms.serialize_enrolment_forms({
        'aim_one': constants.AIMS[0][0],
        'aim_two': constants.AIMS[1][0],
        'company_number': '01234567',
        'email': 'contact@example.com',
        'name': 'jim',
        'password': 'hunter2',
        'referrer': 'google'
    })
    expected = {
        'aims': [constants.AIMS[0][0], constants.AIMS[1][0]],
        'company_number': '01234567',
        'email': 'contact@example.com',
        'personal_name': 'jim',
        'password': 'hunter2',
        'referrer': 'google'
    }
    assert actual == expected


def test_serialize_company_profile_forms():
    logo = create_mock_file()
    actual = forms.serialize_company_profile_forms({
        'company_name': 'Example ltd.',
        'website': 'http://example.com',
        'description': 'Jolly good exporter.',
        'logo': logo,
    })
    expected = {
        'name': 'Example ltd.',
        'website': 'http://example.com',
        'description': 'Jolly good exporter.',
        'logo': logo
    }
    assert actual == expected