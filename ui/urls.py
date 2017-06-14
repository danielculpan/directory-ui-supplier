from django.conf.urls import url
from django.contrib.sitemaps.views import sitemap
from django.views.generic import TemplateView

from company.views import (
    CaseStudyDetailView,
    ContactCompanyView,
    CompanySearchView,
    PublishedProfileDetailView,
    PublishedProfileListView,
)
from enrolment.views import (
    AnonymousSubscribeFormView,
    LeadGenerationFormView,
    InternationalLandingSectorDetailView,
    InternationalLandingSectorListView,
    InternationalLandingView,
    PrivacyCookiesView,
    TermsView,
)
from notifications.views import (
    AnonymousUnsubscribeView
)
from exportopportunity.views import (
    SubmitExportOpportunityView
)
from ui.sitemaps import (
    SectorLandingPageSitemap,
    StaticViewSitemap,
)


sitemaps = {
    'static': StaticViewSitemap,
    'industries': SectorLandingPageSitemap,
}

urlpatterns = [
    url(
        r"^sitemap\.xml$", sitemap, {'sitemaps': sitemaps},
        name='sitemap'
    ),
    url(
        r"^robots\.txt$",
        TemplateView.as_view(
            template_name='robots.txt', content_type='text/plain'
        ),
        name='robots'
    ),
    url(
        r"^$",
        InternationalLandingView.as_view(),
        name="index"
    ),
    url(
        r'^suppliers$',
        PublishedProfileListView.as_view(),
        name='public-company-profiles-list',
    ),
    url(
        r'^search$',
        CompanySearchView.as_view(),
        name='company-search',
    ),
    url(
        r'^suppliers/(?P<company_number>.+)/contact$',
        ContactCompanyView.as_view(),
        name='contact-company',
    ),
    url(
        r'^suppliers/(?P<company_number>.+)/(?P<slug>.+)$',
        PublishedProfileDetailView.as_view(),
        name='public-company-profiles-detail',
    ),
    # obsolete. use `public-company-profiles-detail`
    url(
        r'^suppliers/(?P<company_number>.+)$',
        PublishedProfileDetailView.as_view(),
        name='public-company-profiles-detail-slugless',
    ),
    url(
        r'^industries$',
        InternationalLandingSectorListView.as_view(),
        name='international-sector-list',
    ),
    url(
        r'^industries/(?P<slug>.+)$',
        InternationalLandingSectorDetailView.as_view(),
        name='international-sector-detail',
    ),
    url(
        r'^case-study/(?P<id>.+)/(?P<slug>.+)$',
        CaseStudyDetailView.as_view(),
        name='case-study-details'
    ),
    # obsolete. use `case-study-details`
    url(
        r'^case-study/(?P<id>.+)$',
        CaseStudyDetailView.as_view(),
        name='case-study-details-slugless',
    ),
    url(
        r'^privacy-policy$',
        PrivacyCookiesView.as_view(),
        name='privacy-and-cookies'
    ),
    url(
        r'^terms-and-conditions$',
        TermsView.as_view(),
        name='terms-and-conditions'
    ),
    url(
        r'^subscribe$',
        AnonymousSubscribeFormView.as_view(),
        name='subscribe'
    ),
    url(
        r'^feedback$',
        LeadGenerationFormView.as_view(),
        name='lead-generation'
    ),
    url(
        r'^unsubscribe$',
        AnonymousUnsubscribeView.as_view(),
        name='anonymous-unsubscribe'
    ),
    url(
        r'^export-opportunity$',
        SubmitExportOpportunityView.as_view(),
        name='export-opportunity'
    ),

]
