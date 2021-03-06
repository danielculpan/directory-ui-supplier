import os
from unittest.mock import Mock

import pytest

from django.conf import settings
from django.core.urlresolvers import reverse
from django.template.loader import render_to_string

from enrolment import forms


supplier_context = {
    'supplier': {
        'mobile': '00000000011',
        'email': 'email@example.com',
    }
}


MESSAGE_ENGLISH_ONLY = 'Page in English only'
MORE_INDUSTRIES_LABEL = 'See more industries'


def test_google_tag_manager_project_id():
    context = {
        'analytics': {
            'GOOGLE_TAG_MANAGER_ID': '1234567',
        }
    }
    head_html = render_to_string('google_tag_manager_head.html', context)
    body_html = render_to_string('google_tag_manager_body.html', context)

    assert '1234567' in head_html
    assert 'https://www.googletagmanager.com/ns.html?id=1234567' in body_html


def test_google_tag_manager():
    context = {}
    expected_head = render_to_string('google_tag_manager_head.html', context)
    expected_body = render_to_string('google_tag_manager_body.html', context)

    html = render_to_string('govuk_layout.html', context)

    assert expected_head in html
    assert expected_body in html
    # sanity check
    assert 'www.googletagmanager.com' in expected_head
    assert 'www.googletagmanager.com' in expected_body


def test_templates_render_successfully():
    template_list = []
    template_dirs = [
        os.path.join(settings.BASE_DIR, 'enrolment/templates'),
        os.path.join(settings.BASE_DIR, 'supplier/templates'),
    ]
    # some templates cannot effectively be tested this way e.g., if they
    # translate form help text. Tests these separately.
    blacklisted_filenames = [
        'lead-generation-form.html',
    ]
    for template_dir in template_dirs:
        for dir, dirnames, filenames in os.walk(template_dir):
            for name in filenames:
                if name not in blacklisted_filenames:
                    path = os.path.join(dir, name).replace(template_dir, '')
                    template_list.append(path.lstrip('/'))

    default_context = {
        'supplier': None,
        'form': Mock(),
        'case_study': {
            'image_caption': '',
            'title': '',
            'synopsis': '',
            'testimonial': '',
            'testimonial_name': '',
            'testimonial_company': '',
            'company_name': '',
            'sectors': [],
            'keywords': '',
        },
        'companies': [
            {
                'name': '',
                'description': '',
            },
        ],
        'slug': 'CREATIVE_AND_MEDIA',
    }
    assert template_list
    for template in template_list:
        render_to_string(template, default_context)


def test_social_share_all_populated():
    context = {
        'social': {
            'image': 'image.png',
            'title': 'a title',
            'description': 'a description',
        }
    }
    html = render_to_string('social.html', context)

    assert '<meta property="og:type" content="website" />' in html
    assert '<meta property="og:image" content="image.png" />' in html
    assert '<meta property="og:title" content="a title" />'in html
    assert '<meta property="og:description" content="a description" />' in html


def test_social_share_not_populated():
    context = {}
    html = render_to_string('social.html', context)
    url = '/static/govuk-0.18.0/assets/images/opengraph-image.f86f1d0dd106.png'

    assert '<meta property="og:type" content="website" />' in html
    assert '<meta property="og:image" content="{0}" />'.format(url) in html
    assert '<meta property="og:title"' not in html
    assert '<meta property="og:description"' not in html


def test_language_switcher_show():
    context = {
        'language_switcher': {
            'show': True
        }
    }
    html = render_to_string('language_switcher.html', context)

    assert '<form' in html
    assert MESSAGE_ENGLISH_ONLY not in html


def test_language_switcher_hide():
    context = {
        'language_switcher': {
            'show': False
        },
        'request': {
            'LANGUAGE_CODE': 'en-gb'
        }
    }
    html = render_to_string('language_switcher.html', context)

    assert '<form' not in html
    assert MESSAGE_ENGLISH_ONLY not in html


def test_language_switcher_hide_not_translated_english_selected():
    context = {
        'language_switcher': {
            'show': False
        },
        'request': {
            'LANGUAGE_CODE': 'en-gb'
        }
    }
    html = render_to_string('language_switcher.html', context)

    assert '<form' not in html
    assert MESSAGE_ENGLISH_ONLY not in html


def test_language_switcher_hide_not_translated_german_selected():
    context = {
        'language_switcher': {
            'show': False
        },
        'request': {
            'LANGUAGE_CODE': 'de',
        }
    }
    html = render_to_string('language_switcher.html', context)

    assert '<form' not in html
    assert 'Seite nur auf Englisch' in html


def test_robots(rf):
    request = rf.get('/')

    context = {
        'request': request,
    }

    html = render_to_string('robots.txt', context)

    assert 'Sitemap: http://testserver/sitemap.xml' in html


def test_utm_cookie_domain():
    context = {
        'analytics': {
            'UTM_COOKIE_DOMAIN': '.thing.com',
        }
    }
    html = render_to_string('govuk_layout.html', context)

    assert '<meta id="utmCookieDomain" value=".thing.com" />' in html


def test_international_landing_page_button_feature_flag_on():
    context = {
        'features': {
            'FEATURE_MORE_INDUSTRIES_BUTTON_ENABLED': True,
        }
    }
    html = render_to_string('landing-page.html', context)

    assert MORE_INDUSTRIES_LABEL in html


def test_international_landing_page_button_feature_flag_off():
    context = {
        'features': {
            'FEATURE_MORE_INDUSTRIES_BUTTON_ENABLED': False,
        }
    }
    html = render_to_string('landing-page.html', context)

    assert MORE_INDUSTRIES_LABEL not in html


def test_lead_generation_form():
    context = {
        'form': forms.LeadGenerationForm()
    }
    html = render_to_string('lead-generation.html', context)

    assert html


@pytest.mark.parametrize('template_name', [
    'marketing-pages/bidi/base.html',
    'marketing-pages/base.html',
    'browse-companies.html',
])
def test_filter_search(template_name):
    context = {
        'sector_value': 'AEROSPACE',
        'slug': 'thing',   # marketing-pages/base.html
    }
    html = render_to_string(template_name, context)

    assert reverse('company-search') + '?sectors=AEROSPACE' in html
