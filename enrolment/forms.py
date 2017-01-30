from django import forms
from django.conf import settings
from django.utils import translation
from django.utils.translation import ugettext_lazy as _

from directory_validators.constants import choices

from ui.fields import AgreeToTermsField


class LanguageForm(forms.Form):
    lang = forms.ChoiceField(choices=settings.LANGUAGES)


class InternationalBuyerForm(forms.Form):
    error_css_class = 'input-field-container has-error'
    PLEASE_SELECT_LABEL = _('Please select an industry')

    full_name = forms.CharField(label=_('Your name'))
    email_address = forms.EmailField(label=_('Email address'))
    sector = forms.ChoiceField(
        label=_('Industry'),
        choices=(
            [['', PLEASE_SELECT_LABEL]] + list(choices.COMPANY_CLASSIFICATIONS)
        )
    )
    company_name = forms.CharField(label=_('Company name'))
    country = forms.CharField(label=_('Country'))
    comment = forms.CharField(
        label=_(
            "Tell us if you can't find what you were looking for, or if you "
            "want to give feedback"
        ),
        help_text=_('Maximum 1000 characters.'),
        max_length=1000,
        widget=forms.Textarea,
        required=False,
    )
    terms = AgreeToTermsField()


def serialize_international_buyer_forms(cleaned_data):
    """
    Return the shape directory-api-client expects for saving international
    buyers.

    @param {dict} cleaned_data - All the fields in `InternationalBuyerForm`
    @returns dict

    """

    return {
        'name': cleaned_data['full_name'],
        'email': cleaned_data['email_address'],
        'sector': cleaned_data['sector'],
        'company_name': cleaned_data['company_name'],
        'country': cleaned_data['country'],
        'comment': cleaned_data.get('comment', ''),
    }


def get_language_form_initial_data():
    return {
        'lang': translation.get_language()
    }
