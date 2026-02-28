# core/seller_central.py

from .requester import Requester
from datetime import datetime
import aiohttp
import json


class SellerCentral:
    def __init__(self, asin: str, cookie: str):
        self.asin = asin
        self.cookie = cookie
        self.country_code = "FR"
        self.locale = "en-GB"

    async def get_product_data(self):
        url = f"https://sellercentral-europe.amazon.com/rcpublic/productmatch?searchKey={self.asin}&countryCode={self.country_code}&locale={self.locale}"
        async with Requester(url=url, referrer="https://sellercentral-europe.amazon.com/revcalpublic?mons_sel_locale=en_GB", cookie=self.cookie, api=True) as scraper:
            output = await scraper.fetch_get()
            if not output:
                return None

            try:
                data = json.loads(output.text)
                product = data["data"]["otherProducts"]["products"][0]
                return product["title"], product["link"], product["gl"], product["imageUrl"]
            except Exception as e:
                print(f"Product data {self.asin}: {e}", output.text)
                return None

    async def get_price(self):
        url = f"https://sellercentral-europe.amazon.com/rcpublic/getadditionalpronductinfo?countryCode={self.country_code}&asin={self.asin}&fnsku=&searchType=GENERAL&locale={self.locale}"
        async with Requester(url=url, referrer="https://sellercentral-europe.amazon.com/revcalpublic?mons_sel_locale=en_GB", cookie=self.cookie, api=True) as scraper:
            output = await scraper.fetch_get()
            if not output:
                return None

            try:
                data = json.loads(output.text)
                if data["data"] == {}:
                    return 1
                else:
                    return float(data["data"]["price"]["amount"])

            except Exception as e:
                print(f"Product price {self.asin}: {e}", output.text)
                return None

    async def get_fees(self, gl: str, price: float):
        url = f"https://sellercentral-europe.amazon.com/rcpublic/getfees?countryCode={self.country_code}&locale={self.locale}"
        peak = datetime.now().month in [10, 11, 12]
        payload = {
            "countryCode": self.country_code,
            "itemInfo": {
                "asin": self.asin,
                "glProductGroupName": gl,
                "packageLength": "0",
                "packageWidth": "0",
                "packageHeight": "0",
                "dimensionUnit": "",
                "packageWeight": "0",
                "weightUnit": "",
                "afnPriceStr": str(price),
                "mfnPriceStr": str(price),
                "mfnShippingPriceStr": "0",
                "currency": "EUR",
                "isNewDefined": "false"
            },
            "programIdList": ["Core#0","MFN#1"],
            "programParamMap": {}
        }

        async with Requester(url=url, referrer="https://sellercentral-europe.amazon.com/revcalpublic?mons_sel_locale=en_GB", cookie=self.cookie, api=True) as scraper:
            output = await scraper.fetch_post(payload)
            if not output:
                return None

            try:
                data = json.loads(output.text)
                core = data["data"]["programFeeResultMap"]["Core#0"]
                storage_fee = float(core["perUnitPeakStorageFee"]["total"]["amount"] if peak else core["perUnitNonPeakStorageFee"]["total"]["amount"])
                fulfillment_fees = float(core["otherFeeInfoMap"]["FulfillmentFee"]["total"]["amount"])
                fixed_fee = float(core["otherFeeInfoMap"]["FixedClosingFee"]["total"]["amount"])
                referral_fee = float(core["otherFeeInfoMap"]["ReferralFee"]["total"]["amount"])
                variable_fee = float(core["otherFeeInfoMap"]["VariableClosingFee"]["total"]["amount"])
                digital_services_fee = float(core["otherFeeInfoMap"]["DigitalServicesFee"]["total"]["amount"])
                total_cost = storage_fee + fulfillment_fees + fixed_fee + referral_fee + variable_fee + digital_services_fee
                return round(total_cost, 2)

            except Exception as e:
                print(f"Product fees {self.asin}: {e}", output.text)
                return None

    def sas_link_gen(self):
        return f"https://sas.selleramp.com/sas/lookup?SasLookup%5Bsearch_term%5D={self.asin}"
