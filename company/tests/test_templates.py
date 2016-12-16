from datetime import datetime, timedelta

from django.core.urlresolvers import reverse
from django.core.paginator import Paginator
from django.template.loader import render_to_string

from company import forms


default_context = {
    'company': {
        'sectors': [
            {'value': 'SECTOR1', 'label': 'sector 1'},
            {'value': 'SECTOR2', 'label': 'sector 2'},
        ],
        'employees': '1-10',
        'number': '123456',
        'name': 'UK exporting co ltd.',
        'description': 'Exporters of UK wares.',
        'website': 'www.ukexportersnow.co.uk',
        'logo': 'www.ukexportersnow.co.uk/logo.png',
        'keywords': 'word1 word2',
        'date_of_creation': datetime(2015, 3, 2),
        'modified': datetime.now() - timedelta(hours=1),
        'contact_details': {
            'email_address': 'sales@example.com',
        },
    }
}

DATE_CREATED_LABEL = 'Incorporated'
NO_RESULTS_FOUND_LABEL = 'No companies found'
CONTACT_LINK_LABEL = 'Contact company'
SET_LOGO_LABEL = 'Set logo'
UPDATED_LABEL = 'Last updated'


def test_public_company_profile_details_feature_flag_public_profile_on():
    context = {
        'company': {
            'sectors': [
                {'value': 'THING', 'label': 'thing'},
                {'value': 'OTHER_THING', 'label': 'other_thing'},
            ]
        },
        'features': {
            'FEATURE_PUBLIC_PROFILES_ENABLED': True
        }
    }
    url = reverse('public-company-profiles-list')
    html = render_to_string('company-public-profile-detail.html', context)

    assert 'href="{url}?sectors=THING"'.format(url=url) in html
    assert 'href="{url}?sectors=OTHER_THING"'.format(url=url) in html


def test_public_company_profile_details_links_to_case_studies():
    context = {
        'features': {
            'FEATURE_PUBLIC_PROFILES_ENABLED': True
        },
        'case_studies': [
            {
                "pk": 3,
                "company": 1,
                "description": "great",
                "image_one": "https://image_one.jpg",
                "image_three": None,
                "image_two": "https://image_two.jpg",
                "keywords": "nice",
                "sector": "AEROSPACE",
                "testimonial": "hello",
                "testimonial_name": "Neville",
                "testimonial_job_title": "Abstract hat maker",
                "testimonial_company": "Imaginary hats Ltd",
                "title": "three",
                "video_one": None,
                "website": "http://www.example.com",
                "year": "2000"
            },
        ]
    }
    url = reverse('company-case-study-view', kwargs={'id': '3'})
    html = render_to_string('company-public-profile-detail.html', context)

    assert 'href="{url}"'.format(url=url) not in html


def test_public_company_profile_details_feature_flag_public_profile_off():
    context = {
        'company': {
            'sectors': [
                {'value': 'THING', 'label': 'thing'},
                {'value': 'OTHER_THING', 'label': 'other_thing'},
            ]
        },
    }
    url = reverse('public-company-profiles-list')
    html = render_to_string('company-public-profile-detail.html', context)

    assert 'href="{url}?sectors=THING"'.format(url=url) not in html
    assert 'href="{url}?sectors=OTHER_THING"'.format(url=url) not in html


def test_public_company_profile_details_renders_sectors():
    template_name = template_name = 'company-public-profile-detail.html'
    html = render_to_string(template_name, default_context)
    assert 'sector 1' in html
    assert 'sector 2' in html


def test_public_company_profile_details_renders_date_created():
    template_name = 'company-public-profile-detail.html'
    html = render_to_string(template_name, default_context)
    assert '2015' in html
    assert DATE_CREATED_LABEL in html


def test_public_company_profile_details_handles_no_date_created():
    html = render_to_string('company-public-profile-detail.html')
    assert DATE_CREATED_LABEL not in html


def test_public_company_profile_details_renders_company_number():
    template_name = 'company-public-profile-detail.html'
    html = render_to_string(template_name, default_context)
    assert default_context['company']['number'] in html


def test_public_company_profile_details_renders_company_name():
    template_name = 'company-public-profile-detail.html'
    html = render_to_string(template_name, default_context)
    assert default_context['company']['name'] in html


def test_public_company_profile_details_renders_description():
    template_name = 'company-public-profile-detail.html'
    html = render_to_string(template_name, default_context)
    assert default_context['company']['description'] in html


def test_public_company_profile_details_renders_keywords():
    template_name = 'company-public-profile-detail.html'
    html = render_to_string(template_name, default_context)
    assert default_context['company']['keywords'] in html


def test_public_company_profile_details_renders_website():
    template_name = 'company-public-profile-detail.html'
    html = render_to_string(template_name, default_context)
    assert default_context['company']['website'] in html


def test_public_company_profile_details_renders_logo():
    template_name = 'company-public-profile-detail.html'
    html = render_to_string(template_name, default_context)
    assert default_context['company']['logo'] in html


def test_company_public_profile_list_link_to_profle():
    context = {
        'companies': [
            default_context['company']
        ]
    }
    url = reverse(
        'public-company-profiles-detail',
        kwargs={'company_number': default_context['company']['number']}
    )
    html = render_to_string('company-public-profile-list.html', context)

    assert 'href="{url}"'.format(url=url) in html


def test_company_public_profile_no_results_label():
    form = forms.PublicProfileSearchForm(data={'sectors': 'WATER'})
    assert form.is_valid()
    context = {
        'companies': [],
        'form': form,
    }
    html = render_to_string('company-public-profile-list.html', context)

    assert NO_RESULTS_FOUND_LABEL in html


def test_company_public_profile_results_label():
    form = forms.PublicProfileSearchForm(data={'sectors': 'WATER'})
    assert form.is_valid()
    paginator = Paginator([{}], 10)
    context = {
        'selected_sector_label': 'thing',
        'companies':  [
            default_context['company']
        ],
        'pagination': paginator.page(1),
        'form': form,
    }
    html = render_to_string('company-public-profile-list.html', context)
    assert "Displaying 1 of 1 \'thing\' company" in html
    assert NO_RESULTS_FOUND_LABEL not in html


def test_company_public_profile_renders_modified():
    context = {
        'companies':  [
            default_context['company']
        ],
    }
    html = render_to_string('company-public-profile-list.html', context)
    assert UPDATED_LABEL in html
    assert '1 hour ago'


def test_company_public_profile_results_label_plural():
    form = forms.PublicProfileSearchForm(data={'sectors': 'WATER'})
    assert form.is_valid()
    paginator = Paginator(range(10), 10)
    context = {
        'selected_sector_label': 'thing',
        'companies': [
            default_context['company'],
            default_context['company'],
        ],
        'pagination': paginator.page(1),
        'form': form,
    }
    html = render_to_string('company-public-profile-list.html', context)
    assert "Displaying 2 of 10 \'thing\' companies" in html
    assert NO_RESULTS_FOUND_LABEL not in html


def test_company_public_profile_list_paginate_next():
    form = forms.PublicProfileSearchForm(data={'sectors': 'WATER'})
    assert form.is_valid()

    paginator = Paginator(range(100), 10)
    context = {
        'pagination': paginator.page(1),
        'form': form,
        'companies': [{'number': '01234567A'}]
    }

    html = render_to_string('company-public-profile-list.html', context)

    assert 'href="?sectors=WATER&page=2"' in html


def test_company_public_profile_list_paginate_prev():
    form = forms.PublicProfileSearchForm(data={'sectors': 'WATER'})
    assert form.is_valid()

    paginator = Paginator(range(100), 10)
    context = {
        'pagination': paginator.page(2),
        'form': form,
        'companies': [{'number': '01234567A'}]
    }

    html = render_to_string('company-public-profile-list.html', context)

    assert 'href="?sectors=WATER&page=1"' in html


def test_supplier_case_study_details_renders_company_details():
    context = {
        'case_study': {
            'company': {
                'date_of_creation': '1 Jan 2015',
                'name': 'Example corp',
            }
        }
    }
    html = render_to_string('supplier-case-study-detail.html', context)

    assert context['case_study']['company']['name'] in html
    assert context['case_study']['company']['date_of_creation'] in html


def test_supplier_case_study_details_renders_case_study_details():
    context = {
        'case_study': {
            'sector': {
                'label': 'Water'
            },
            'year': '2000',
            'testimonial': 'Good.',
            'testimonial_name': 'Neville',
            'testimonial_job_title': 'Abstract hat maker',
            'testimonial_company': 'Imaginary hats Ltd',
            'title': 'Very good thing',
            'image_one': 'image_one.png',
            'image_two': 'image_two.png',
            'image_three': 'image_three.png',
        }
    }
    html = render_to_string('supplier-case-study-detail.html', context)

    assert context['case_study']['sector']['label'] in html
    assert context['case_study']['year'] in html
    assert context['case_study']['testimonial'] in html
    assert context['case_study']['testimonial_name'] in html
    assert context['case_study']['testimonial_job_title'] in html
    assert context['case_study']['testimonial_company'] in html
    assert context['case_study']['title'] in html
    assert context['case_study']['image_one'] in html
    assert context['case_study']['image_two'] in html
    assert context['case_study']['image_three'] in html


def test_supplier_case_study_detail_render_profile_link_flag_on_published():
    context = {
        'case_study': {
            'company': {
                'number': 3,
                'is_published': True,
            },
        },
        'features': {
            'FEATURE_PUBLIC_PROFILES_ENABLED': True,
        },
    }
    url = reverse(
        'public-company-profiles-detail', kwargs={'company_number': '3'}
    )
    html = render_to_string('supplier-case-study-detail.html', context)

    assert url in html


def test_supplier_case_study_detail_render_profile_link_flag_on_unpublished():
    context = {
        'case_study': {
            'company': {
                'number': 3,
                'is_published': False,
            },
        },
        'features': {
            'FEATURE_PUBLIC_PROFILES_ENABLED': True,
        },
    }
    url = reverse(
        'public-company-profiles-detail', kwargs={'company_number': '3'}
    )
    html = render_to_string('supplier-case-study-detail.html', context)

    assert url not in html


def test_supplier_case_study_details_renders_case_study_flag_off_published():
    context = {
        'case_study': {
            'company': {
                'number': 3,
                'is_published': True,
            },
        },
        'features': {
            'FEATURE_PUBLIC_PROFILES_ENABLED': False
        },
    }
    url = reverse(
        'public-company-profiles-detail', kwargs={'company_number': '3'}
    )
    html = render_to_string('supplier-case-study-detail.html', context)

    assert url not in html


def test_supplier_case_study_details_renders_case_study_flag_off_unpublished():
    context = {
        'case_study': {
            'company': {
                'number': 3,
                'is_published': False,
            },
        },
        'features': {
            'FEATURE_PUBLIC_PROFILES_ENABLED': False
        },
    }
    url = reverse(
        'public-company-profiles-detail', kwargs={'company_number': '3'}
    )
    html = render_to_string('supplier-case-study-detail.html', context)

    assert url not in html


def test_company_public_details_renders_contact_details():
    template_name = 'company-public-profile-detail.html'
    context = default_context
    html = render_to_string(template_name, context)

    assert context['company']['contact_details']['email_address'] in html
    assert CONTACT_LINK_LABEL in html


def test_company_profile_details_renders_contact_details():
    template_name = 'company-private-profile-detail.html'
    context = default_context

    html = render_to_string(template_name, context)

    assert context['company']['website'] in html
    assert context['company']['contact_details']['email_address'] in html


def test_company_profile_details_renders_company_details():
    template_name = 'company-private-profile-detail.html'
    context = default_context

    html = render_to_string(template_name, context)

    assert context['company']['employees'] in html
    assert context['company']['number'] in html


def test_company_profile_details_renders_company_name():
    template_name = 'company-private-profile-detail.html'
    html = render_to_string(template_name, default_context)
    assert default_context['company']['name'] in html


def test_company_profile_details_renders_logo():
    template_name = 'company-private-profile-detail.html'
    html = render_to_string(template_name, default_context)

    assert default_context['company']['logo'] in html
    assert SET_LOGO_LABEL not in html


def test_company_profile_details_renders_set_logo():
    template_name = 'company-private-profile-detail.html'
    html = render_to_string(template_name, {})

    assert SET_LOGO_LABEL in html


def test_company_profile_details_renders_description():
    template_name = 'company-private-profile-detail.html'
    html = render_to_string(template_name, default_context)
    assert default_context['company']['description'] in html


def test_company_profile_details_renders_sectors():
    template_name = 'company-private-profile-detail.html'
    html = render_to_string(template_name, default_context)
    assert 'sector 1' in html
    assert 'sector 2' in html


def test_company_profile_details_renders_keywords():
    template_name = 'company-private-profile-detail.html'
    html = render_to_string(template_name, default_context)
    assert default_context['company']['keywords'] in html


def test_company_private_profile_details_renders_standalone_edit_links():
    context = {'show_wizard_links': False}
    html = render_to_string('company-private-profile-detail.html', context)

    assert reverse('company-edit-address') in html
    assert reverse('company-edit-sectors') in html
    assert reverse('company-edit-key-facts') in html


def test_company_private_profile_details_renders_wizard_links():
    context = {'show_wizard_links': True}
    html = render_to_string('company-private-profile-detail.html', context)
    company_edit_link = 'href="{url}"'.format(url=reverse('company-edit'))

    assert reverse('company-edit-address') not in html
    assert reverse('company-edit-sectors') not in html
    assert reverse('company-edit-key-facts') not in html
    assert html.count(company_edit_link) == 6
