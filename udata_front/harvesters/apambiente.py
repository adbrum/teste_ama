from datetime import datetime
import requests
from urllib.parse import urlparse, urlencode

from udata.harvest.backends.base import BaseBackend
from udata.models import Resource, Dataset, License
from owslib.csw import CatalogueServiceWeb

from udata.harvest.models import HarvestItem

# backend = 'https://sniambgeoportal.apambiente.pt/geoportal/csw'


class PortalAmbienteBackend(BaseBackend):
    display_name = 'Harvester Portal do Ambiente'

    def inner_harvest(self):
        startposition = 0
        csw = CatalogueServiceWeb(self.source.url)
        csw.getrecords2(maxrecords=1)
        matches = csw.results.get("matches")

        while startposition <= matches:
            csw.getrecords2(maxrecords=100, startposition=startposition)
            startposition = csw.results.get('nextrecord')
            for rec in csw.records:
                item = {}
                record = csw.records[rec]
                item["id"] = record.identifier
                item["title"] = record.title
                item["description"] = record.abstract
                item["url"] = record.references[0].get('url')
                item["type"] = record.type
                # self.add_item(record.identifier, title=record.title, date=None, item=item)
                self.process_dataset(record.identifier, title=record.title, date=None, items=item)

    def inner_process_dataset(self, item: HarvestItem, **kwargs):
        dataset = self.get_dataset(item.remote_id)
        # Here you comes your implementation. You should :
        # - fetch the remote dataset (if necessary)
        # - validate the fetched payload
        # - map its content to the dataset fields
        # - store extra significant data in the `extra` attribute
        # - map resources data
        item = kwargs.get('items')

        # Set basic dataset fields
        dataset.title = item['title']
        dataset.license = License.guess('cc-by')
        dataset.tags = ["apambiente.pt"]
        dataset.description = item['description']

        if item.get('date'):
            dataset.created_at = item['date']

        dataset.description = item.get('description')

        # Force recreation of all resources
        dataset.resources = []

        url = item.get('url')

        if item.get('type') == "liveData":
            type = "wms"
        else:
            type = url.split('.')[-1].lower()
            if len(type) > 3:
                type = "wms"

        new_resource = Resource(
            title=dataset.title,
            url=url,
            filetype='remote',
            format=type
        )
        dataset.resources.append(new_resource)

        return dataset
