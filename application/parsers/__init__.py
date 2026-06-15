"""
解析器注册表
"""
from application.parsers.vat_e import VatEParser
from application.parsers.vat_m import VatMParser
from application.parsers.digital_vat import DigitalVatParser
from application.parsers.itinerary import ItineraryParser
from application.parsers.train import TrainParser
from application.parsers.taxi import TaxiParser

PARSERS = {
    'vat_e': VatEParser,
    'vat_m': VatMParser,
    'digital_vat': DigitalVatParser,
    'itinerary': ItineraryParser,
    'train': TrainParser,
    'taxi': TaxiParser,
}


def get_parser(doc_type, ocr_lines):
    cls = PARSERS.get(doc_type)
    if cls is None:
        return None
    return cls(ocr_lines).parse()
