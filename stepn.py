import requests

url_api = "https://api.stepn.com/run"
url_pics = "https://res.stepn.com/imgOut"

params_orderlist = [
    "order",  # Sorting
    "chain",  # Blockchain id
    "refresh",  # Force refresh
    "page",  # Page index
    "type",  # Sneakers || Shoeboxes
    "gType",  # Don't know
    "quality",  # Common, Uncommon, Rare, Epic, Legendary
    "level",  # Level of the shoes
    "bread",  # Number of mints
]

mapping_chain = {
    "sol": "103",
    "bnb": "104",
    "eth": "101",
}

mapping_type = {
    "sneakers_all": "600",
    "sneakers_walker": "601",
    "sneakers_jogger": "602",
    "sneakers_runner": "603",
    "sneakers_trainer": "604",
    "shoeboxes_all": "301",
}

mapping_order = {
    "lowest_price": "2001",
    "highest_price": "2002",
    "latest": "1002",
}

mapping_quality = {
    "common": "1",
    "uncommon": "2",
    "rare": "3",
    "epic": "4",
    "legendary": "5",
}

mapping_response_attrs = {
    0: "Efficiency",
    1: "Luck",
    2: "Comfort",
    3: "Resilience",
    4: "Unknown",
}


class StepnRequest(object):

    @classmethod
    def get_code_login(cls, email: str):
        url = cls.creates_url_params(endpoint='sendlogincode', account=email)

        response = requests.get(url)
        return response.json()

    @classmethod
    def get_login(cls, email: str, password):
        url = cls.creates_url_params(endpoint='login', account=email, password=password, type=4)

        response = requests.get(url)
        return response.json()

    @classmethod
    def get_orderlist(cls, **kwargs) -> dict:
        """
        params_example = {
            "order": mapping_order["lowest_price"],
            "chain": mapping_chain["sol"],
            "refresh": "true",
            "page": 0,
            "type": mapping_type["sneakers_all"],
            "gType": "",
            "quality": "",
            "level": "",
            "bread": "",
        }
        """
        url = cls.creates_url_params(endpoint='orderlist', **kwargs)

        response = requests.get(url)
        return response.json()

    @classmethod
    def get_orderdata(cls, order_id) -> dict:
        """
        Get one specific order
        """
        url = cls.creates_url_params(endpoint='orderdata', order_id=order_id)

        response = requests.get(url)
        return response.json()

    @staticmethod
    def creates_url_params(endpoint, **kwargs) -> str:
        url = f"{url_api}/{endpoint}?"

        for i, (key, value) in enumerate(kwargs.items()):
            if i > 0:
                url = f"{url}&"

            url = f"{url}{key}={value}"

        return url
