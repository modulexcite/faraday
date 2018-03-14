#-*- coding: utf8 -*-
"""Tests for many API endpoints that do not depend on workspace_name"""

import pytest
from hypothesis import given, strategies as st

from test_cases import factories
from test_api_non_workspaced_base import ReadWriteAPITests, API_PREFIX
from server.models import (
    License,
)
from server.api.modules.licenses import LicenseView
from test_cases.factories import LicenseFactory


class LicenseEnvelopedView(LicenseView):
    """A custom view to test that enveloping on generic views work ok"""
    route_base = "test_envelope_list"

    def _envelope_list(self, objects, pagination_metadata=None):
        return {"object_list": objects}


class TestLicensesAPI(ReadWriteAPITests):
    model = License
    factory = factories.LicenseFactory
    api_endpoint = 'licenses'
    # unique_fields = ['ip']
    # update_fields = ['ip', 'description', 'os']

    def test_envelope_list(self, test_client, app):
        LicenseEnvelopedView.register(app)
        original_res = test_client.get(self.url())
        assert original_res.status_code == 200
        new_res = test_client.get(API_PREFIX + 'test_envelope_list/')
        assert new_res.status_code == 200

        assert new_res.json == {"object_list": original_res.json}

    def test_license_note_was_missing(self, test_client, session):
        notes = 'A great note. License'
        lic = LicenseFactory.create(notes=notes)
        session.commit()
        res = test_client.get(self.url(obj=lic))
        assert res.status_code == 200
        assert res.json['notes'] == 'A great note. License'


def license_json():
    return st.fixed_dictionaries(
        {
            "lictype": st.one_of(st.none(), st.text()),
            "metadata": st.fixed_dictionaries({
                "update_time": st.floats(),
                "update_user": st.one_of(st.none(), st.text()),
                "update_action": st.integers(),
                "creator": st.one_of(st.none(), st.text()),
                "create_time": st.floats(),
                "update_controller_action": st.one_of(st.none(), st.text()),
            "owner": st.one_of(st.none(), st.text())}),
            "notes": st.one_of(st.none(), st.text()),
            "product": st.one_of(st.none(), st.text()),
            "start": st.datetimes(),
            "end": st.datetimes(),
            "type": st.one_of(st.none(), st.text())
         })


@pytest.mark.usefixtures('logged_user')
@pytest.mark.hypothesis
def test_hypothesis_license(test_client):
    LicenseData = license_json()

    @given(LicenseData)
    def send_api_request(raw_data):
        res = test_client.post('_api/v2/licenses/', data=raw_data)
        assert res.status_code in [201, 400, 409]

    send_api_request()