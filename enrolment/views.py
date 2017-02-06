from django.conf import settings
from django.shortcuts import Http404
from django.template.response import TemplateResponse
from django.utils import translation
from django.views.generic import TemplateView
from django.views.generic.edit import FormView

from zenpy import Zenpy
from zenpy.lib.api_objects import Ticket, User

from api_client import api_client
from enrolment import constants, forms


ZENPY_CREDENTIALS = {
    'email': settings.ZENDESK_EMAIL,
    'token': settings.ZENDESK_TOKEN,
    'subdomain': settings.ZENDESK_SUBDOMAIN
}
# Zenpy will let the connection timeout after 5s and will retry 3 times
ZENPY_CLIENT = Zenpy(timeout=5, **ZENPY_CREDENTIALS)


class EnableTranslationsMixin:

    def __init__(self, *args, **kwargs):
        dependency = 'ui.middleware.ForceDefaultLocale'
        assert dependency in settings.MIDDLEWARE_CLASSES

    def dispatch(self, request, *args, **kwargs):
        translation.activate(request.LANGUAGE_CODE)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['language_switcher'] = {
            'show': True,
            'form': forms.LanguageForm(
                initial=forms.get_language_form_initial_data(),
            )
        }
        return context


class BuyerSubscribeFormView(FormView):
    success_template = 'landing-page-international-success.html'
    template_name = 'subscribe.html'
    form_class = forms.InternationalBuyerForm

    def _get_or_create_zendesk_user(self, cleaned_data):
        user_search = ZENPY_CLIENT.search(
            type='user',
            email=cleaned_data['email_address'],
        )
        if user_search.count == 0:
            user = User(
                name=cleaned_data['full_name'],
                email=cleaned_data['email_address'],
            )
            user_id = ZENPY_CLIENT.users.create(user).id
        else:
            user_id = user_search.values[0]['id']
        return user_id

    def _create_zendesk_ticket(self, cleaned_data, user_id):
        description = (
            'Name: {full_name}\n'
            'Email: {email_address}\n'
            'Company: {company_name}\n'
            'Country: {country}\n'
            'Sector: {sector}\n'
            'Comment: {comment}'
        ).format(**cleaned_data)
        ticket = Ticket(
            subject=settings.ZENDESK_TICKET_SUBJECT,
            description=description,
            submitter_id=user_id,
            requester_id=user_id,
        )
        ZENPY_CLIENT.tickets.create(ticket)

    def form_valid(self, form):
        data = forms.serialize_international_buyer_forms(form.cleaned_data)
        api_client.buyer.send_form(data)
        if form.cleaned_data['comment']:
            user_id = self._get_or_create_zendesk_user(form.cleaned_data)
            self._create_zendesk_ticket(form.cleaned_data, user_id)
        return TemplateResponse(self.request, self.success_template)


class InternationalLandingView(EnableTranslationsMixin, TemplateView):
    template_name = 'landing-page-international.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_view_name'] = 'index'
        return context


class InternationalLandingSectorListView(TemplateView):
    template_name = 'landing-page-international-sector-list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_view_name'] = 'international-sector-list'
        return context


class PrivacyCookiesView(TemplateView):
    template_name = 'privacy-and-cookies.html'


class TermsView(TemplateView):
    template_name = 'terms-and-conditions.html'


class InternationalLandingSectorDetailView(TemplateView):

    @classmethod
    def get_active_pages(cls):
        pages = {
            'health': {
                'template': 'marketing-pages/health.html',
                'context': constants.HEALTH_SECTOR_CONTEXT,
                'is_active': True,
            },
            'tech': {
                'template': 'marketing-pages/tech.html',
                'context': constants.TECH_SECTOR_CONTEXT,
                'is_active': True,
            },
            'creative': {
                'template': 'marketing-pages/creative.html',
                'context': constants.CREATIVE_SECTOR_CONTEXT,
                'is_active': True,
            },
            'food-and-drink': {
                'template': 'marketing-pages/food.html',
                'context': constants.FOOD_SECTOR_CONTEXT,
                'is_active': True,
            },
            'advanced-manufacturing': {
                'template': 'marketing-pages/advanced-manufacturing.html',
                'context': constants.ADVANCED_MANUFACTURING_CONTEXT,
                'is_active': settings.FEATURE_ADVANCED_MANUFACTURING_ENABLED,
            }
        }
        return {key: val for key, val in pages.items() if val['is_active']}

    def dispatch(self, request, *args, **kwargs):
        if self.kwargs['slug'] not in self.get_active_pages():
            raise Http404()
        return super().dispatch(request, *args, **kwargs)

    def get_template_names(self):
        pages = self.get_active_pages()
        template_name = pages[self.kwargs['slug']]['template']
        return [template_name]

    def get_context_data(self, *args, **kwargs):
        pages = self.get_active_pages()
        context = super().get_context_data(*args, **kwargs)
        context.update(pages[self.kwargs['slug']]['context'])
        context['show_proposition'] = 'verbose' in self.request.GET
        context['slug'] = self.kwargs['slug']
        return context
